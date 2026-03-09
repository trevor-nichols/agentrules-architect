"""Codex provider implementation of ``BaseArchitect``."""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from typing import Any

from agentrules.config.prompts.final_analysis_prompt import format_final_analysis_prompt
from agentrules.config.prompts.phase_2_prompts import format_phase2_structured_prompt
from agentrules.config.prompts.phase_4_prompts import format_phase4_prompt
from agentrules.core.agents.base import BaseArchitect, ModelProvider, ReasoningMode
from agentrules.core.configuration import ConfigManager, get_config_manager
from agentrules.core.utils.structured_outputs import (
    extract_phase2_agents,
    parse_structured_output_text,
    resolve_phase_result_value,
)
from agentrules.core.utils.system_prompt import build_agent_system_prompt, resolve_system_prompt
from agentrules.core.utils.token_estimator import compute_effective_limits, estimate_tokens

from .client import CodexAppServerClient
from .errors import CodexProtocolError
from .process import CodexAppServerProcess
from .request_builder import PreparedRequest, prepare_request
from .response_parser import ParsedResponse, collect_turn_notifications, parse_turn_notifications

logger = logging.getLogger("project_extractor")


class CodexArchitect(BaseArchitect):
    """Architect implementation backed by the Codex app-server runtime."""

    def __init__(
        self,
        model_name: str,
        reasoning: ReasoningMode = ReasoningMode.DISABLED,
        name: str | None = None,
        role: str | None = None,
        responsibilities: list[str] | None = None,
        prompt_template: str | None = None,
        system_prompt: str | None = None,
        tools_config: dict[str, Any] | None = None,
        model_config: Any | None = None,
        config_manager: ConfigManager | None = None,
        command: Sequence[str] | None = None,
        request_timeout_seconds: float = 300.0,
    ) -> None:
        super().__init__(
            provider=ModelProvider.CODEX,
            model_name=model_name,
            reasoning=reasoning,
            name=name,
            role=role,
            responsibilities=responsibilities,
            tools_config=tools_config,
            model_config=model_config,
            system_prompt=system_prompt,
        )
        self.prompt_template = prompt_template or self._get_default_prompt_template()
        self._config_manager = config_manager or get_config_manager()
        self._command = tuple(command) if command is not None else None
        self._request_timeout_seconds = request_timeout_seconds

    @staticmethod
    def _get_default_prompt_template() -> str:
        return (
            "Project context:\n"
            "{context}\n\n"
            "Complete the current analysis task using this context."
        )

    def format_prompt(self, context: dict[str, Any]) -> str:
        responsibilities_str = (
            "\n".join(f"- {item}" for item in self.responsibilities) if self.responsibilities else ""
        )
        context_str = json.dumps(context, indent=2) if isinstance(context, dict) else str(context)
        return self.prompt_template.format(
            agent_name=self.name or "Codex Architect",
            agent_role=self.role or "analyzing the project",
            agent_responsibilities=responsibilities_str,
            context=context_str,
        )

    def _resolve_system_prompt(self, context: dict[str, Any] | None = None) -> str:
        default_prompt = self.system_prompt
        if not default_prompt:
            default_prompt = build_agent_system_prompt(
                agent_name=self.name or "Codex Architect",
                agent_role=self.role or "analyzing the project",
                responsibilities=self.responsibilities,
            )
        resolved = resolve_system_prompt(context=context, default_prompt=default_prompt)
        if not resolved:
            raise ValueError(f"No system prompt could be resolved for Codex agent '{self.name or self.model_name}'.")
        return resolved

    async def analyze(self, context: dict[str, Any], tools: list[Any] | None = None) -> dict[str, Any]:
        del tools  # Codex relies on runtime-native tools; AgentRules tool bridging lands in later milestones.
        agent_name = self.name or "Codex Architect"
        phase_name = context.get("_structured_output_phase")
        force_unstructured = bool(context.get("_force_unstructured_output"))
        effective_phase = None if force_unstructured else phase_name if isinstance(phase_name, str) else None

        try:
            content = context.get("formatted_prompt") or self.format_prompt(context)
            system_prompt = self._resolve_system_prompt(context)
            prepared = self._prepare_request(
                content,
                system_prompt=system_prompt,
                phase_name=effective_phase,
                cwd=self._resolve_cwd(context),
            )
            self._log_token_estimate(prepared)

            from agentrules.core.utils.model_config_helper import get_model_config_name

            logger.info(
                "[bold cyan]%s:[/bold cyan] Sending request to %s via Codex app-server (Config: %s)",
                agent_name,
                self.model_name,
                get_model_config_name(self),
            )

            parsed = await self._execute_request(prepared)
            if parsed.error_message:
                raise CodexProtocolError(parsed.error_message)

            result: dict[str, Any] = {
                "agent": agent_name,
                "findings": parsed.findings,
                "tool_calls": parsed.tool_calls,
            }

            if "outputSchema" in prepared.turn_params:
                structured_payload = parse_structured_output_text(parsed.findings)
                if structured_payload is None:
                    raise CodexProtocolError(
                        f"Codex returned invalid structured output for {effective_phase or 'this request'}."
                    )
                result["structured_output"] = structured_payload

            return result
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("[bold red]Error in %s:[/bold red] %s", agent_name, str(exc))
            return {
                "agent": agent_name,
                "error": str(exc),
            }

    async def create_analysis_plan(self, phase1_results: dict, prompt: str | None = None) -> dict[str, Any]:
        return await self._run_phase_request(
            {"formatted_prompt": prompt or format_phase2_structured_prompt(phase1_results)},
            phase_name="phase2",
            result_key="plan",
            empty_value="No plan generated",
        )

    async def synthesize_findings(self, phase3_results: dict, prompt: str | None = None) -> dict[str, Any]:
        return await self._run_phase_request(
            {"formatted_prompt": prompt or format_phase4_prompt(phase3_results)},
            phase_name="phase4",
            result_key="analysis",
            empty_value="No synthesis generated",
        )

    async def final_analysis(self, consolidated_report: dict, prompt: str | None = None) -> dict[str, Any]:
        return await self._run_phase_request(
            {"formatted_prompt": prompt or format_final_analysis_prompt(consolidated_report)},
            phase_name="final",
            result_key="analysis",
            empty_value="No final analysis generated",
        )

    async def consolidate_results(self, all_results: dict, prompt: str | None = None) -> dict[str, Any]:
        default_prompt = (
            "Consolidate these results into a comprehensive report:\n\n"
            f"{json.dumps(all_results, indent=2)}"
        )
        response = await self._run_phase_request(
            {"formatted_prompt": prompt or default_prompt},
            phase_name="phase5",
            result_key="report",
            empty_value="No report generated",
            include_phase=True,
        )
        response.setdefault("phase", "Consolidation")
        return response

    def _prepare_request(
        self,
        content: str,
        *,
        system_prompt: str,
        phase_name: str | None,
        cwd: str | None,
    ) -> PreparedRequest:
        return prepare_request(
            config_manager=self._config_manager,
            model_name=self.model_name,
            content=content,
            system_prompt=system_prompt,
            reasoning=self.reasoning,
            phase_name=phase_name,
            cwd=cwd,
        )

    async def _execute_request(self, prepared: PreparedRequest) -> ParsedResponse:
        process = CodexAppServerProcess(prepared.launch_config, command=self._command)
        async with CodexAppServerClient(
            process,
            request_timeout_seconds=self._request_timeout_seconds,
        ) as client:
            thread = await client.start_thread(prepared.thread_params)
            if not thread.thread.id:
                raise CodexProtocolError("Codex thread/start response did not include a thread id.")

            turn_params = dict(prepared.turn_params)
            turn_params["threadId"] = thread.thread.id
            turn = await client.start_turn(turn_params)
            if not turn.turn.id:
                raise CodexProtocolError("Codex turn/start response did not include a turn id.")

            notifications = await collect_turn_notifications(
                client,
                thread_id=thread.thread.id,
                turn_id=turn.turn.id,
                timeout_seconds=self._request_timeout_seconds,
            )
            return parse_turn_notifications(
                notifications,
                thread_id=thread.thread.id,
                turn_id=turn.turn.id,
            )

    async def _run_phase_request(
        self,
        context: dict[str, Any],
        *,
        phase_name: str,
        result_key: str,
        empty_value: str,
        include_phase: bool = False,
    ) -> dict[str, Any]:
        request_context = dict(context)
        request_context["_structured_output_phase"] = phase_name
        result = await self.analyze(request_context)

        findings_source: Any = (
            result.get("structured_output")
            if isinstance(result.get("structured_output"), dict)
            else result.get("findings")
        )
        value, structured_payload = resolve_phase_result_value(
            phase=phase_name,
            result_key=result_key,
            findings=findings_source,
            empty_value=empty_value,
        )

        response: dict[str, Any] = {
            result_key: value,
            "error": result.get("error"),
        }
        if result.get("tool_calls"):
            response["tool_calls"] = result["tool_calls"]
        if include_phase:
            response["phase"] = "Consolidation"
        if structured_payload is not None:
            response["structured_output"] = structured_payload
            if phase_name == "phase2":
                phase2_agents = extract_phase2_agents(structured_payload)
                if phase2_agents is not None:
                    response["agents"] = phase2_agents
        return response

    def _resolve_cwd(self, context: dict[str, Any] | None) -> str | None:
        if not isinstance(context, dict):
            return None
        for key in ("_codex_cwd", "cwd"):
            value = context.get(key)
            if isinstance(value, str) and value.strip():
                return value
        return None

    def _log_token_estimate(self, prepared: PreparedRequest) -> None:
        result = estimate_tokens(
            provider=self.provider,
            model_name=self.model_name,
            payload=prepared.token_payload,
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
        logger.info("[bold cyan]Token preflight:[/bold cyan] %s", detail)


__all__ = ["CodexArchitect"]
