"""Helpers for preparing Codex app-server requests."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentrules.core.agents.base import ReasoningMode
from agentrules.core.agents.codex.process import CodexProcessLaunchConfig
from agentrules.core.configuration import ConfigManager
from agentrules.core.utils.structured_outputs import build_codex_output_schema


@dataclass(frozen=True)
class PreparedRequest:
    """Represents a fully prepared Codex request bundle."""

    launch_config: CodexProcessLaunchConfig
    thread_params: dict[str, Any]
    turn_params: dict[str, Any]
    token_payload: dict[str, Any]


def prepare_request(
    *,
    config_manager: ConfigManager,
    model_name: str,
    content: str,
    system_prompt: str,
    reasoning: ReasoningMode,
    phase_name: str | None,
    cwd: str | None = None,
) -> PreparedRequest:
    """Build the launch config and thread/turn payloads for one Codex request."""

    normalized_cwd = _normalize_cwd(cwd)
    launch_config = config_manager.build_codex_launch_config(
        cwd=normalized_cwd,
        config_overrides={"developer_instructions": system_prompt},
    )
    effort = _resolve_reasoning_effort(reasoning)
    output_schema = build_codex_output_schema(phase_name)

    thread_params: dict[str, Any] = {
        "approvalPolicy": "never",
        "cwd": normalized_cwd,
        "ephemeral": True,
        "model": model_name,
        "sandbox": "read-only",
    }

    turn_params: dict[str, Any] = {
        "approvalPolicy": "never",
        "cwd": normalized_cwd,
        "input": [{"type": "text", "text": content}],
        "model": model_name,
        "sandboxPolicy": _build_read_only_sandbox_policy(normalized_cwd),
        "summary": _resolve_reasoning_summary(effort),
    }
    if effort is not None:
        turn_params["effort"] = effort
    if output_schema is not None:
        turn_params["outputSchema"] = output_schema

    token_payload = {
        "input": content,
        "instructions": system_prompt,
    }

    return PreparedRequest(
        launch_config=launch_config,
        thread_params=thread_params,
        turn_params=turn_params,
        token_payload=token_payload,
    )


def _normalize_cwd(cwd: str | None) -> str:
    candidate = cwd or os.getcwd()
    return str(Path(candidate).expanduser().resolve())


def _resolve_reasoning_effort(reasoning: ReasoningMode) -> str | None:
    if reasoning in {
        ReasoningMode.MINIMAL,
        ReasoningMode.LOW,
        ReasoningMode.MEDIUM,
        ReasoningMode.HIGH,
    }:
        return reasoning.value
    if reasoning in {ReasoningMode.ENABLED, ReasoningMode.DYNAMIC}:
        return ReasoningMode.MEDIUM.value
    return "none"


def _resolve_reasoning_summary(effort: str | None) -> str:
    if effort in {None, "none"}:
        return "none"
    return "concise"


def _build_read_only_sandbox_policy(cwd: str) -> dict[str, Any]:
    return {
        "type": "readOnly",
        "networkAccess": False,
        "access": {
            "type": "restricted",
            "includePlatformDefaults": True,
            "readableRoots": [cwd],
        },
    }
