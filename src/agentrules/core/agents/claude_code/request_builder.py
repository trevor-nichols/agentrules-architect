"""Helpers for preparing Claude Code Agent SDK requests."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentrules.core.agents.base import ReasoningMode
from agentrules.core.configuration import ConfigManager
from agentrules.core.utils.structured_outputs import build_claude_code_output_format

DEFAULT_THINKING_BUDGET = 16_000
READ_ONLY_ALLOWED_TOOLS = ("Read", "Glob", "Grep")
RESEARCH_ALLOWED_TOOLS = ("Read", "Glob", "Grep", "WebSearch", "WebFetch")
DEFAULT_DISALLOWED_TOOLS = (
    "Bash",
    "Edit",
    "MultiEdit",
    "NotebookEdit",
    "Write",
)


@dataclass(frozen=True)
class PreparedRequest:
    """Represents a fully prepared Claude Code Agent SDK request."""

    prompt: str
    options: dict[str, Any]
    token_payload: dict[str, Any]
    execution_timeout_seconds: float


def prepare_request(
    *,
    config_manager: ConfigManager,
    model_name: str,
    content: str,
    system_prompt: str,
    reasoning: ReasoningMode,
    phase_name: str | None,
    cwd: str | None = None,
    effort: str | None = None,
    tools_config: dict[str, Any] | None = None,
) -> PreparedRequest:
    """Build Claude Agent SDK options for one request."""

    normalized_cwd = _normalize_cwd(cwd)
    runtime_config = config_manager.get_claude_code_config()
    output_format = build_claude_code_output_format(phase_name)

    options: dict[str, Any] = {
        "allowed_tools": list(_resolve_allowed_tools(tools_config)),
        "cwd": normalized_cwd,
        "disallowed_tools": list(DEFAULT_DISALLOWED_TOOLS),
        "env": config_manager.build_claude_code_environment(),
        "max_turns": runtime_config.max_turns,
        "model": model_name,
        "permission_mode": "dontAsk",
        "setting_sources": [],
        "system_prompt": _build_system_prompt_option(system_prompt),
        "tools": {"type": "preset", "preset": "claude_code"},
    }

    if runtime_config.cli_path is not None:
        options["cli_path"] = runtime_config.cli_path

    thinking = _build_thinking_config(reasoning)
    if thinking is not None:
        options["thinking"] = thinking

    resolved_effort = _resolve_effort(reasoning, effort)
    if resolved_effort is not None:
        options["effort"] = resolved_effort

    if output_format is not None:
        options["output_format"] = output_format

    if runtime_config.max_budget_usd is not None:
        options["max_budget_usd"] = runtime_config.max_budget_usd

    token_payload = {
        "input": content,
        "instructions": system_prompt,
    }

    return PreparedRequest(
        prompt=content,
        options=options,
        token_payload=token_payload,
        execution_timeout_seconds=runtime_config.request_timeout_seconds,
    )


def _normalize_cwd(cwd: str | None) -> str:
    candidate = cwd or os.getcwd()
    return str(Path(candidate).expanduser().resolve())


def _resolve_allowed_tools(tools_config: dict[str, Any] | None) -> tuple[str, ...]:
    if tools_config and tools_config.get("enabled"):
        return RESEARCH_ALLOWED_TOOLS
    return READ_ONLY_ALLOWED_TOOLS


def _build_system_prompt_option(system_prompt: str) -> dict[str, Any]:
    return {
        "type": "preset",
        "preset": "claude_code",
        "append": system_prompt,
        "exclude_dynamic_sections": True,
    }


def _build_thinking_config(reasoning: ReasoningMode) -> dict[str, Any] | None:
    if reasoning == ReasoningMode.DYNAMIC:
        return {"type": "adaptive"}
    if reasoning == ReasoningMode.ENABLED:
        return {"type": "enabled", "budget_tokens": DEFAULT_THINKING_BUDGET}
    return None


def _resolve_effort(reasoning: ReasoningMode, effort: str | None) -> str | None:
    if effort in {"low", "medium", "high", "max"}:
        return effort
    if reasoning == ReasoningMode.LOW:
        return "low"
    if reasoning == ReasoningMode.MEDIUM:
        return "medium"
    if reasoning in {ReasoningMode.HIGH, ReasoningMode.XHIGH}:
        return "high" if reasoning == ReasoningMode.HIGH else "max"
    return None


__all__ = [
    "DEFAULT_DISALLOWED_TOOLS",
    "DEFAULT_THINKING_BUDGET",
    "PreparedRequest",
    "READ_ONLY_ALLOWED_TOOLS",
    "RESEARCH_ALLOWED_TOOLS",
    "prepare_request",
]
