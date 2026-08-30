"""Anthropic Claude model capability helpers.

Centralize provider capability metadata so new Claude families can be added by
describing their supported features instead of scattering string checks across
the request builders.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import cast

from agentrules.core.agents.base import ReasoningMode
from agentrules.core.types.models import AnthropicEffort


class ThinkingPolicy(Enum):
    """Provider-native thinking behavior for a Claude model family."""

    LEGACY = "legacy"
    ADAPTIVE_OPT_IN = "adaptive_opt_in"
    ADAPTIVE_DEFAULT = "adaptive_default"
    ALWAYS_ADAPTIVE = "always_adaptive"


@dataclass(frozen=True)
class CapabilityProfile:
    """Capability metadata for a Claude model family."""

    family_prefix: str
    display_name: str
    supports_structured_output_format: bool = False
    supports_adaptive_thinking: bool = False
    supports_manual_thinking: bool = True
    supported_effort_levels: frozenset[AnthropicEffort] = frozenset()
    supported_effort_levels_with_thinking_disabled: frozenset[AnthropicEffort] | None = None
    thinking_policy: ThinkingPolicy = ThinkingPolicy.LEGACY
    may_return_midstream_refusal: bool = False

    def matches(self, model_name: str) -> bool:
        normalized = normalize_model_name(model_name)
        return normalized == self.family_prefix or normalized.startswith(f"{self.family_prefix}-")


_DEFAULT_PROFILE = CapabilityProfile(
    family_prefix="",
    display_name="Unknown Claude family",
)

_SUPPORTED_EFFORT_LEVELS: frozenset[AnthropicEffort] = frozenset(
    {"low", "medium", "high", "xhigh", "max"}
)

_CAPABILITY_PROFILES: tuple[CapabilityProfile, ...] = (
    CapabilityProfile(
        family_prefix="claude-fable-5",
        display_name="Claude Fable 5",
        supports_structured_output_format=True,
        supports_adaptive_thinking=True,
        supports_manual_thinking=False,
        supported_effort_levels=frozenset({"low", "medium", "high", "xhigh", "max"}),
        thinking_policy=ThinkingPolicy.ALWAYS_ADAPTIVE,
        may_return_midstream_refusal=True,
    ),
    CapabilityProfile(
        family_prefix="claude-sonnet-5",
        display_name="Claude Sonnet 5",
        supports_structured_output_format=True,
        supports_adaptive_thinking=True,
        supports_manual_thinking=False,
        supported_effort_levels=frozenset({"low", "medium", "high", "xhigh", "max"}),
        thinking_policy=ThinkingPolicy.ADAPTIVE_DEFAULT,
    ),
    CapabilityProfile(
        family_prefix="claude-sonnet-4-6",
        display_name="Claude Sonnet 4.6",
        supports_structured_output_format=True,
        supports_adaptive_thinking=True,
        supported_effort_levels=frozenset({"low", "medium", "high", "max"}),
    ),
    CapabilityProfile(
        family_prefix="claude-sonnet-4-5",
        display_name="Claude Sonnet 4.5",
        supports_structured_output_format=True,
    ),
    CapabilityProfile(
        family_prefix="claude-haiku-4-5",
        display_name="Claude Haiku 4.5",
        supports_structured_output_format=True,
    ),
    CapabilityProfile(
        family_prefix="claude-opus-5",
        display_name="Claude Opus 5",
        supports_structured_output_format=True,
        supports_adaptive_thinking=True,
        supports_manual_thinking=False,
        supported_effort_levels=frozenset({"low", "medium", "high", "xhigh", "max"}),
        supported_effort_levels_with_thinking_disabled=frozenset({"low", "medium", "high"}),
        thinking_policy=ThinkingPolicy.ADAPTIVE_DEFAULT,
        may_return_midstream_refusal=True,
    ),
    CapabilityProfile(
        family_prefix="claude-opus-4-8",
        display_name="Claude Opus 4.8",
        supports_structured_output_format=True,
        supports_adaptive_thinking=True,
        supports_manual_thinking=False,
        supported_effort_levels=frozenset({"low", "medium", "high", "xhigh", "max"}),
        thinking_policy=ThinkingPolicy.ADAPTIVE_OPT_IN,
    ),
    CapabilityProfile(
        family_prefix="claude-opus-4-7",
        display_name="Claude Opus 4.7",
        supports_structured_output_format=True,
        supports_adaptive_thinking=True,
        supports_manual_thinking=False,
        supported_effort_levels=frozenset({"low", "medium", "high", "xhigh", "max"}),
        thinking_policy=ThinkingPolicy.ADAPTIVE_OPT_IN,
    ),
    CapabilityProfile(
        family_prefix="claude-opus-4-6",
        display_name="Claude Opus 4.6",
        supports_structured_output_format=True,
        supports_adaptive_thinking=True,
        supported_effort_levels=frozenset({"low", "medium", "high", "max"}),
    ),
    CapabilityProfile(
        family_prefix="claude-opus-4-5",
        display_name="Claude Opus 4.5",
        supports_structured_output_format=True,
        supported_effort_levels=frozenset({"low", "medium", "high"}),
    ),
)


def normalize_model_name(model_name: str) -> str:
    return model_name.strip().lower()


def resolve_capability_profile(model_name: str) -> CapabilityProfile:
    """Return the capability profile for the supplied Claude model family."""

    for profile in _CAPABILITY_PROFILES:
        if profile.matches(model_name):
            return profile
    return _DEFAULT_PROFILE


def supports_adaptive_thinking(model_name: str) -> bool:
    """Return True when the model supports thinking.type='adaptive'."""

    return resolve_capability_profile(model_name).supports_adaptive_thinking


def supports_manual_thinking(model_name: str) -> bool:
    """Return True when the model accepts thinking.type='enabled' with budget_tokens."""

    return resolve_capability_profile(model_name).supports_manual_thinking


def thinking_policy(model_name: str) -> ThinkingPolicy:
    """Return the model family's explicit thinking policy."""

    return resolve_capability_profile(model_name).thinking_policy


def supported_effort_levels(model_name: str) -> frozenset[AnthropicEffort]:
    """Return the supported output_config.effort levels for the model."""

    return resolve_capability_profile(model_name).supported_effort_levels


def effort_from_reasoning_mode(reasoning: ReasoningMode) -> AnthropicEffort | None:
    """Translate shared reasoning-effort modes to Anthropic effort values."""

    if reasoning in {
        ReasoningMode.LOW,
        ReasoningMode.MEDIUM,
        ReasoningMode.HIGH,
        ReasoningMode.XHIGH,
        ReasoningMode.MAX,
    }:
        return cast(AnthropicEffort, reasoning.value)
    return None


def resolve_effort(
    *,
    model_name: str,
    reasoning: ReasoningMode,
    effort: AnthropicEffort | str | None,
) -> AnthropicEffort | None:
    """Resolve and validate the request's provider-native effort value."""

    if effort is None:
        requested_effort = effort_from_reasoning_mode(reasoning)
        if requested_effort is None and reasoning not in {
            ReasoningMode.DISABLED,
            ReasoningMode.ENABLED,
            ReasoningMode.DYNAMIC,
        }:
            raise ValueError(
                f"Reasoning mode '{reasoning.value}' is not supported for Anthropic models."
            )
    else:
        if not isinstance(effort, str):
            raise ValueError(f"Invalid effort value type: {type(effort)!r}")

        normalized_effort = effort.strip().lower()
        if normalized_effort not in _SUPPORTED_EFFORT_LEVELS:
            supported = ", ".join(sorted(_SUPPORTED_EFFORT_LEVELS))
            raise ValueError(
                f"Invalid effort value '{effort}'. Supported values: {supported}."
            )
        requested_effort = cast(AnthropicEffort, normalized_effort)

    if requested_effort is None:
        return None

    allowed_effort_levels = supported_effort_levels(model_name)
    if not allowed_effort_levels:
        raise ValueError(
            "Effort is only supported for "
            f"{describe_profiles_with_effort()}; model '{model_name}' does not support "
            "output_config.effort."
        )
    if requested_effort not in allowed_effort_levels:
        supported = ", ".join(sorted(allowed_effort_levels))
        raise ValueError(
            f"Effort '{requested_effort}' is not supported for model '{model_name}'. "
            f"Supported values for this model: {supported}."
        )
    return requested_effort


def validate_thinking_effort_compatibility(
    *,
    model_name: str,
    thinking_type: str | None,
    effort: AnthropicEffort | str | None,
) -> None:
    """Reject provider-invalid combinations of thinking policy and effort."""

    if thinking_type != "disabled" or effort is None:
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


def supports_effort(model_name: str) -> bool:
    """Return True when the model supports output_config.effort."""

    return bool(supported_effort_levels(model_name))


def supports_max_effort(model_name: str) -> bool:
    """Return True when effort='max' is allowed."""

    return "max" in supported_effort_levels(model_name)


def supports_structured_output_format(model_name: str) -> bool:
    """Return True when the model supports output_config.format JSON schemas."""

    return resolve_capability_profile(model_name).supports_structured_output_format


def may_return_midstream_refusal(model_name: str) -> bool:
    """Return True when streamed output must be held until refusal status is known."""

    return resolve_capability_profile(model_name).may_return_midstream_refusal


def describe_profiles_with_adaptive_thinking() -> str:
    """Return a human-readable list of model families that support adaptive thinking."""

    return _describe_profiles(
        profile for profile in _CAPABILITY_PROFILES if profile.supports_adaptive_thinking
    )


def describe_profiles_with_effort() -> str:
    """Return a human-readable list of model families that support effort selection."""

    return _describe_profiles(
        profile for profile in _CAPABILITY_PROFILES if profile.supported_effort_levels
    )


def _describe_profiles(profiles: Iterable[CapabilityProfile]) -> str:
    labels = [profile.display_name for profile in profiles]
    if not labels:
        return "no Claude families"
    if len(labels) == 1:
        return labels[0]
    return ", ".join(labels[:-1]) + f", and {labels[-1]}"
