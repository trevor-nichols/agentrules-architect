"""Gemini provider implementation of ``BaseArchitect``."""

from __future__ import annotations

import json
import logging
import os
from collections.abc import AsyncIterator, Iterator
from typing import Any

from google.genai import types as genai_types

from agentrules.core.agents.base import BaseArchitect, ModelProvider, ReasoningMode
from agentrules.core.streaming import StreamChunk, StreamEventType
from agentrules.core.utils.async_stream import iterate_in_thread

from .client import build_gemini_client, generate_content_async
from .prompting import default_prompt_template, format_prompt
from .response_parser import (
    _collect_candidate_parts,
    _extract_function_call_args,
    parse_generate_response,
)
from .tooling import resolve_tool_config

logger = logging.getLogger("project_extractor")


DEFAULT_THINKING_BUDGET = 16000
DYNAMIC_THINKING_BUDGET = -1
DISABLED_THINKING_BUDGET = 0


class GeminiArchitect(BaseArchitect):
    """Architect class for interacting with Google's Gemini models."""

    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        reasoning: ReasoningMode = ReasoningMode.DISABLED,
        name: str | None = None,
        role: str | None = None,
        responsibilities: list[str] | None = None,
        prompt_template: str | None = None,
        api_key: str | None = None,
        tools_config: dict[str, Any] | None = None,
    ):
        super().__init__(
            provider=ModelProvider.GEMINI,
            model_name=model_name,
            reasoning=reasoning,
            name=name,
            role=role,
            responsibilities=responsibilities,
            tools_config=tools_config,
        )
        self.prompt_template = prompt_template or default_prompt_template()
        google_key = os.environ.get("GOOGLE_API_KEY")
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if gemini_key and not google_key:
            os.environ["GOOGLE_API_KEY"] = gemini_key
            google_key = gemini_key
        if gemini_key:
            os.environ.pop("GEMINI_API_KEY", None)

        env_key = os.environ.get("GOOGLE_API_KEY")
        resolved_key = api_key or env_key
        should_attempt_client = api_key is not None or env_key is not None or os.environ.get(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )
        if should_attempt_client:
            self.client, self._client_error_hint = build_gemini_client(resolved_key)
        else:
            self.client = None
            self._client_error_hint = (
                "Gemini client not initialized. Provide GEMINI_API_KEY, GOOGLE_API_KEY, "
                "GOOGLE_APPLICATION_CREDENTIALS, or pass api_key directly to GeminiArchitect."
            )

    @property
    def supports_streaming(self) -> bool:
        return self.client is not None

    # Public API -----------------------------------------------------------------
    def format_prompt(self, context: dict[str, Any]) -> str:
        return format_prompt(
            template=self.prompt_template,
            agent_name=self.name or "Gemini Architect",
            agent_role=self.role or "analyzing the project",
            responsibilities=self.responsibilities,
            context=context,
        )

    async def analyze(self, context: dict[str, Any], tools: list[Any] | None = None) -> dict[str, Any]:
        client = self.client
        if client is None:
            return self._client_not_initialized_result()

        prompt = context.get("formatted_prompt") or self.format_prompt(context)

        config_kwargs: dict[str, Any] = {}
        if self.role:
            config_kwargs["system_instruction"] = (
                f"You are {self.name or 'an AI assistant'}, responsible for {self.role}."
            )

        api_tools = resolve_tool_config(tools, self.tools_config)
        if api_tools:
            config_kwargs["tools"] = api_tools

        thinking_config = self._build_thinking_config()
        if thinking_config is not None:
            config_kwargs["thinking_config"] = thinking_config

        generation_config = genai_types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

        agent_name = self.name or "Gemini Architect"
        detail_suffix = self._compose_request_detail_suffix(thinking_config, api_tools)

        from agentrules.core.utils.model_config_helper import get_model_config_name  # Local import to avoid cycle

        model_config_name = get_model_config_name(self)
        logger.info(
            f"[bold magenta]{agent_name}:[/bold magenta] Sending request to {self.model_name} "
            f"(Config: {model_config_name}){detail_suffix}"
        )

        response = await generate_content_async(
            client,
            model=self.model_name,
            contents=prompt,
            config=generation_config,
        )

        logger.info(f"[bold green]{agent_name}:[/bold green] Received response from {self.model_name}")

        parsed = parse_generate_response(response)
        result: dict[str, Any] = {
            "agent": agent_name,
            "findings": parsed.findings,
        }
        if parsed.function_calls:
            result["function_calls"] = parsed.function_calls
            logger.info(f"[bold magenta]{agent_name}:[/bold magenta] Model requested function call(s).")
            if not parsed.findings:
                result["findings"] = None

        return result

    async def create_analysis_plan(self, phase1_results: dict, prompt: str | None = None) -> dict[str, Any]:
        context: dict[str, Any] = {"phase1_results": phase1_results}
        if prompt:
            context["formatted_prompt"] = prompt
        result = await self.analyze(context)
        return {
            "plan": result.get("findings", "No plan generated"),
            "error": result.get("error"),
        }

    async def synthesize_findings(self, phase3_results: dict, prompt: str | None = None) -> dict[str, Any]:
        context: dict[str, Any] = {"phase3_results": phase3_results}
        if prompt:
            context["formatted_prompt"] = prompt
        result = await self.analyze(context)
        return {
            "analysis": result.get("findings", "No synthesis generated"),
            "error": result.get("error"),
        }

    async def final_analysis(self, consolidated_report: dict, prompt: str | None = None) -> dict[str, Any]:
        context: dict[str, Any] = {"consolidated_report": consolidated_report}
        if prompt:
            context["formatted_prompt"] = prompt
        result = await self.analyze(context)
        return {
            "analysis": result.get("findings", "No final analysis generated"),
            "error": result.get("error"),
        }

    async def consolidate_results(self, all_results: dict, prompt: str | None = None) -> dict[str, Any]:
        client = self.client
        if client is None:
            return {
                "phase": "Consolidation",
                "error": self._client_error_hint or "Gemini client not initialized.",
            }

        content = prompt or (
            "Consolidate these results into a comprehensive report:\n\n"
            f"{json.dumps(all_results, indent=2)}"
        )

        model_name = self._resolve_consolidation_model()
        response = await generate_content_async(
            client,
            model=model_name,
            contents=content,
            config=None,
        )

        parsed = parse_generate_response(response)
        return {
            "phase": "Consolidation",
            "report": parsed.findings or "No report generated",
        }

    def stream_analyze(
        self,
        context: dict[str, Any],
        tools: list[Any] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        async def _generator() -> AsyncIterator[StreamChunk]:
            client = self.client
            if client is None:
                raise RuntimeError(self._client_error_hint or "Gemini streaming unavailable.")

            prompt = context.get("formatted_prompt") or self.format_prompt(context)

            config_kwargs: dict[str, Any] = {}
            if self.role:
                config_kwargs["system_instruction"] = (
                    f"You are {self.name or 'an AI assistant'}, responsible for {self.role}."
                )

            api_tools = resolve_tool_config(tools, self.tools_config)
            if api_tools:
                config_kwargs["tools"] = api_tools

            thinking_config = self._build_thinking_config()
            if thinking_config is not None:
                config_kwargs["thinking_config"] = thinking_config

            generation_config = genai_types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

            agent_name = self.name or "Gemini Architect"
            detail_suffix = self._compose_request_detail_suffix(thinking_config, api_tools)

            from agentrules.core.utils.model_config_helper import get_model_config_name  # Local import to avoid cycle

            model_config_name = get_model_config_name(self)
            logger.info(
                f"[bold magenta]{agent_name}:[/bold magenta] Streaming request to {self.model_name} "
                f"(Config: {model_config_name}){detail_suffix}"
            )

            try:
                async for chunk in iterate_in_thread(
                    lambda: self._stream_content(client, prompt, generation_config)
                ):
                    yield chunk
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error(f"[bold red]Streaming error in {agent_name}:[/bold red] {str(exc)}")
                raise

        return _generator()

    # Internal helpers -----------------------------------------------------------
    def _resolve_consolidation_model(self) -> str:
        if self.reasoning == ReasoningMode.DISABLED:
            return self.model_name
        return self._stable_model_name()

    def _client_not_initialized_result(self) -> dict[str, Any]:
        message = self._client_error_hint or "Gemini client not initialized."
        return {
            "agent": self.name or "Gemini Architect",
            "error": message,
        }

    def _compose_request_detail_suffix(
        self,
        thinking_config: genai_types.ThinkingConfig | None,
        api_tools: list[Any] | None,
    ) -> str:
        details: list[str] = []
        thinking_detail = self._describe_thinking_config(thinking_config)
        if thinking_detail:
            details.append(thinking_detail)
        if api_tools:
            details.append("with tools enabled")
        return f" ({', '.join(details)})" if details else ""

    @staticmethod
    def _describe_thinking_config(
        thinking_config: genai_types.ThinkingConfig | None,
    ) -> str | None:
        if thinking_config is None:
            return None

        level = getattr(thinking_config, "thinking_level", None)
        if level:
            normalized = str(getattr(level, "value", level)).lower()
            return f"with thinking level {normalized}"

        budget = getattr(thinking_config, "thinking_budget", None)
        if budget == DISABLED_THINKING_BUDGET:
            return "with thinking disabled"
        if budget == DYNAMIC_THINKING_BUDGET:
            return "with dynamic thinking"
        if isinstance(budget, int):
            return f"with thinking (budget={budget})"
        return None

    def _build_thinking_config(self) -> genai_types.ThinkingConfig | None:
        reasoning_mode = self.reasoning

        if self._model_supports_thinking_level():
            level = self._map_reasoning_mode_to_thinking_level(reasoning_mode)
            if level is None:
                return None
            return genai_types.ThinkingConfig(thinking_level=level)

        if reasoning_mode == ReasoningMode.DYNAMIC:
            return genai_types.ThinkingConfig(thinking_budget=DYNAMIC_THINKING_BUDGET)
        if reasoning_mode == ReasoningMode.ENABLED:
            return genai_types.ThinkingConfig(thinking_budget=DEFAULT_THINKING_BUDGET)
        if reasoning_mode == ReasoningMode.DISABLED:
            if self._model_supports_disabling_thinking():
                return genai_types.ThinkingConfig(thinking_budget=DISABLED_THINKING_BUDGET)
            logger.debug(
                "Model %s does not support disabling thinking; falling back to dynamic budget.",
                self.model_name,
            )
            return genai_types.ThinkingConfig(thinking_budget=DYNAMIC_THINKING_BUDGET)
        return None

    def _map_reasoning_mode_to_thinking_level(
        self,
        reasoning_mode: ReasoningMode,
    ) -> genai_types.ThinkingLevel | None:
        if reasoning_mode in (ReasoningMode.DISABLED, ReasoningMode.MINIMAL, ReasoningMode.LOW):
            return genai_types.ThinkingLevel.LOW
        if reasoning_mode in (
            ReasoningMode.ENABLED,
            ReasoningMode.DYNAMIC,
            ReasoningMode.MEDIUM,
            ReasoningMode.HIGH,
        ):
            return genai_types.ThinkingLevel.HIGH
        return None

    def _model_supports_disabling_thinking(self) -> bool:
        if self._model_supports_thinking_level():
            return False
        normalized = self.model_name.lower()
        # Gemini 2.5 Pro does not allow disabling thinking according to the docs.
        return "gemini-2.5-pro" not in normalized

    def _model_supports_thinking_level(self) -> bool:
        normalized = self.model_name.lower()
        return "gemini-3" in normalized

    def _stable_model_name(self) -> str:
        normalized = self.model_name.lower()
        if "gemini-2.5-flash" in normalized:
            return "gemini-2.5-flash"
        if "gemini-2.5-pro" in normalized:
            return "gemini-2.5-pro"
        if "gemini-3-pro" in normalized:
            return "gemini-3-pro-preview"
        return self.model_name

    def _stream_content(
        self,
        client: Any,
        prompt: str,
        config: genai_types.GenerateContentConfig | None,
    ) -> Iterator[StreamChunk]:
        stream = client.models.generate_content_stream(
            model=self.model_name,
            contents=prompt,
            config=config,
        )

        for chunk in stream:
            for part in _collect_candidate_parts(chunk):
                part_text = getattr(part, "text", None)
                if part_text:
                    yield StreamChunk(StreamEventType.TEXT_DELTA, str(part_text), None, None, None, None, chunk)

                function_call = getattr(part, "function_call", None)
                if function_call:
                    call_payload = {
                        "name": getattr(function_call, "name", None),
                        "args": _extract_function_call_args(function_call),
                    }
                    yield StreamChunk(
                        StreamEventType.TOOL_CALL_DELTA,
                        None,
                        None,
                        call_payload,
                        None,
                        None,
                        chunk,
                    )

        final_response = getattr(stream, "response", None)
        if final_response:
            usage = getattr(final_response, "usage_metadata", None)
            finish_reason = None
            candidates = getattr(final_response, "candidates", []) or []
            if candidates:
                finish_reason = getattr(candidates[0], "finish_reason", None)

            yield StreamChunk(
                StreamEventType.MESSAGE_END,
                None,
                None,
                None,
                finish_reason,
                self._to_dict(usage),
                final_response,
            )

    @staticmethod
    def _to_dict(value: Any) -> dict[str, Any] | None:
        if value is None:
            return None
        if isinstance(value, dict):
            return value
        if hasattr(value, "model_dump"):
            try:
                dumped = value.model_dump()  # type: ignore[call-arg]
                if isinstance(dumped, dict):
                    return dumped
            except TypeError:
                pass
        if hasattr(value, "to_dict"):
            result = value.to_dict()
            if isinstance(result, dict):
                return result
        if hasattr(value, "__dict__"):
            return {
                key: val
                for key, val in value.__dict__.items()
                if not key.startswith("_")
            }
        return None
