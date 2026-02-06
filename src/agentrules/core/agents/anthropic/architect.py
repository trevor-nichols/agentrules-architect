"""Anthropic provider implementation of ``BaseArchitect``."""
from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator, Iterator
from typing import Any

from agentrules.core.agents.base import BaseArchitect, ModelProvider, ReasoningMode
from agentrules.core.streaming import StreamChunk, StreamEventType
from agentrules.core.utils.async_stream import iterate_in_thread
from agentrules.core.utils.token_estimator import compute_effective_limits, estimate_tokens

from .client import execute_message_request, get_client
from .prompting import default_prompt_template, format_prompt
from .request_builder import PreparedRequest, prepare_request
from .response_parser import parse_response
from .tooling import resolve_tool_config

logger = logging.getLogger("project_extractor")


class AnthropicArchitect(BaseArchitect):
    """Architect class for interacting with Anthropic's Claude models."""

    def __init__(
        self,
        model_name: str = "claude-sonnet-4-5",
        reasoning: ReasoningMode = ReasoningMode.DISABLED,
        name: str | None = None,
        role: str | None = None,
        responsibilities: list[str] | None = None,
        prompt_template: str | None = None,
        tools_config: dict[str, Any] | None = None,
        model_config: Any | None = None,
    ) -> None:
        super().__init__(
            provider=ModelProvider.ANTHROPIC,
            model_name=model_name,
            reasoning=reasoning,
            name=name,
            role=role,
            responsibilities=responsibilities,
            tools_config=tools_config,
            model_config=model_config,
        )
        self.prompt_template = prompt_template or default_prompt_template()

    @property
    def supports_streaming(self) -> bool:
        return True

    # Public API -----------------------------------------------------------------
    def format_prompt(self, context: dict[str, Any]) -> str:
        return format_prompt(
            template=self.prompt_template,
            agent_name=self.name or "Claude Architect",
            agent_role=self.role or "analyzing the project",
            responsibilities=self.responsibilities,
            context=context,
        )

    async def analyze(self, context: dict[str, Any], tools: list[Any] | None = None) -> dict[str, Any]:
        try:
            prompt = context.get("formatted_prompt") or self.format_prompt(context)
            provider_tools = resolve_tool_config(tools, self.tools_config)
            prepared = self._prepare_request(prompt, provider_tools)
            self._log_token_estimate(prepared)

            from agentrules.core.utils.model_config_helper import get_model_config_name  # Local import to avoid cycles

            model_config_name = get_model_config_name(self)
            agent_name = self.name or "Claude Architect"
            detail_parts: list[str] = []
            if "thinking" in prepared.payload:
                thinking = prepared.payload["thinking"]
                if isinstance(thinking, dict):
                    budget = thinking.get("budget_tokens")
                    detail = thinking.get("type")
                    if detail == "enabled" and budget:
                        detail_parts.append(f"with thinking (budget={budget})")
                    elif detail:
                        detail_parts.append(f"with thinking ({detail})")
            if provider_tools:
                detail_parts.append("with tools enabled")

            detail_suffix = f" ({', '.join(detail_parts)})" if detail_parts else ""
            logger.info(
                f"[bold purple]{agent_name}:[/bold purple] Sending request to {self.model_name} "
                f"(Config: {model_config_name}){detail_suffix}"
            )

            response = execute_message_request(prepared.payload)

            logger.info(
                f"[bold green]{agent_name}:[/bold green] Received response from {self.model_name}"
            )

            parsed = parse_response(response)
            results: dict[str, Any] = {
                "agent": agent_name,
                "findings": parsed.findings,
                "tool_calls": parsed.tool_calls,
            }

            if parsed.tool_calls:
                logger.info(
                    f"[bold purple]{agent_name}:[/bold purple] Model requested tool call(s)."
                )

            return results
        except Exception as exc:  # pragma: no cover - defensive logging
            agent_name = self.name or "Claude Architect"
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
        async def _generator() -> AsyncIterator[StreamChunk]:
            prompt = context.get("formatted_prompt") or self.format_prompt(context)
            provider_tools = resolve_tool_config(tools, self.tools_config)
            prepared = self._prepare_request(prompt, provider_tools)
            self._log_token_estimate(prepared)

            from agentrules.core.utils.model_config_helper import get_model_config_name  # Local import to avoid cycles

            model_config_name = get_model_config_name(self)
            agent_name = self.name or "Claude Architect"
            detail_parts: list[str] = []
            if "thinking" in prepared.payload:
                thinking = prepared.payload["thinking"]
                if isinstance(thinking, dict):
                    detail = thinking.get("type")
                    budget = thinking.get("budget_tokens")
                    if detail and budget:
                        detail_parts.append(f"with thinking ({detail}, budget={budget})")
                    elif detail:
                        detail_parts.append(f"with thinking ({detail})")
            if provider_tools:
                detail_parts.append("with tools enabled")

            detail_suffix = f" ({', '.join(detail_parts)})" if detail_parts else ""
            logger.info(
                f"[bold purple]{agent_name}:[/bold purple] Streaming request to {self.model_name} "
                f"(Config: {model_config_name}){detail_suffix}"
            )

            try:
                async for chunk in iterate_in_thread(lambda: self._stream_messages(prepared)):
                    yield chunk
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error(f"[bold red]Streaming error in {agent_name}:[/bold red] {str(exc)}")
                raise

        return _generator()

    async def create_analysis_plan(self, phase1_results: dict, prompt: str | None = None) -> dict[str, Any]:
        context: dict[str, Any] = {"phase1_results": phase1_results}
        if prompt:
            context["formatted_prompt"] = prompt
        result = await self.analyze(context)
        response: dict[str, Any] = {
            "plan": result.get("findings", "No plan generated"),
            "error": result.get("error"),
        }
        if result.get("tool_calls"):
            response["tool_calls"] = result["tool_calls"]
        return response

    async def synthesize_findings(self, phase3_results: dict, prompt: str | None = None) -> dict[str, Any]:
        context: dict[str, Any] = {"phase3_results": phase3_results}
        if prompt:
            context["formatted_prompt"] = prompt
        result = await self.analyze(context)
        response: dict[str, Any] = {
            "analysis": result.get("findings", "No synthesis generated"),
            "error": result.get("error"),
        }
        if result.get("tool_calls"):
            response["tool_calls"] = result["tool_calls"]
        return response

    async def final_analysis(self, consolidated_report: dict, prompt: str | None = None) -> dict[str, Any]:
        context: dict[str, Any] = {"consolidated_report": consolidated_report}
        if prompt:
            context["formatted_prompt"] = prompt
        result = await self.analyze(context)
        response: dict[str, Any] = {
            "analysis": result.get("findings", "No final analysis generated"),
            "error": result.get("error"),
        }
        if result.get("tool_calls"):
            response["tool_calls"] = result["tool_calls"]
        return response

    async def consolidate_results(self, all_results: dict, prompt: str | None = None) -> dict[str, Any]:
        content = prompt or (
            "Consolidate these results into a comprehensive report:\n\n"
            f"{json.dumps(all_results, indent=2)}"
        )

        result = await self.analyze({"formatted_prompt": content})
        response: dict[str, Any] = {
            "phase": "Consolidation",
            "report": result.get("findings", "No report generated"),
        }
        if result.get("error"):
            response["error"] = result["error"]
        if result.get("tool_calls"):
            response["tool_calls"] = result["tool_calls"]
        return response

    # Internal helpers -----------------------------------------------------------
    def _prepare_request(
        self,
        prompt: str,
        tools: list[Any] | None,
    ) -> PreparedRequest:
        return prepare_request(
            model_name=self.model_name,
            prompt=prompt,
            reasoning=self.reasoning,
            tools=tools,
            effort=getattr(self._model_config, "anthropic_effort", None),
        )

    def _log_token_estimate(self, prepared: PreparedRequest) -> None:
        result = estimate_tokens(
            provider=self.provider,
            model_name=self.model_name,
            payload=prepared.payload,
            estimator_family=getattr(self._model_config, "estimator_family", None),
            client=get_client(),
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
        logger.info(f"[bold purple]Token preflight:[/bold purple] {detail}")

    def _stream_messages(self, prepared: PreparedRequest) -> Iterator[StreamChunk]:
        client = get_client()
        payload = dict(prepared.payload)
        payload["stream"] = True
        active_tool_inputs: dict[int, dict[str, Any]] = {}

        with client.messages.stream(**payload) as stream:  # type: ignore[arg-type]
            for event in stream.events():
                event_type = getattr(event, "type", "")

                if event_type == "content_block_start":
                    block = getattr(event, "content_block", None)
                    index_obj = getattr(event, "index", None)
                    if (
                        block
                        and getattr(block, "type", None) == "tool_use"
                        and isinstance(index_obj, int)
                    ):
                        active_tool_inputs[index_obj] = {
                            "id": getattr(block, "id", None),
                            "name": getattr(block, "name", None),
                            "buffer": [],
                        }
                    continue

                if event_type == "content_block_delta":
                    index_obj = getattr(event, "index", None)
                    delta = getattr(event, "delta", None)
                    delta_type = getattr(delta, "type", None)

                    if delta_type == "text_delta":
                        text = getattr(delta, "text", None)
                        if text:
                            yield StreamChunk(
                                StreamEventType.TEXT_DELTA,
                                str(text),
                                None,
                                None,
                                None,
                                None,
                                event,
                            )
                        continue

                    if delta_type == "thinking_delta":
                        thinking = getattr(delta, "thinking", None)
                        if thinking:
                            yield StreamChunk(
                                StreamEventType.REASONING_DELTA,
                                None,
                                str(thinking),
                                None,
                                None,
                                None,
                                event,
                            )
                        continue

                    if (
                        delta_type == "input_json_delta"
                        and isinstance(index_obj, int)
                        and index_obj in active_tool_inputs
                    ):
                        partial = getattr(delta, "partial_json", None)
                        if partial:
                            active_tool_inputs[index_obj]["buffer"].append(partial)
                            yield StreamChunk(
                                StreamEventType.TOOL_CALL_DELTA,
                                None,
                                None,
                                {
                                    "partial_json": partial,
                                    "id": active_tool_inputs[index_obj].get("id"),
                                    "name": active_tool_inputs[index_obj].get("name"),
                                },
                                None,
                                None,
                                event,
                            )
                        continue

                    continue

                if event_type == "content_block_stop":
                    index_obj = getattr(event, "index", None)
                    tool_meta = active_tool_inputs.pop(index_obj, None) if isinstance(index_obj, int) else None
                    if tool_meta:
                        full_json = "".join(tool_meta["buffer"])
                        tool_payload: dict[str, Any] = {
                            "id": tool_meta.get("id"),
                            "name": tool_meta.get("name"),
                        }
                        if full_json:
                            try:
                                tool_payload["input"] = json.loads(full_json)
                            except json.JSONDecodeError:
                                tool_payload["input"] = full_json
                        yield StreamChunk(
                            StreamEventType.TOOL_CALL_DELTA,
                            None,
                            None,
                            tool_payload,
                            None,
                            None,
                            event,
                        )
                    continue

                if event_type == "message_delta":
                    delta_event = getattr(event, "delta", None)
                    usage = getattr(delta_event, "usage", None)
                    if usage:
                        yield StreamChunk(
                            StreamEventType.MESSAGE_DELTA,
                            None,
                            None,
                            None,
                            None,
                            self._to_dict(usage),
                            event,
                        )
                    continue

                if event_type == "message_stop":
                    final = stream.get_final_response()
                    usage = getattr(final, "usage", None)
                    stop_reason = getattr(final, "stop_reason", None)
                    yield StreamChunk(
                        StreamEventType.MESSAGE_END,
                        None,
                        None,
                        None,
                        stop_reason,
                        self._to_dict(usage),
                        final,
                    )
                    continue

                if event_type == "error":
                    error = getattr(event, "error", None)
                    message = str(getattr(error, "message", error))
                    yield StreamChunk(StreamEventType.ERROR, message, None, None, None, None, event)
                    continue

                if event_type == "ping":
                    continue

                yield StreamChunk(StreamEventType.SYSTEM, None, None, None, None, None, event)

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


__all__ = ["AnthropicArchitect"]
