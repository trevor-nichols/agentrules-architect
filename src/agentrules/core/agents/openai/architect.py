"""Implementation of the OpenAI architect."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator, Iterator
from typing import Any

from agentrules.config.prompts.final_analysis_prompt import format_final_analysis_prompt
from agentrules.config.prompts.phase_2_prompts import format_phase2_prompt
from agentrules.config.prompts.phase_4_prompts import format_phase4_prompt
from agentrules.core.agents.base import BaseArchitect, ModelProvider, ReasoningMode
from agentrules.core.streaming import StreamChunk, StreamEventType
from agentrules.core.utils.async_stream import iterate_in_thread
from agentrules.core.utils.token_estimator import compute_effective_limits, estimate_tokens

from .client import execute_request, get_client
from .config import resolve_model_defaults
from .request_builder import PreparedRequest, prepare_request
from .response_parser import parse_response

logger = logging.getLogger("project_extractor")


class OpenAIArchitect(BaseArchitect):
    """
    Architect implementation backed by OpenAI's chat and responses APIs.

    The class coordinates prompt preparation, request construction, SDK dispatch,
    and response normalisation via the helper modules housed in this package.
    """

    def __init__(
        self,
        model_name: str = "o3",
        reasoning: ReasoningMode | None = None,
        temperature: float | None = None,
        name: str | None = None,
        role: str | None = None,
        responsibilities: list[str] | None = None,
        prompt_template: str | None = None,
        tools_config: dict | None = None,
        text_verbosity: str | None = None,
        model_config: Any | None = None,
    ):
        defaults = resolve_model_defaults(model_name)
        effective_reasoning = reasoning or defaults.default_reasoning

        effective_temperature = temperature
        if (
            effective_temperature is None
            and defaults.default_temperature is not None
            and effective_reasoning == ReasoningMode.TEMPERATURE
        ):
            effective_temperature = defaults.default_temperature

        super().__init__(
            provider=ModelProvider.OPENAI,
            model_name=model_name,
            reasoning=effective_reasoning,
            temperature=effective_temperature,
            name=name,
            role=role,
            responsibilities=responsibilities,
            tools_config=tools_config,
            model_config=model_config,
        )

        self.prompt_template = prompt_template or self._get_default_prompt_template()
        self.text_verbosity = text_verbosity
        self._use_responses_api = defaults.use_responses_api

    @property
    def supports_streaming(self) -> bool:
        return True

    @staticmethod
    def _get_default_prompt_template() -> str:
        """Default prompt template applied when none is provided."""
        return """You are {agent_name}, responsible for {agent_role}.

Your specific responsibilities are:
{agent_responsibilities}

Analyze this project context and provide a detailed report focused on your domain:

{context}

Format your response as a structured report with clear sections and findings."""

    def format_prompt(self, context: dict) -> str:
        """
        Fill the prompt template with the agent metadata and analysis context.

        Args:
            context: Dictionary containing the context for analysis

        Returns:
            Formatted prompt string
        """
        responsibilities_str = (
            "\n".join(f"- {r}" for r in self.responsibilities) if self.responsibilities else ""
        )
        context_str = json.dumps(context, indent=2) if isinstance(context, dict) else str(context)

        return self.prompt_template.format(
            agent_name=self.name or "OpenAI Architect",
            agent_role=self.role or "analyzing the project",
            agent_responsibilities=responsibilities_str,
            context=context_str,
        )

    async def analyze(self, context: dict, tools: list[Any] | None = None) -> dict:
        """
        Run analysis using the OpenAI model, potentially using tools.

        Args:
            context: Dictionary containing the context for analysis
            tools: Optional list of tools the model can use.
                   Follows OpenAI's tool definition format.

        Returns:
            Dictionary containing the analysis results, potential tool calls, or error information
        """
        try:
            content = context.get("formatted_prompt") or self.format_prompt(context)

            final_tools = self._resolve_tools(tools)
            prepared = self._prepare_request(content, final_tools)
            self._log_token_estimate(prepared)

            from agentrules.core.utils.model_config_helper import get_model_config_name

            model_config_name = get_model_config_name(self)
            agent_name = self.name or "OpenAI Architect"
            detail_suffix = " with tools enabled" if final_tools else ""
            api_label = "Responses API" if prepared.api == "responses" else "Chat Completions API"

            logger.info(
                f"[bold blue]{agent_name}:[/bold blue] Sending request to {self.model_name} "
                f"via {api_label} (Config: {model_config_name}){detail_suffix}"
            )

            response = execute_request(prepared)

            logger.info(
                f"[bold green]{agent_name}:[/bold green] Received response from {self.model_name}"
            )

            parsed = parse_response(response, prepared.api)
            results = {
                "agent": agent_name,
                "findings": parsed.findings,
                "tool_calls": parsed.tool_calls,
            }

            if parsed.tool_calls:
                logger.info(f"[bold blue]{agent_name}:[/bold blue] Model requested tool call(s).")

            return results
        except Exception as exc:  # pragma: no cover - defensive logging
            agent_name = self.name or "OpenAI Architect"
            logger.error(f"[bold red]Error in {agent_name}:[/bold red] {str(exc)}")
            return {
                "agent": agent_name,
                "error": str(exc),
            }

    def stream_analyze(
        self,
        context: dict[str, Any],
        tools: list[Any] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """Stream analysis output incrementally from the OpenAI model."""

        async def _generator() -> AsyncIterator[StreamChunk]:
            content = context.get("formatted_prompt") or self.format_prompt(context)
            final_tools = self._resolve_tools(tools)
            prepared = self._prepare_request(content, final_tools)
            self._log_token_estimate(prepared)

            from agentrules.core.utils.model_config_helper import get_model_config_name

            model_config_name = get_model_config_name(self)
            agent_name = self.name or "OpenAI Architect"
            detail_suffix = " with tools enabled" if final_tools else ""
            api_label = "Responses API" if prepared.api == "responses" else "Chat Completions API"

            logger.info(
                f"[bold blue]{agent_name}:[/bold blue] Streaming request to {self.model_name} "
                f"via {api_label} (Config: {model_config_name}){detail_suffix}"
            )

            try:
                async for chunk in iterate_in_thread(lambda: self._stream_dispatch(prepared)):
                    yield chunk
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error(f"[bold red]Streaming error in {agent_name}:[/bold red] {str(exc)}")
                raise

        return _generator()

    async def create_analysis_plan(self, phase1_results: dict, prompt: str | None = None) -> dict:
        """Create an analysis plan based on Phase 1 results."""
        return await self._run_simple_request(
            prompt or format_phase2_prompt(phase1_results),
            result_key="plan",
            empty_value="No plan generated",
        )

    async def synthesize_findings(self, phase3_results: dict, prompt: str | None = None) -> dict:
        """Synthesize findings from Phase 3."""
        return await self._run_simple_request(
            prompt or format_phase4_prompt(phase3_results),
            result_key="analysis",
            empty_value="No synthesis generated",
        )

    async def final_analysis(self, consolidated_report: dict, prompt: str | None = None) -> dict:
        """Perform final analysis on the consolidated report."""
        return await self._run_simple_request(
            prompt or format_final_analysis_prompt(consolidated_report),
            result_key="analysis",
            empty_value="No final analysis generated",
        )

    async def consolidate_results(self, all_results: dict, prompt: str | None = None) -> dict:
        """Consolidate results from all previous phases."""
        default_prompt = (
            "Consolidate these results into a comprehensive report:\n\n"
            f"{json.dumps(all_results, indent=2)}"
        )

        response = await self._run_simple_request(
            prompt or default_prompt,
            result_key="report",
            empty_value="No report generated",
            include_phase=True,
        )
        response.setdefault("phase", "Consolidation")
        return response

    def _prepare_request(
        self,
        content: str,
        tools: list[Any] | None = None,
    ) -> PreparedRequest:
        return prepare_request(
            model_name=self.model_name,
            content=content,
            reasoning=self.reasoning,
            temperature=self.temperature,
            tools=tools,
            text_verbosity=self.text_verbosity,
            use_responses_api=self._use_responses_api,
        )

    def _resolve_tools(self, tools: list[Any] | None) -> list[Any] | None:
        if not tools and not (self.tools_config and self.tools_config.get("enabled", False)):
            return None

        tool_list = tools or self.tools_config.get("tools", [])
        if not tool_list:
            return None

        from agentrules.core.agent_tools.tool_manager import ToolManager

        return ToolManager.get_provider_tools(tool_list, ModelProvider.OPENAI)

    async def _run_simple_request(
        self,
        content: str,
        *,
        result_key: str,
        empty_value: str,
        include_phase: bool = False,
    ) -> dict:
        try:
            prepared = self._prepare_request(content)
            self._log_token_estimate(prepared)
            response = execute_request(prepared)
            parsed = parse_response(response, prepared.api)

            result: dict[str, Any] = {result_key: parsed.findings or empty_value}
            if parsed.tool_calls:
                result["tool_calls"] = parsed.tool_calls

            if include_phase:
                result["phase"] = "Consolidation"

            return result
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(f"Error during OpenAI request: {str(exc)}")
            response: dict[str, Any] = {"error": str(exc)}
            if include_phase:
                response["phase"] = "Consolidation"
            return response

    def _stream_dispatch(self, prepared: PreparedRequest) -> Iterator[StreamChunk]:
        if prepared.api == "responses":
            yield from self._stream_responses_api(prepared)
        else:
            yield from self._stream_chat_api(prepared)

    def _stream_responses_api(self, prepared: PreparedRequest) -> Iterator[StreamChunk]:
        client = get_client()
        payload = dict(prepared.payload)

        with client.responses.stream(**payload) as stream:  # type: ignore[arg-type]
            for event in stream:
                event_type = getattr(event, "type", "")
                if event_type == "response.output_text.delta":
                    text = getattr(event, "delta", None)
                    if text:
                        yield StreamChunk(StreamEventType.TEXT_DELTA, str(text), None, None, None, None, event)
                    continue

                if event_type == "response.tool_call.delta":
                    delta = getattr(event, "delta", None)
                    if delta:
                        yield StreamChunk(
                            StreamEventType.TOOL_CALL_DELTA,
                            None,
                            None,
                            self._coerce_to_dict(delta),
                            None,
                            None,
                            event,
                        )
                    continue

                if event_type == "response.completed":
                    response_obj = getattr(event, "response", None)
                    usage = getattr(response_obj, "usage", None)
                    finish_reason = getattr(response_obj, "finish_reason", None)
                    yield StreamChunk(
                        StreamEventType.MESSAGE_END,
                        None,
                        None,
                        None,
                        finish_reason,
                        self._coerce_to_dict(usage),
                        event,
                    )
                    continue

                if event_type == "response.error":
                    error = getattr(event, "error", None)
                    message = getattr(error, "message", None) if error else None
                    yield StreamChunk(
                        StreamEventType.ERROR,
                        str(message or error or "Unknown error"),
                        None,
                        None,
                        None,
                        None,
                        event,
                    )
                    continue

                if event_type in {"response.canceled", "response.truncated"}:
                    yield StreamChunk(
                        StreamEventType.MESSAGE_END,
                        None,
                        None,
                        None,
                        event_type.split(".")[-1],
                        None,
                        event,
                    )
                    continue

                if event_type == "response.output_text.done":
                    continue

                yield StreamChunk(StreamEventType.SYSTEM, None, None, None, None, None, event)

    def _stream_chat_api(self, prepared: PreparedRequest) -> Iterator[StreamChunk]:
        client = get_client()
        payload = dict(prepared.payload)
        payload["stream"] = True

        response_iterator = client.chat.completions.create(**payload)
        for chunk in response_iterator:
            choices = getattr(chunk, "choices", []) or []
            if not choices:
                continue
            choice = choices[0]
            delta = getattr(choice, "delta", None)
            if delta:
                text = getattr(delta, "content", None)
                if text:
                    yield StreamChunk(StreamEventType.TEXT_DELTA, str(text), None, None, None, None, chunk)

                tool_calls = getattr(delta, "tool_calls", None)
                if tool_calls:
                    for tool_delta in tool_calls:
                        tool_payload = self._coerce_tool_call_delta(tool_delta)
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
                    self._coerce_to_dict(usage),
                    chunk,
                )

    @staticmethod
    def _coerce_to_dict(value: Any) -> dict[str, Any] | None:
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

    def _coerce_tool_call_delta(self, tool_delta: Any) -> dict[str, Any] | None:
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
        logger.info(f"[bold blue]Token preflight:[/bold blue] {detail}")


__all__ = ["OpenAIArchitect"]
