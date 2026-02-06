from agentrules.core.agents.anthropic.request_builder import (
    DEFAULT_THINKING_BUDGET,
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


def test_prepare_request_dynamic_reasoning_passthrough() -> None:
    prepared: PreparedRequest = prepare_request(
        model_name="claude-opus-4-6",
        prompt="hello",
        reasoning=ReasoningMode.DYNAMIC,
        tools=None,
    )

    assert prepared.payload["thinking"] == {"type": "adaptive"}


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


def test_prepare_request_effort_max_unsupported_model_raises() -> None:
    try:
        prepare_request(
            model_name="claude-opus-4-5-20251101",
            prompt="hello",
            reasoning=ReasoningMode.DISABLED,
            tools=None,
            effort="max",
        )
    except ValueError as exc:
        assert "Effort 'max'" in str(exc)
    else:
        raise AssertionError("Expected ValueError for effort=max on unsupported model")
