"""xAI provider implementation of ``BaseArchitect``."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Iterator
from typing import Any

from agentrules.core.agents.base import BaseArchitect, ModelProvider, ReasoningMode
from agentrules.core.streaming import StreamChunk, StreamEventType
from agentrules.core.utils.async_stream import iterate_in_thread
from agentrules.core.utils.token_estimator import compute_effective_limits, estimate_tokens

from .client import execute_chat_completion
from .config import ModelDefaults, resolve_base_url, resolve_model_defaults
from .prompting import default_prompt_template
from .prompting import format_prompt as format_analysis_prompt
from .request_builder import PreparedRequest, prepare_request
from .response_parser import parse_response
from .tooling import resolve_tool_config

logger = logging.getLogger("project_extractor")


class XaiArchitect(BaseArchitect):
    """Architect implementation backed by xAI's OpenAI-compatible API."""

    def __init__(
        self,
        model_name: str = "grok-4-0709",
        reasoning: ReasoningMode | None = None,
        temperature: float | None = None,
        name: str | None = None,
        role: str | None = None,
        responsibilities: list[str] | None = None,
        prompt_template: str | None = None,
        base_url: str | None = None,
        tools_config: dict[str, Any] | None = None,
        model_config: Any | None = None,
    ) -> None:
        self._defaults: ModelDefaults = resolve_model_defaults(model_name)
        effective_reasoning = reasoning or self._defaults.default_reasoning

        super().__init__(
            provider=ModelProvider.XAI,
            model_name=model_name,
            reasoning=effective_reasoning,
            temperature=temperature,
            name=name,
            role=role,
            responsibilities=responsibilities,
            tools_config=tools_config,
            model_config=model_config,
        )

        self.prompt_template = prompt_template or default_prompt_template()
        self.base_url = resolve_base_url(base_url)
        self._client_override: Any | None = None

    # Public API -----------------------------------------------------------------
    @property
    def supports_streaming(self) -> bool:
        return True
    def format_prompt(self, context: dict[str, Any]) -> str:
        return format_analysis_prompt(
            template=self.prompt_template,
            agent_name=self.name or "xAI Architect",
            agent_role=self.role or "analyzing the project",
            responsibilities=self.responsibilities,
            context=context,
        )

    async def analyze(self, context: dict[str, Any], tools: list[Any] | None = None) -> dict[str, Any]:
        try:
            content = context.get("formatted_prompt") or self.format_prompt(context)

            provider_tools = resolve_tool_config(
                tools,
                self.tools_config,
                allow_tools=self._defaults.tools_allowed,
            )

            prepared = self._prepare_request(content, provider_tools)
            self._log_token_estimate(prepared)

            from agentrules.core.utils.model_config_helper import get_model_config_name  # Local import to avoid cycles

            model_config_name = get_model_config_name(self)
            agent_name = self.name or f"xAI {self.model_name}"

            detail_parts: list[str] = []
            if provider_tools:
                detail_parts.append("with tools enabled")
            if self.reasoning not in {ReasoningMode.DISABLED, ReasoningMode.TEMPERATURE}:
                detail_parts.append(f"reasoning={self.reasoning.value}")
            if self.temperature is not None:
                detail_parts.append(f"temperature={self.temperature}")

            detail_suffix = f" ({', '.join(detail_parts)})" if detail_parts else ""
            logger.info(
                f"[bold yellow]{agent_name}:[/bold yellow] Sending request to {self.model_name} "
                f"(Config: {model_config_name}){detail_suffix}"
            )

            response = self._execute(prepared)

            logger.info(
                f"[bold green]{agent_name}:[/bold green] Received response from {self.model_name}"
            )

            parsed = parse_response(response)
            results: dict[str, Any] = {
                "agent": agent_name,
                "findings": parsed.findings,
                "tool_calls": parsed.tool_calls,
                "reasoning": parsed.reasoning,
                "encrypted_reasoning": parsed.encrypted_reasoning,
            }

            if parsed.tool_calls:
                logger.info(f"[bold yellow]{agent_name}:[/bold yellow] Model requested tool call(s).")

            return results
        except Exception as exc:  # pragma: no cover - defensive logging
            agent_name = self.name or "xAI Architect"
            logger.error(f"[bold red]Error in {agent_name}:[/bold red] {str(exc)}")
            return {
                "agent": agent_name,
                "error": str(exc),
            }

    async def stream_analyze(
        self,
        context: dict[str, Any],
        tools: list[Any] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        content = context.get("formatted_prompt") or self.format_prompt(context)

        provider_tools = resolve_tool_config(
            tools,
            self.tools_config,
            allow_tools=self._defaults.tools_allowed,
        )

        prepared = self._prepare_request(content, provider_tools)
        self._log_token_estimate(prepared)

        from agentrules.core.utils.model_config_helper import get_model_config_name  # Local import to avoid cycles

        model_config_name = get_model_config_name(self)
        agent_name = self.name or f"xAI {self.model_name}"

        detail_parts: list[str] = []
        if provider_tools:
            detail_parts.append("with tools enabled")
        if self.reasoning not in {ReasoningMode.DISABLED, ReasoningMode.TEMPERATURE}:
            detail_parts.append(f"reasoning={self.reasoning.value}")
        if self.temperature is not None:
            detail_parts.append(f"temperature={self.temperature}")

        detail_suffix = f" ({', '.join(detail_parts)})" if detail_parts else ""
        logger.info(
            f"[bold yellow]{agent_name}:[/bold yellow] Streaming request to {self.model_name} "
            f"(Config: {model_config_name}){detail_suffix}"
        )

        try:
            async for chunk in iterate_in_thread(lambda: self._stream_dispatch(prepared)):
                yield chunk
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(f"[bold red]Streaming error in {agent_name}:[/bold red] {str(exc)}")
            raise

    async def create_analysis_plan(self, phase1_results: dict, prompt: str | None = None) -> dict[str, Any]:
        context: dict[str, Any] = {"phase1_results": phase1_results}
        if prompt:
            context["formatted_prompt"] = prompt
        return await self._run_phase_request(context, result_key="plan", empty_value="No plan generated")

    async def synthesize_findings(self, phase3_results: dict, prompt: str | None = None) -> dict[str, Any]:
        context: dict[str, Any] = {"phase3_results": phase3_results}
        if prompt:
            context["formatted_prompt"] = prompt
        return await self._run_phase_request(
            context,
            result_key="analysis",
            empty_value="No synthesis generated",
        )

    async def final_analysis(self, consolidated_report: dict, prompt: str | None = None) -> dict[str, Any]:
        context: dict[str, Any] = {"consolidated_report": consolidated_report}
        if prompt:
            context["formatted_prompt"] = prompt
        return await self._run_phase_request(
            context,
            result_key="analysis",
            empty_value="No final analysis generated",
        )

    async def consolidate_results(self, all_results: dict, prompt: str | None = None) -> dict[str, Any]:
        context: dict[str, Any] = {"all_results": all_results}
        if prompt:
            context["formatted_prompt"] = prompt
        response = await self._run_phase_request(
            context,
            result_key="report",
            empty_value="No report generated",
            include_phase=True,
        )
        response.setdefault("phase", "Consolidation")
        return response

    # Client management ----------------------------------------------------------
    @property
    def client(self) -> Any:
        """Expose the underlying client for backwards compatibility with existing tests."""
        if self._client_override is not None:
            return self._client_override
        from .client import get_client  # Local import to avoid cycles

        return get_client(self.base_url)

    @client.setter
    def client(self, value: Any) -> None:
        self._client_override = value

    def _execute(self, prepared: PreparedRequest) -> Any:
        if self._client_override is not None:
            return self._client_override.chat.completions.create(**prepared.payload)
        return execute_chat_completion(prepared.payload, base_url=self.base_url)

    # Internal helpers -----------------------------------------------------------
    def _prepare_request(self, content: str, tools: list[Any] | None) -> PreparedRequest:
        return prepare_request(
            model_name=self.model_name,
            content=content,
            reasoning=self.reasoning,
            defaults=self._defaults,
            tools=tools,
            temperature=self.temperature,
        )

    def _log_token_estimate(self, prepared: PreparedRequest) -> None:
        result = estimate_tokens(
            provider=self.provider,
            model_name=self.model_name,
            payload=prepared.payload,
            api=getattr(prepared, "api", None),
            estimator_family=getattr(self._model_config, "estimator_family", None),
        )
        limit, _margin, effective = compute_effective_limits(
            getattr(self._model_config, "max_input_tokens", None),
            getattr(self._model_config, "safety_margin_tokens", None),
        )
        detail = f"estimate={result.estimated or 'n/a'} source={result.source}"
        if result.error:
            detail += f" error={result.error}"
        if limit:
            detail += f" limit={limit}"
        if effective:
            detail += f" effective_limit={effective}"
        logger.info(f"[bold cyan]Token preflight:[/bold cyan] {detail}")

    async def _run_phase_request(
        self,
        context: dict[str, Any],
        *,
        result_key: str,
        empty_value: str,
        include_phase: bool = False,
    ) -> dict[str, Any]:
        result = await self.analyze(context)
        response: dict[str, Any] = {
            result_key: result.get("findings") or empty_value,
        }

        if include_phase:
            response["phase"] = "Consolidation"

        if result.get("tool_calls"):
            response["tool_calls"] = result["tool_calls"]
        if result.get("reasoning"):
            response["reasoning"] = result["reasoning"]
        if result.get("encrypted_reasoning"):
            response["encrypted_reasoning"] = result["encrypted_reasoning"]
        if result.get("error"):
            response["error"] = result["error"]
        return response

    def _stream_dispatch(self, prepared: PreparedRequest) -> Iterator[StreamChunk]:
        client = self._client_override or self.client
        payload = dict(prepared.payload)
        payload["stream"] = True

        iterator = client.chat.completions.create(**payload)
        for chunk in iterator:
            choices = getattr(chunk, "choices", []) or []
            if not choices:
                continue
            choice = choices[0]
            delta = getattr(choice, "delta", None)
            if delta:
                text = getattr(delta, "content", None)
                if text:
                    yield StreamChunk(StreamEventType.TEXT_DELTA, str(text), None, None, None, None, chunk)

                reasoning = getattr(delta, "reasoning_content", None)
                if reasoning:
                    yield StreamChunk(StreamEventType.REASONING_DELTA, None, str(reasoning), None, None, None, chunk)

                tool_calls = getattr(delta, "tool_calls", None)
                if tool_calls:
                    for tool_delta in tool_calls:
                        tool_payload = self._coerce_tool_delta(tool_delta)
                        if tool_payload:
                            yield StreamChunk(
                                StreamEventType.TOOL_CALL_DELTA,
                                None,
                                None,
                                tool_payload,
                                None,
                                None,
                                chunk,
                            )

            finish_reason = getattr(choice, "finish_reason", None)
            if finish_reason:
                usage = getattr(chunk, "usage", None)
                yield StreamChunk(
                    StreamEventType.MESSAGE_END,
                    None,
                    None,
                    None,
                    str(finish_reason),
                    self._to_dict(usage),
                    chunk,
                )

    @staticmethod
    def _coerce_tool_delta(tool_delta: Any) -> dict[str, Any] | None:
        if tool_delta is None:
            return None
        payload = {
            "id": getattr(tool_delta, "id", None),
            "type": getattr(tool_delta, "type", None),
        }
        function_delta = getattr(tool_delta, "function", None)
        if function_delta:
            payload["function"] = {
                "name": getattr(function_delta, "name", None),
                "arguments": getattr(function_delta, "arguments", None),
            }
        return {key: value for key, value in payload.items() if value is not None} or None

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


__all__ = ["XaiArchitect"]
