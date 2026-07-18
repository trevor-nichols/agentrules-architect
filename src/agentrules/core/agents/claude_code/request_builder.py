"""Helpers for preparing Claude Code Agent SDK requests."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentrules.core.agents.anthropic.capabilities import (
    ThinkingPolicy,
    supported_effort_levels,
    supports_adaptive_thinking,
    supports_manual_thinking,
    thinking_policy,
)
from agentrules.core.agents.base import ReasoningMode
from agentrules.core.configuration import CLAUDE_CODE_API_KEY_ENV_VARS, ConfigManager
from agentrules.core.types.models import (
    CLAUDE_CODE_RUNTIME_DEFAULT_MODEL,
    is_claude_code_runtime_managed_model,
)
from agentrules.core.utils.structured_outputs import build_claude_code_output_format

DEFAULT_THINKING_BUDGET = 16_000
_SUPPORTED_EFFORT_LEVELS = frozenset({"low", "medium", "high", "xhigh", "max"})
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
    sanitized_env_vars: tuple[str, ...]


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
    sanitized_env_vars = _resolve_sanitized_env_vars(
        auth_strategy=runtime_config.auth_strategy,
        sanitize_api_key_env=runtime_config.sanitize_api_key_env,
    )
    resolved_cli_path = _resolve_cli_path(
        config_manager,
        configured_cli_path=runtime_config.cli_path,
    )
    _validate_runtime_model_support(config_manager, model_name)

    options: dict[str, Any] = {
        "allowed_tools": list(_resolve_allowed_tools(tools_config)),
        "cwd": normalized_cwd,
        "disallowed_tools": list(DEFAULT_DISALLOWED_TOOLS),
        "env": config_manager.build_claude_code_environment(),
        "max_turns": runtime_config.max_turns,
        "permission_mode": "dontAsk",
        "setting_sources": [],
        "system_prompt": _build_system_prompt_option(system_prompt),
        "tools": {"type": "preset", "preset": "claude_code"},
    }
    if model_name != CLAUDE_CODE_RUNTIME_DEFAULT_MODEL:
        options["model"] = model_name

    if resolved_cli_path is not None:
        options["cli_path"] = resolved_cli_path

    if not is_claude_code_runtime_managed_model(model_name):
        thinking = _build_thinking_config(model_name, reasoning)
        if thinking is not None:
            options["thinking"] = thinking

        resolved_effort = _resolve_effort(model_name, reasoning, effort)
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
        sanitized_env_vars=sanitized_env_vars,
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


def _build_thinking_config(model_name: str, reasoning: ReasoningMode) -> dict[str, Any] | None:
    policy = thinking_policy(model_name)
    if policy == ThinkingPolicy.ALWAYS_ADAPTIVE:
        if reasoning == ReasoningMode.DISABLED:
            raise ValueError(
                f"Model '{model_name}' always uses adaptive thinking and cannot disable it in Claude Code."
            )
        return None
    if policy == ThinkingPolicy.ADAPTIVE_DEFAULT:
        if reasoning == ReasoningMode.DISABLED:
            return {"type": "disabled"}
        if reasoning in {ReasoningMode.DYNAMIC, ReasoningMode.ENABLED}:
            return {"type": "adaptive"}

    if reasoning == ReasoningMode.DYNAMIC:
        if not supports_adaptive_thinking(model_name):
            raise ValueError(
                f"Model '{model_name}' does not support adaptive thinking in Claude Code runtime."
            )
        return {"type": "adaptive"}
    if reasoning == ReasoningMode.ENABLED:
        if supports_manual_thinking(model_name):
            return {"type": "enabled", "budget_tokens": DEFAULT_THINKING_BUDGET}
        if supports_adaptive_thinking(model_name):
            return {"type": "adaptive"}
        raise ValueError(
            f"Model '{model_name}' does not support enabled or adaptive thinking in Claude Code runtime."
        )
    return None


def _resolve_effort(model_name: str, reasoning: ReasoningMode, effort: str | None) -> str | None:
    allowed_effort_levels = supported_effort_levels(model_name)

    if effort is not None:
        normalized_effort = effort.strip().lower()
        if normalized_effort not in _SUPPORTED_EFFORT_LEVELS:
            supported = ", ".join(sorted(_SUPPORTED_EFFORT_LEVELS))
            raise ValueError(f"Invalid effort value '{effort}'. Supported values: {supported}.")
        if normalized_effort not in allowed_effort_levels:
            supported = ", ".join(sorted(allowed_effort_levels))
            raise ValueError(
                f"Effort '{normalized_effort}' is not supported for model '{model_name}'. "
                f"Supported values for this model: {supported}."
            )
        return normalized_effort

    if reasoning == ReasoningMode.LOW:
        return "low"
    if reasoning == ReasoningMode.MEDIUM:
        return "medium"
    if reasoning == ReasoningMode.HIGH:
        return "high"
    if reasoning == ReasoningMode.XHIGH:
        if "xhigh" in allowed_effort_levels:
            return "xhigh"
        if "max" in allowed_effort_levels:
            return "max"
        if "high" in allowed_effort_levels:
            return "high"
    if reasoning == ReasoningMode.MAX:
        if "max" in allowed_effort_levels:
            return "max"
        if "xhigh" in allowed_effort_levels:
            return "xhigh"
        if "high" in allowed_effort_levels:
            return "high"
    return None


def _validate_runtime_model_support(config_manager: ConfigManager, model_name: str) -> None:
    minimum_version = config_manager.minimum_claude_code_version_for_model(model_name)
    if minimum_version is None:
        return

    runtime_version = config_manager.get_claude_code_runtime_version()
    if runtime_version is None:
        raise ValueError(
            f"Model '{model_name}' requires Claude Code {minimum_version} or later, but the resolved "
            "runtime version could not be verified."
        )
    if runtime_version < minimum_version:
        raise ValueError(
            f"Model '{model_name}' requires Claude Code {minimum_version} or later, "
            f"but the resolved runtime reports {runtime_version}."
        )


def _resolve_sanitized_env_vars(
    *,
    auth_strategy: str,
    sanitize_api_key_env: bool,
) -> tuple[str, ...]:
    if auth_strategy == "oauth" and sanitize_api_key_env:
        return CLAUDE_CODE_API_KEY_ENV_VARS
    return ()


def _resolve_cli_path(
    config_manager: ConfigManager,
    *,
    configured_cli_path: str | None,
) -> str | None:
    if configured_cli_path is None:
        return None
    resolved = config_manager.resolve_claude_code_executable()
    if resolved is None:
        raise ValueError(
            f"Configured Claude Code executable could not be resolved: {configured_cli_path!r}."
        )
    return resolved


__all__ = [
    "DEFAULT_DISALLOWED_TOOLS",
    "DEFAULT_THINKING_BUDGET",
    "PreparedRequest",
    "READ_ONLY_ALLOWED_TOOLS",
    "RESEARCH_ALLOWED_TOOLS",
    "prepare_request",
]
