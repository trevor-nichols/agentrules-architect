"""Helpers for constructing Anthropic Messages API payloads."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agentrules.core.agents.base import ReasoningMode
from agentrules.core.types.models import AnthropicEffort

from .capabilities import (
    supports_adaptive_thinking,
    supports_effort,
    supports_max_effort,
    supports_structured_output_format,
)

DEFAULT_MAX_TOKENS = 20_000
DEFAULT_THINKING_BUDGET = 16_000
_SUPPORTED_EFFORT_LEVELS: set[str] = {"low", "medium", "high", "max"}


@dataclass(frozen=True)
class PreparedRequest:
    """Container for a ready-to-dispatch Anthropic request."""

    payload: dict[str, Any]


def prepare_request(
    *,
    model_name: str,
    prompt: str,
    reasoning: ReasoningMode,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    tools: list[Any] | None,
    effort: AnthropicEffort | str | None = None,
    output_format: dict[str, Any] | None = None,
    system_prompt: str | None = None,
) -> PreparedRequest:
    payload: dict[str, Any] = {
        "model": model_name,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
    }
    if system_prompt:
        payload["system"] = system_prompt

    thinking = _build_thinking_payload(model_name=model_name, reasoning=reasoning)
    if thinking is not None:
        payload["thinking"] = thinking

    if tools:
        payload["tools"] = tools

    output_config = _build_output_config(
        model_name=model_name,
        effort=effort,
        output_format=output_format,
    )
    if output_config is not None:
        payload["output_config"] = output_config

    return PreparedRequest(payload=payload)


def _build_thinking_payload(*, model_name: str, reasoning: ReasoningMode) -> dict[str, Any] | None:
    if reasoning == ReasoningMode.ENABLED:
        return {"type": "enabled", "budget_tokens": DEFAULT_THINKING_BUDGET}

    if reasoning == ReasoningMode.DYNAMIC:
        # Claude Opus 4.6 introduced "adaptive" thinking mode. Other models do not
        # support it; fail fast so callers get an actionable error instead of a
        # confusing API 400.
        if supports_adaptive_thinking(model_name):
            return {"type": "adaptive"}
        raise ValueError(
            "Adaptive thinking (ReasoningMode.DYNAMIC) is only supported for Claude Opus 4.6 "
            "(model 'claude-opus-4-6'). Use ReasoningMode.ENABLED for fixed-budget thinking "
            "on other Claude models."
        )

    if reasoning == ReasoningMode.DISABLED:
        return None

    return None


def _build_output_config(
    *,
    model_name: str,
    effort: AnthropicEffort | str | None,
    output_format: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if effort is None and output_format is None:
        return None

    output_config: dict[str, Any] = {}

    if effort is not None:
        if not supports_effort(model_name):
            raise ValueError(
                f"Effort is only supported for Claude Opus 4.5/4.6; model '{model_name}' "
                "does not support output_config.effort."
            )

        if not isinstance(effort, str):
            raise ValueError(f"Invalid effort value type: {type(effort)!r}")

        normalized = effort.strip().lower()
        if normalized not in _SUPPORTED_EFFORT_LEVELS:
            supported = ", ".join(sorted(_SUPPORTED_EFFORT_LEVELS))
            raise ValueError(f"Invalid effort value '{effort}'. Supported values: {supported}.")

        if normalized == "max" and not supports_max_effort(model_name):
            raise ValueError(
                "Effort 'max' is only supported for Claude Opus 4.6; "
                f"model '{model_name}' does not support effort='max'."
            )

        output_config["effort"] = normalized

    if output_format is not None and supports_structured_output_format(model_name):
        output_config["format"] = output_format

    if not output_config:
        return None
    return output_config
