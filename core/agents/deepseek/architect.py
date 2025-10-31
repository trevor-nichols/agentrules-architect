"""DeepSeek provider implementation of ``BaseArchitect``."""

from __future__ import annotations

import logging
from typing import Any

from core.agents.base import BaseArchitect, ModelProvider, ReasoningMode

from .client import execute_chat_completion
from .config import ModelDefaults, resolve_base_url, resolve_model_defaults
from .prompting import default_prompt_template
from .prompting import format_prompt as format_analysis_prompt
from .request_builder import PreparedRequest, prepare_request
from .response_parser import parse_response
from .tooling import resolve_tool_config

logger = logging.getLogger("project_extractor")


class DeepSeekArchitect(BaseArchitect):
    """Architect implementation backed by DeepSeek's OpenAI-compatible API."""

    def __init__(
        self,
        model_name: str = "deepseek-chat",
        reasoning: ReasoningMode | None = None,
        temperature: float | None = None,
        name: str | None = None,
        role: str | None = None,
        responsibilities: list[str] | None = None,
        prompt_template: str | None = None,
        base_url: str | None = None,
        tools_config: dict[str, Any] | None = None,
    ) -> None:
        self._defaults: ModelDefaults = resolve_model_defaults(model_name)
        effective_reasoning = reasoning or self._defaults.default_reasoning

        self._client_override: Any | None = None
        supports_sampling = self.model_name.lower() != "deepseek-reasoner"
        effective_temperature = temperature if supports_sampling else None
        if temperature is not None and not supports_sampling:
            logger.info(
                (
                    "[bold teal]%s:[/bold teal] Ignoring temperature %.2f because %s "
                    "does not support sampling parameters."
                ),
                name or "DeepSeek Architect",
                temperature,
                model_name,
            )

        super().__init__(
            provider=ModelProvider.DEEPSEEK,
            model_name=model_name,
            reasoning=effective_reasoning,
            temperature=effective_temperature,
            name=name,
            role=role,
            responsibilities=responsibilities,
            tools_config=tools_config,
        )

        self.prompt_template = prompt_template or default_prompt_template()
        self.base_url = resolve_base_url(base_url)

    # Public API -----------------------------------------------------------------
    def format_prompt(self, context: dict[str, Any]) -> str:
        return format_analysis_prompt(
            template=self.prompt_template,
            agent_name=self.name or "DeepSeek Architect",
            agent_role=self.role or "code architecture analysis",
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

            tools_requested = bool(tools or (self.tools_config and self.tools_config.get("enabled")))
            if tools_requested and not self._defaults.tools_allowed:
                logger.info(
                    (
                        "[bold teal]%s:[/bold teal] Ignoring tool configuration because %s "
                        "does not support function calling."
                    ),
                    self.name or "DeepSeek Architect",
                    self.model_name,
                )

            prepared = self._prepare_request(content, provider_tools)

            from core.utils.model_config_helper import get_model_config_name  # Local import to avoid cycles

            model_config_name = get_model_config_name(self)
            agent_name = self.name or f"DeepSeek {self.model_name.replace('-', ' ').title()}"
            detail_parts: list[str] = []
            if provider_tools:
                detail_parts.append("with tools enabled")
            if self._defaults.max_output_tokens:
                detail_parts.append(f"max_tokens={self._defaults.max_output_tokens}")

            detail_suffix = f" ({', '.join(detail_parts)})" if detail_parts else ""
            logger.info(
                f"[bold teal]{agent_name}:[/bold teal] Sending request to {self.model_name} "
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
                "reasoning": parsed.reasoning,
                "tool_calls": parsed.tool_calls,
            }

            if parsed.tool_calls:
                logger.info(
                    f"[bold teal]{agent_name}:[/bold teal] Model requested tool call(s)."
                )

            return results
        except Exception as exc:  # pragma: no cover - defensive logging
            agent_name = self.name or "DeepSeek Architect"
            logger.error(f"[bold red]Error in {agent_name}:[/bold red] {str(exc)}")
            return {
                "agent": agent_name,
                "error": str(exc),
            }

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
        """
        Expose the underlying client for backwards compatibility with existing tests.
        """
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
            "reasoning": result.get("reasoning"),
        }

        if include_phase:
            response["phase"] = "Consolidation"

        if result.get("tool_calls"):
            response["tool_calls"] = result["tool_calls"]
        if result.get("error"):
            response["error"] = result["error"]
        return response
