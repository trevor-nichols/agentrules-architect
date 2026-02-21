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
