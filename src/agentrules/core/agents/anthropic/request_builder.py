"""Helpers for constructing Anthropic Messages API payloads."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agentrules.core.agents.base import ReasoningMode
from agentrules.core.types.models import AnthropicEffort

from .capabilities import (
    ThinkingPolicy,
    describe_profiles_with_adaptive_thinking,
    resolve_capability_profile,
    resolve_effort,
    supports_adaptive_thinking,
    supports_manual_thinking,
    supports_structured_output_format,
)

DEFAULT_NONSTREAMING_MAX_TOKENS = 20_000
EXTENDED_EFFORT_MAX_TOKENS = 64_000
DEFAULT_THINKING_BUDGET = 16_000
_EXTENDED_EFFORT_LEVELS: set[str] = {"xhigh", "max"}


@dataclass(frozen=True)
class PreparedRequest:
    """Container for a ready-to-dispatch Anthropic request."""

    payload: dict[str, Any]


def prepare_request(
    *,
    model_name: str,
    prompt: str,
    reasoning: ReasoningMode,
    max_tokens: int | None = None,
    tools: list[Any] | None,
    effort: AnthropicEffort | str | None = None,
    output_format: dict[str, Any] | None = None,
    system_prompt: str | None = None,
) -> PreparedRequest:
    resolved_effort = resolve_effort(
        model_name=model_name,
        reasoning=reasoning,
        effort=effort,
    )
    output_config = _build_output_config(
        model_name=model_name,
        effort=resolved_effort,
        output_format=output_format,
    )
    normalized_effort = output_config.get("effort") if output_config is not None else None
    payload: dict[str, Any] = {
        "model": model_name,
        "max_tokens": _resolve_max_tokens(max_tokens, normalized_effort),
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
    _validate_thinking_effort_compatibility(
        model_name=model_name,
        thinking=thinking,
        effort=normalized_effort,
    )
    if thinking is not None:
        payload["thinking"] = thinking

    if tools:
        payload["tools"] = tools

    if output_config is not None:
        payload["output_config"] = output_config

    return PreparedRequest(payload=payload)


def _resolve_max_tokens(max_tokens: int | None, effort: str | None) -> int:
    if max_tokens is not None:
        return max_tokens
    if effort in _EXTENDED_EFFORT_LEVELS:
        return EXTENDED_EFFORT_MAX_TOKENS
    return DEFAULT_NONSTREAMING_MAX_TOKENS


def _validate_thinking_effort_compatibility(
    *,
    model_name: str,
    thinking: dict[str, Any] | None,
    effort: str | None,
) -> None:
    if thinking is None or thinking.get("type") != "disabled" or effort is None:
        return

    allowed_effort_levels = (
        resolve_capability_profile(model_name).supported_effort_levels_with_thinking_disabled
    )
    if allowed_effort_levels is None or effort in allowed_effort_levels:
        return

    supported = ", ".join(sorted(allowed_effort_levels))
    raise ValueError(
        f"Effort '{effort}' is not supported for model '{model_name}' when thinking is "
        f"disabled. Supported values for disabled thinking: {supported}. Enable adaptive "
        "thinking or select a supported effort level."
    )


def _build_thinking_payload(*, model_name: str, reasoning: ReasoningMode) -> dict[str, Any] | None:
    profile = resolve_capability_profile(model_name)

    if profile.thinking_policy == ThinkingPolicy.ALWAYS_ADAPTIVE:
        if reasoning == ReasoningMode.DISABLED:
            raise ValueError(
                f"Model '{model_name}' always uses adaptive thinking and does not support "
                "ReasoningMode.DISABLED. Select a valid effort level instead."
            )
        # Adaptive thinking is automatic for this policy. Omitting the field is
        # the provider-recommended request shape.
        return None

    if profile.thinking_policy == ThinkingPolicy.ADAPTIVE_DEFAULT:
        if reasoning == ReasoningMode.DISABLED:
            return {"type": "disabled"}
        if reasoning in {ReasoningMode.ENABLED, ReasoningMode.DYNAMIC}:
            return {"type": "adaptive"}
        return None

    if reasoning == ReasoningMode.ENABLED:
        if supports_manual_thinking(model_name):
            return {"type": "enabled", "budget_tokens": DEFAULT_THINKING_BUDGET}
        if supports_adaptive_thinking(model_name):
            return {"type": "adaptive"}
        raise ValueError(
            f"Model '{model_name}' does not support enabled or adaptive thinking."
        )

    if reasoning == ReasoningMode.DYNAMIC:
        if supports_adaptive_thinking(model_name):
            return {"type": "adaptive"}
        raise ValueError(
            "Adaptive thinking (ReasoningMode.DYNAMIC) is only supported for "
            f"{describe_profiles_with_adaptive_thinking()}; model '{model_name}' does not "
            "support it. Use ReasoningMode.ENABLED for fixed-budget thinking on older Claude "
            "models."
        )

    if reasoning == ReasoningMode.DISABLED:
        return None

    return None


def _build_output_config(
    *,
    model_name: str,
    effort: AnthropicEffort | None,
    output_format: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if effort is None and output_format is None:
        return None

    output_config: dict[str, Any] = {}

    if effort is not None:
        output_config["effort"] = effort

    if output_format is not None and supports_structured_output_format(model_name):
        output_config["format"] = output_format

    if not output_config:
        return None
    return output_config
