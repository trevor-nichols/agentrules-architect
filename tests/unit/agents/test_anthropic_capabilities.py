from agentrules.core.agents.anthropic.capabilities import (
    resolve_capability_profile,
    supported_effort_levels,
    supports_adaptive_thinking,
    supports_effort,
    supports_structured_output_format,
)


def test_supports_structured_output_format_matrix() -> None:
    assert supports_structured_output_format("claude-sonnet-4-5")
    assert supports_structured_output_format("claude-sonnet-4-6")
    assert supports_structured_output_format("claude-haiku-4-5")
    assert supports_structured_output_format("claude-opus-4-5-20251101")
    assert supports_structured_output_format("claude-opus-4-6")
    assert not supports_structured_output_format("claude-opus-4-1")


def test_supports_adaptive_thinking_matrix() -> None:
    assert supports_adaptive_thinking("claude-sonnet-4-6")
    assert supports_adaptive_thinking("claude-opus-4-6")
    assert not supports_adaptive_thinking("claude-sonnet-4-5")
    assert not supports_adaptive_thinking("claude-opus-4-5-20251101")


def test_supports_effort_matrix() -> None:
    assert supports_effort("claude-sonnet-4-6")
    assert supports_effort("claude-opus-4-5-20251101")
    assert supports_effort("claude-opus-4-6")
    assert not supports_effort("claude-sonnet-4-5")


def test_supported_effort_levels_reflect_family_capabilities() -> None:
    assert supported_effort_levels("claude-sonnet-4-6") == frozenset({"low", "medium", "high"})
    assert supported_effort_levels("claude-opus-4-6") == frozenset({"low", "medium", "high", "max"})
    assert supported_effort_levels("claude-opus-4-5-20251101") == frozenset({"low", "medium", "high"})
    assert supported_effort_levels("claude-haiku-4-5") == frozenset()


def test_resolve_capability_profile_supports_snapshot_suffixes() -> None:
    profile = resolve_capability_profile("claude-sonnet-4-6-20260305")

    assert profile.display_name == "Claude Sonnet 4.6"
    assert profile.supports_adaptive_thinking
