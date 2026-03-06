from __future__ import annotations

from agentrules.core.agents.base import ReasoningMode
from agentrules.core.agents.xai.config import resolve_model_defaults
from agentrules.core.agents.xai.request_builder import prepare_request


def test_prepare_request_sets_reasoning_effort_when_supported() -> None:
    defaults = resolve_model_defaults("grok-4-fast-reasoning")
    prepared = prepare_request(
        model_name="grok-4-fast-reasoning",
        content="Analyze",
        reasoning=ReasoningMode.HIGH,
        defaults=defaults,
        tools=None,
    )

    payload = prepared.payload
    assert payload["reasoning_effort"] == "high"


def test_prepare_request_sets_reasoning_effort_for_grok41_when_supported() -> None:
    defaults = resolve_model_defaults("grok-4-1-fast-reasoning")
    prepared = prepare_request(
        model_name="grok-4-1-fast-reasoning",
        content="Analyze",
        reasoning=ReasoningMode.HIGH,
        defaults=defaults,
        tools=None,
    )

    payload = prepared.payload
    assert payload["reasoning_effort"] == "high"


def test_prepare_request_prepends_system_message() -> None:
    defaults = resolve_model_defaults("grok-4-fast-reasoning")
    prepared = prepare_request(
        model_name="grok-4-fast-reasoning",
        content="Analyze architecture",
        system_prompt="You are a principal architect.",
        reasoning=ReasoningMode.DISABLED,
        defaults=defaults,
        tools=None,
    )

    payload = prepared.payload
    assert payload["messages"][0] == {"role": "system", "content": "You are a principal architect."}
    assert payload["messages"][1] == {"role": "user", "content": "Analyze architecture"}


def test_prepare_request_adds_response_format() -> None:
    defaults = resolve_model_defaults("grok-4-0709")
    prepared = prepare_request(
        model_name="grok-4-0709",
        content="Return JSON",
        reasoning=ReasoningMode.DISABLED,
        defaults=defaults,
        tools=None,
        response_format={"type": "json_object"},
    )

    payload = prepared.payload
    assert payload["response_format"] == {"type": "json_object"}


def test_resolve_defaults_for_grok41_fast_non_reasoning() -> None:
    defaults = resolve_model_defaults("grok-4-1-fast-non-reasoning")

    assert defaults.default_reasoning == ReasoningMode.DISABLED
    assert defaults.reasoning_effort_supported is False
