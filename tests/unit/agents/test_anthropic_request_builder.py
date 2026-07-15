import pytest

from agentrules.core.agents.anthropic.request_builder import (
    DEFAULT_THINKING_BUDGET,
    EXTENDED_EFFORT_MAX_TOKENS,
    PreparedRequest,
    prepare_request,
)
from agentrules.core.agents.base import ReasoningMode


def test_prepare_request_without_reasoning_skips_thinking() -> None:
    prepared: PreparedRequest = prepare_request(
        model_name="claude-sonnet-4-5",
        prompt="hello",
        reasoning=ReasoningMode.DISABLED,
        tools=None,
    )

    assert "thinking" not in prepared.payload
    assert prepared.payload["max_tokens"] == 20_000


def test_prepare_request_sets_top_level_system_prompt() -> None:
    prepared: PreparedRequest = prepare_request(
        model_name="claude-sonnet-4-5",
        prompt="hello",
        system_prompt="You are a security auditor.",
        reasoning=ReasoningMode.DISABLED,
        tools=None,
    )

    assert prepared.payload["system"] == "You are a security auditor."


def test_prepare_request_with_reasoning_includes_budget() -> None:
    prepared: PreparedRequest = prepare_request(
        model_name="claude-sonnet-4-5",
        prompt="hello",
        reasoning=ReasoningMode.ENABLED,
        tools=None,
    )

    assert prepared.payload["thinking"] == {
        "type": "enabled",
        "budget_tokens": DEFAULT_THINKING_BUDGET,
    }


def test_prepare_request_enabled_reasoning_uses_adaptive_for_opus47() -> None:
    prepared: PreparedRequest = prepare_request(
        model_name="claude-opus-4-7",
        prompt="hello",
        reasoning=ReasoningMode.ENABLED,
        tools=None,
    )

    assert prepared.payload["thinking"] == {"type": "adaptive"}


def test_prepare_request_dynamic_reasoning_passthrough() -> None:
    prepared: PreparedRequest = prepare_request(
        model_name="claude-opus-4-6",
        prompt="hello",
        reasoning=ReasoningMode.DYNAMIC,
        tools=None,
    )

    assert prepared.payload["thinking"] == {"type": "adaptive"}


def test_prepare_request_dynamic_reasoning_passthrough_for_sonnet46() -> None:
    prepared: PreparedRequest = prepare_request(
        model_name="claude-sonnet-4-6",
        prompt="hello",
        reasoning=ReasoningMode.DYNAMIC,
        tools=None,
    )

    assert prepared.payload["thinking"] == {"type": "adaptive"}


def test_prepare_request_sonnet5_disabled_is_explicit() -> None:
    prepared = prepare_request(
        model_name="claude-sonnet-5",
        prompt="hello",
        reasoning=ReasoningMode.DISABLED,
        tools=None,
    )

    assert prepared.payload["thinking"] == {"type": "disabled"}


@pytest.mark.parametrize("reasoning", [ReasoningMode.ENABLED, ReasoningMode.DYNAMIC])
def test_prepare_request_sonnet5_thinking_uses_adaptive(reasoning: ReasoningMode) -> None:
    prepared = prepare_request(
        model_name="claude-sonnet-5",
        prompt="hello",
        reasoning=reasoning,
        tools=None,
    )

    assert prepared.payload["thinking"] == {"type": "adaptive"}
    assert "budget_tokens" not in prepared.payload["thinking"]


def test_prepare_request_fable5_uses_always_on_adaptive_default() -> None:
    prepared = prepare_request(
        model_name="claude-fable-5",
        prompt="hello",
        reasoning=ReasoningMode.DYNAMIC,
        tools=None,
        effort="high",
    )

    assert "thinking" not in prepared.payload
    assert prepared.payload["output_config"] == {"effort": "high"}


def test_prepare_request_fable5_rejects_disabled_thinking() -> None:
    with pytest.raises(ValueError, match="always uses adaptive thinking"):
        prepare_request(
            model_name="claude-fable-5",
            prompt="hello",
            reasoning=ReasoningMode.DISABLED,
            tools=None,
        )


@pytest.mark.parametrize("effort", ["low", "medium", "high", "xhigh", "max"])
@pytest.mark.parametrize("model_name", ["claude-sonnet-5", "claude-fable-5"])
def test_prepare_request_claude5_accepts_documented_efforts(
    model_name: str,
    effort: str,
) -> None:
    prepared = prepare_request(
        model_name=model_name,
        prompt="hello",
        reasoning=ReasoningMode.DYNAMIC,
        tools=None,
        effort=effort,
    )

    assert prepared.payload["output_config"] == {"effort": effort}


@pytest.mark.parametrize("model_name", ["claude-sonnet-5", "claude-fable-5"])
@pytest.mark.parametrize("effort", ["xhigh", "max"])
def test_prepare_request_claude5_uses_extended_output_budget(
    model_name: str,
    effort: str,
) -> None:
    prepared = prepare_request(
        model_name=model_name,
        prompt="hello",
        reasoning=ReasoningMode.DYNAMIC,
        tools=None,
        effort=effort,
    )

    assert prepared.payload["max_tokens"] == EXTENDED_EFFORT_MAX_TOKENS


def test_prepare_request_preserves_explicit_output_budget() -> None:
    prepared = prepare_request(
        model_name="claude-sonnet-5",
        prompt="hello",
        reasoning=ReasoningMode.DYNAMIC,
        max_tokens=8_192,
        tools=None,
        effort="max",
    )

    assert prepared.payload["max_tokens"] == 8_192


@pytest.mark.parametrize("model_name", ["claude-sonnet-5", "claude-fable-5"])
def test_prepare_request_claude5_includes_structured_output(model_name: str) -> None:
    output_format = {"type": "json_schema", "schema": {"type": "object"}}
    prepared = prepare_request(
        model_name=model_name,
        prompt="hello",
        reasoning=ReasoningMode.DYNAMIC,
        tools=None,
        effort="medium",
        output_format=output_format,
    )

    assert prepared.payload["output_config"] == {
        "effort": "medium",
        "format": output_format,
    }


def test_prepare_request_dynamic_reasoning_unsupported_model_raises() -> None:
    try:
        prepare_request(
            model_name="claude-sonnet-4-5",
            prompt="hello",
            reasoning=ReasoningMode.DYNAMIC,
            tools=None,
        )
    except ValueError as exc:
        assert "Adaptive thinking" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsupported adaptive thinking model")


def test_prepare_request_effort_adds_output_config() -> None:
    prepared: PreparedRequest = prepare_request(
        model_name="claude-opus-4-6",
        prompt="hello",
        reasoning=ReasoningMode.DYNAMIC,
        tools=None,
        effort="medium",
    )

    assert prepared.payload["output_config"] == {"effort": "medium"}


def test_prepare_request_effort_accepts_xhigh_for_opus47() -> None:
    prepared: PreparedRequest = prepare_request(
        model_name="claude-opus-4-7",
        prompt="hello",
        reasoning=ReasoningMode.DYNAMIC,
        tools=None,
        effort="xhigh",
    )

    assert prepared.payload["output_config"] == {"effort": "xhigh"}


def test_prepare_request_effort_adds_output_config_for_sonnet46() -> None:
    prepared: PreparedRequest = prepare_request(
        model_name="claude-sonnet-4-6",
        prompt="hello",
        reasoning=ReasoningMode.DYNAMIC,
        tools=None,
        effort="medium",
    )

    assert prepared.payload["output_config"] == {"effort": "medium"}


def test_prepare_request_effort_accepts_max_for_sonnet46() -> None:
    prepared: PreparedRequest = prepare_request(
        model_name="claude-sonnet-4-6",
        prompt="hello",
        reasoning=ReasoningMode.DYNAMIC,
        tools=None,
        effort="max",
    )

    assert prepared.payload["output_config"] == {"effort": "max"}


def test_prepare_request_effort_unsupported_model_raises() -> None:
    try:
        prepare_request(
            model_name="claude-sonnet-4-5",
            prompt="hello",
            reasoning=ReasoningMode.DISABLED,
            tools=None,
            effort="low",
        )
    except ValueError as exc:
        assert "Effort is only supported" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsupported effort model")


def test_prepare_request_effort_max_supported_for_opus_46() -> None:
    prepared: PreparedRequest = prepare_request(
        model_name="claude-opus-4-6",
        prompt="hello",
        reasoning=ReasoningMode.DYNAMIC,
        tools=None,
        effort="max",
    )

    assert prepared.payload["output_config"] == {"effort": "max"}


def test_prepare_request_effort_xhigh_unsupported_for_opus46_raises() -> None:
    try:
        prepare_request(
            model_name="claude-opus-4-6",
            prompt="hello",
            reasoning=ReasoningMode.DYNAMIC,
            tools=None,
            effort="xhigh",
        )
    except ValueError as exc:
        assert "Supported values for this model: high, low, max, medium" in str(exc)
    else:
        raise AssertionError("Expected ValueError for effort=xhigh on unsupported model")


def test_prepare_request_effort_xhigh_unsupported_for_sonnet46_raises() -> None:
    try:
        prepare_request(
            model_name="claude-sonnet-4-6",
            prompt="hello",
            reasoning=ReasoningMode.DYNAMIC,
            tools=None,
            effort="xhigh",
        )
    except ValueError as exc:
        assert "Supported values for this model: high, low, max, medium" in str(exc)
    else:
        raise AssertionError("Expected ValueError for effort=xhigh on unsupported model")


def test_prepare_request_effort_max_unsupported_for_opus45_raises() -> None:
    try:
        prepare_request(
            model_name="claude-opus-4-5-20251101",
            prompt="hello",
            reasoning=ReasoningMode.DISABLED,
            tools=None,
            effort="max",
        )
    except ValueError as exc:
        assert "Supported values for this model: high, low, medium" in str(exc)
    else:
        raise AssertionError("Expected ValueError for effort=max on unsupported model")


def test_prepare_request_merges_effort_and_output_format() -> None:
    output_format = {"type": "json_schema", "schema": {"type": "object"}}
    prepared: PreparedRequest = prepare_request(
        model_name="claude-opus-4-6",
        prompt="hello",
        reasoning=ReasoningMode.DISABLED,
        tools=None,
        effort="low",
        output_format=output_format,
    )

    assert prepared.payload["output_config"] == {
        "effort": "low",
        "format": output_format,
    }


def test_prepare_request_includes_output_format_for_supported_model() -> None:
    output_format = {"type": "json_schema", "schema": {"type": "object"}}
    prepared: PreparedRequest = prepare_request(
        model_name="claude-sonnet-4-5",
        prompt="hello",
        reasoning=ReasoningMode.DISABLED,
        tools=None,
        output_format=output_format,
    )

    assert prepared.payload["output_config"] == {"format": output_format}


def test_prepare_request_skips_output_format_for_unsupported_model() -> None:
    output_format = {"type": "json_schema", "schema": {"type": "object"}}
    prepared: PreparedRequest = prepare_request(
        model_name="claude-opus-4-1",
        prompt="hello",
        reasoning=ReasoningMode.DISABLED,
        tools=None,
        output_format=output_format,
    )

    assert "output_config" not in prepared.payload
