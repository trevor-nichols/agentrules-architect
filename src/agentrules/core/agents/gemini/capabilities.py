"""Gemini model capability helpers.

Centralize model-family metadata so Gemini preview models can be added by
declaring their behavior instead of expanding string checks in the architect.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from agentrules.core.agents.base import ReasoningMode

GeminiThinkingLevelName = Literal["minimal", "low", "medium", "high"]


@dataclass(frozen=True)
class GeminiCapabilityProfile:
    """Capability metadata for a Gemini model family."""

    family_prefix: str
    stable_name: str
    display_name: str
    uses_thinking_level: bool = False
    supports_structured_output_with_tools: bool = False
    supports_disabling_thinking: bool = True
    supported_thinking_levels: tuple[GeminiThinkingLevelName, ...] = ()

    def matches(self, model_name: str) -> bool:
        normalized = normalize_model_name(model_name)
        return normalized == self.family_prefix or normalized.startswith(f"{self.family_prefix}-")


_DEFAULT_PROFILE = GeminiCapabilityProfile(
    family_prefix="",
    stable_name="",
    display_name="Unknown Gemini family",
)

_CAPABILITY_PROFILES: tuple[GeminiCapabilityProfile, ...] = (
    GeminiCapabilityProfile(
        family_prefix="gemini-3.1-pro",
        stable_name="gemini-3.1-pro-preview",
        display_name="Gemini 3.1 Pro",
        uses_thinking_level=True,
        supports_structured_output_with_tools=True,
        supports_disabling_thinking=False,
        supported_thinking_levels=("low", "high"),
    ),
    GeminiCapabilityProfile(
        family_prefix="gemini-3-pro",
        stable_name="gemini-3-pro-preview",
        display_name="Gemini 3 Pro",
        uses_thinking_level=True,
        supports_structured_output_with_tools=True,
        supports_disabling_thinking=False,
        supported_thinking_levels=("low", "high"),
    ),
    GeminiCapabilityProfile(
        family_prefix="gemini-3.1-flash-lite",
        stable_name="gemini-3.1-flash-lite-preview",
        display_name="Gemini 3.1 Flash-Lite",
        uses_thinking_level=True,
        supports_structured_output_with_tools=True,
        supports_disabling_thinking=False,
        supported_thinking_levels=("minimal", "low", "medium", "high"),
    ),
    GeminiCapabilityProfile(
        family_prefix="gemini-3-flash",
        stable_name="gemini-3-flash-preview",
        display_name="Gemini 3 Flash",
        uses_thinking_level=True,
        supports_structured_output_with_tools=True,
        supports_disabling_thinking=False,
        supported_thinking_levels=("minimal", "low", "medium", "high"),
    ),
    GeminiCapabilityProfile(
        family_prefix="gemini-2.5-pro",
        stable_name="gemini-2.5-pro",
        display_name="Gemini 2.5 Pro",
        supports_disabling_thinking=False,
    ),
    GeminiCapabilityProfile(
        family_prefix="gemini-2.5-flash",
        stable_name="gemini-2.5-flash",
        display_name="Gemini 2.5 Flash",
        supports_disabling_thinking=True,
    ),
)


def normalize_model_name(model_name: str) -> str:
    return model_name.strip().lower()


def resolve_capability_profile(model_name: str) -> GeminiCapabilityProfile:
    """Return the capability profile for the supplied Gemini model."""

    for profile in _CAPABILITY_PROFILES:
        if profile.matches(model_name):
            return profile
    return _DEFAULT_PROFILE


def stable_model_name(model_name: str) -> str:
    """Return the stable family name used for reporting and fallback decisions."""

    profile = resolve_capability_profile(model_name)
    return profile.stable_name or model_name


def model_supports_thinking_level(model_name: str) -> bool:
    """Return True when the model uses thinking_level controls."""

    return resolve_capability_profile(model_name).uses_thinking_level


def model_supports_structured_output_with_tools(model_name: str) -> bool:
    """Return True when structured output and tools can be combined."""

    return resolve_capability_profile(model_name).supports_structured_output_with_tools


def model_supports_disabling_thinking(model_name: str) -> bool:
    """Return True when thinking can be disabled with a zero budget."""

    return resolve_capability_profile(model_name).supports_disabling_thinking


def resolve_thinking_level(
    *,
    model_name: str,
    reasoning_mode: ReasoningMode,
    thinking_level_enum: Any,
) -> Any | None:
    """Map a generic reasoning mode to the nearest supported Gemini thinking level."""

    profile = resolve_capability_profile(model_name)
    if not profile.supported_thinking_levels or thinking_level_enum is None:
        return None

    target_level = _choose_level(profile.supported_thinking_levels, reasoning_mode)
    if target_level is None:
        return None

    for candidate in _enum_lookup_order(target_level):
        if candidate not in profile.supported_thinking_levels:
            continue
        value = getattr(thinking_level_enum, candidate.upper(), None)
        if value is not None:
            return value
    return None


def _choose_level(
    supported_levels: tuple[GeminiThinkingLevelName, ...],
    reasoning_mode: ReasoningMode,
) -> GeminiThinkingLevelName | None:
    level_set = set(supported_levels)

    if reasoning_mode in {ReasoningMode.DISABLED, ReasoningMode.MINIMAL}:
        if "minimal" in level_set:
            return "minimal"
        if "low" in level_set:
            return "low"
        return supported_levels[0] if supported_levels else None

    if reasoning_mode == ReasoningMode.LOW:
        if "low" in level_set:
            return "low"
        if "minimal" in level_set:
            return "minimal"
        return supported_levels[0] if supported_levels else None

    if reasoning_mode == ReasoningMode.MEDIUM:
        if "medium" in level_set:
            return "medium"
        if "high" in level_set:
            return "high"
        if "low" in level_set:
            return "low"
        return supported_levels[0] if supported_levels else None

    if reasoning_mode in {ReasoningMode.ENABLED, ReasoningMode.DYNAMIC, ReasoningMode.HIGH}:
        if "high" in level_set:
            return "high"
        if "medium" in level_set:
            return "medium"
        return supported_levels[-1] if supported_levels else None

    return None


def _enum_lookup_order(target_level: GeminiThinkingLevelName) -> tuple[GeminiThinkingLevelName, ...]:
    if target_level == "minimal":
        return ("minimal", "low", "medium", "high")
    if target_level == "low":
        return ("low", "minimal", "medium", "high")
    if target_level == "medium":
        return ("medium", "high", "low", "minimal")
    return ("high", "medium", "low", "minimal")
