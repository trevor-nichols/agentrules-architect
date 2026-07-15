from agentrules.core.agents.anthropic.capabilities import (
    ThinkingPolicy,
    may_return_midstream_refusal,
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
    assert supports_structured_output_format("claude-opus-4-7")
    assert supports_structured_output_format("claude-opus-4-8")
    assert supports_structured_output_format("claude-sonnet-5")
    assert supports_structured_output_format("claude-fable-5")
    assert not supports_structured_output_format("claude-opus-4-1")


def test_supports_adaptive_thinking_matrix() -> None:
    assert supports_adaptive_thinking("claude-sonnet-4-6")
    assert supports_adaptive_thinking("claude-opus-4-6")
    assert supports_adaptive_thinking("claude-opus-4-7")
    assert supports_adaptive_thinking("claude-opus-4-8")
    assert supports_adaptive_thinking("claude-sonnet-5")
    assert supports_adaptive_thinking("claude-fable-5")
    assert not supports_adaptive_thinking("claude-sonnet-4-5")
    assert not supports_adaptive_thinking("claude-opus-4-5-20251101")


def test_supports_effort_matrix() -> None:
    assert supports_effort("claude-sonnet-4-6")
    assert supports_effort("claude-opus-4-5-20251101")
    assert supports_effort("claude-opus-4-6")
    assert supports_effort("claude-opus-4-7")
    assert supports_effort("claude-opus-4-8")
    assert supports_effort("claude-sonnet-5")
    assert supports_effort("claude-fable-5")
    assert not supports_effort("claude-sonnet-4-5")


def test_supported_effort_levels_reflect_family_capabilities() -> None:
    assert supported_effort_levels("claude-sonnet-4-6") == frozenset({"low", "medium", "high", "max"})
    assert supported_effort_levels("claude-opus-4-6") == frozenset({"low", "medium", "high", "max"})
    assert supported_effort_levels("claude-opus-4-7") == frozenset({"low", "medium", "high", "xhigh", "max"})
    assert supported_effort_levels("claude-opus-4-8") == frozenset({"low", "medium", "high", "xhigh", "max"})
    assert supported_effort_levels("claude-opus-4-5-20251101") == frozenset({"low", "medium", "high"})
    assert supported_effort_levels("claude-haiku-4-5") == frozenset()
    assert supported_effort_levels("claude-sonnet-5") == frozenset(
        {"low", "medium", "high", "xhigh", "max"}
    )
    assert supported_effort_levels("claude-fable-5") == frozenset(
        {"low", "medium", "high", "xhigh", "max"}
    )


def test_resolve_capability_profile_supports_snapshot_suffixes() -> None:
    profile = resolve_capability_profile("claude-sonnet-4-6-20260305")

    assert profile.display_name == "Claude Sonnet 4.6"
    assert profile.supports_adaptive_thinking


def test_claude_5_thinking_policies_are_explicit() -> None:
    assert (
        resolve_capability_profile("claude-sonnet-5").thinking_policy
        == ThinkingPolicy.ADAPTIVE_DEFAULT
    )
    assert (
        resolve_capability_profile("claude-fable-5").thinking_policy
        == ThinkingPolicy.ALWAYS_ADAPTIVE
    )


def test_only_fable_requires_midstream_refusal_buffering() -> None:
    assert may_return_midstream_refusal("claude-fable-5")
    assert may_return_midstream_refusal("claude-fable-5-20260609")
    assert not may_return_midstream_refusal("claude-sonnet-5")
    assert not may_return_midstream_refusal("claude-opus-4-8")
