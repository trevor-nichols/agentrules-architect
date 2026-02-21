from agentrules.core.agents.anthropic.capabilities import (
    supports_effort,
    supports_structured_output_format,
)


def test_supports_structured_output_format_matrix() -> None:
    assert supports_structured_output_format("claude-sonnet-4-5")
    assert supports_structured_output_format("claude-haiku-4-5")
    assert supports_structured_output_format("claude-opus-4-5-20251101")
    assert supports_structured_output_format("claude-opus-4-6")
    assert not supports_structured_output_format("claude-opus-4-1")


def test_supports_effort_stays_limited_to_opus_45_and_46() -> None:
    assert supports_effort("claude-opus-4-5-20251101")
    assert supports_effort("claude-opus-4-6")
    assert not supports_effort("claude-sonnet-4-5")
