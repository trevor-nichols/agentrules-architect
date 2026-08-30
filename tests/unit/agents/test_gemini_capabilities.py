from __future__ import annotations

from types import SimpleNamespace

import pytest

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
        model_name="gemini-3.1-flash-lite",
        reasoning_mode=ReasoningMode.DISABLED,
        thinking_level_enum=_THINKING_LEVELS,
    )

    assert level == "minimal"


def test_gemini35_flash_maps_medium_to_medium() -> None:
    level = resolve_thinking_level(
        model_name="gemini-3.5-flash",
        reasoning_mode=ReasoningMode.MEDIUM,
        thinking_level_enum=_THINKING_LEVELS,
    )

    assert level == "medium"


@pytest.mark.parametrize(
    ("model_name", "expected_name", "expected_levels"),
    [
        ("gemini-3.7-flash", "Gemini 3.7 Flash", ("low", "medium", "high")),
        (
            "gemini-3.6-flash-20260815",
            "Gemini 3.6 Flash",
            ("minimal", "low", "medium", "high"),
        ),
        (
            "gemini-3.5-flash-lite-20260815",
            "Gemini 3.5 Flash-Lite",
            ("minimal", "low", "medium", "high"),
        ),
    ],
)
def test_current_flash_profiles_resolve_exact_and_snapshot_names(
    model_name: str,
    expected_name: str,
    expected_levels: tuple[str, ...],
) -> None:
    profile = resolve_capability_profile(model_name)

    assert profile.display_name == expected_name
    assert profile.supported_thinking_levels == expected_levels
    assert profile.requires_exact_thinking_level
    assert profile.supports_structured_output_with_tools


@pytest.mark.parametrize(
    ("model_name", "reasoning_mode", "expected_level"),
    [
        ("gemini-3.7-flash", ReasoningMode.LOW, "low"),
        ("gemini-3.7-flash", ReasoningMode.MEDIUM, "medium"),
        ("gemini-3.7-flash", ReasoningMode.HIGH, "high"),
        ("gemini-3.6-flash", ReasoningMode.MINIMAL, "minimal"),
        ("gemini-3.6-flash", ReasoningMode.LOW, "low"),
        ("gemini-3.6-flash", ReasoningMode.MEDIUM, "medium"),
        ("gemini-3.6-flash", ReasoningMode.HIGH, "high"),
        ("gemini-3.5-flash-lite", ReasoningMode.MINIMAL, "minimal"),
        ("gemini-3.5-flash-lite", ReasoningMode.LOW, "low"),
        ("gemini-3.5-flash-lite", ReasoningMode.MEDIUM, "medium"),
        ("gemini-3.5-flash-lite", ReasoningMode.HIGH, "high"),
    ],
)
def test_current_flash_profiles_preserve_exact_thinking_levels(
    model_name: str,
    reasoning_mode: ReasoningMode,
    expected_level: str,
) -> None:
    assert (
        resolve_thinking_level(
            model_name=model_name,
            reasoning_mode=reasoning_mode,
            thinking_level_enum=_THINKING_LEVELS,
        )
        == expected_level
    )


@pytest.mark.parametrize(
    "reasoning_mode",
    [
        ReasoningMode.DISABLED,
        ReasoningMode.MINIMAL,
        ReasoningMode.ENABLED,
        ReasoningMode.DYNAMIC,
        ReasoningMode.XHIGH,
        ReasoningMode.MAX,
    ],
)
def test_gemini37_rejects_unsupported_reasoning_modes(
    reasoning_mode: ReasoningMode,
) -> None:
    with pytest.raises(ValueError, match="gemini-3.7-flash"):
        resolve_thinking_level(
            model_name="gemini-3.7-flash",
            reasoning_mode=reasoning_mode,
            thinking_level_enum=_THINKING_LEVELS,
        )


def test_exact_profile_rejects_sdk_enum_without_required_level() -> None:
    with pytest.raises(ValueError, match="does not expose the required 'minimal'"):
        resolve_thinking_level(
            model_name="gemini-3.6-flash",
            reasoning_mode=ReasoningMode.MINIMAL,
            thinking_level_enum=SimpleNamespace(LOW="low", MEDIUM="medium", HIGH="high"),
        )


def test_pro_family_maps_medium_to_high() -> None:
    level = resolve_thinking_level(
        model_name="gemini-3.1-pro-preview",
        reasoning_mode=ReasoningMode.MEDIUM,
        thinking_level_enum=_THINKING_LEVELS,
    )

    assert level == "high"


def test_stable_model_name_and_schema_tool_support_follow_family_profile() -> None:
    assert stable_model_name("gemini-3.1-flash-lite-preview") == "gemini-3.1-flash-lite-preview"
    assert stable_model_name("gemini-3.1-flash-lite") == "gemini-3.1-flash-lite"
    assert model_supports_structured_output_with_tools("gemini-3.5-flash")
    assert not model_supports_structured_output_with_tools("gemini-2.5-flash")
