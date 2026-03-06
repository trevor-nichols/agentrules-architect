from __future__ import annotations

from types import SimpleNamespace

from agentrules.core.agents.base import ReasoningMode
from agentrules.core.agents.gemini.capabilities import (
    model_supports_structured_output_with_tools,
    resolve_capability_profile,
    resolve_thinking_level,
    stable_model_name,
)

_THINKING_LEVELS = SimpleNamespace(
    MINIMAL="minimal",
    LOW="low",
    MEDIUM="medium",
    HIGH="high",
)


def test_resolve_capability_profile_for_gemini31_pro() -> None:
    profile = resolve_capability_profile("gemini-3.1-pro-preview")

    assert profile.display_name == "Gemini 3.1 Pro"
    assert profile.supported_thinking_levels == ("low", "high")


def test_flash_family_maps_disabled_to_minimal_when_supported() -> None:
    level = resolve_thinking_level(
        model_name="gemini-3.1-flash-lite-preview",
        reasoning_mode=ReasoningMode.DISABLED,
        thinking_level_enum=_THINKING_LEVELS,
    )

    assert level == "minimal"


def test_flash_family_maps_medium_to_medium() -> None:
    level = resolve_thinking_level(
        model_name="gemini-3-flash-preview",
        reasoning_mode=ReasoningMode.MEDIUM,
        thinking_level_enum=_THINKING_LEVELS,
    )

    assert level == "medium"


def test_pro_family_maps_medium_to_high() -> None:
    level = resolve_thinking_level(
        model_name="gemini-3.1-pro-preview",
        reasoning_mode=ReasoningMode.MEDIUM,
        thinking_level_enum=_THINKING_LEVELS,
    )

    assert level == "high"


def test_stable_model_name_and_schema_tool_support_follow_family_profile() -> None:
    assert stable_model_name("gemini-3.1-flash-lite-preview") == "gemini-3.1-flash-lite-preview"
    assert model_supports_structured_output_with_tools("gemini-3.1-pro-preview")
    assert not model_supports_structured_output_with_tools("gemini-2.5-flash")
