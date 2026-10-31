from __future__ import annotations

from types import SimpleNamespace

import pytest

from agentrules.core.agents.base import ReasoningMode
from agentrules.core.agents.xai.architect import XaiArchitect
from agentrules.core.agents.xai.config import resolve_model_defaults
from agentrules.core.agents.xai.request_builder import prepare_request


def test_prepare_request_sets_reasoning_effort_when_supported() -> None:
    defaults = resolve_model_defaults("grok-4.3")
    prepared = prepare_request(
        model_name="grok-4.3",
        content="Analyze",
        reasoning=ReasoningMode.HIGH,
        defaults=defaults,
        tools=None,
    )

    payload = prepared.payload
    assert payload["reasoning_effort"] == "high"


def test_prepare_request_normalizes_max_to_high_for_existing_xai_models() -> None:
    defaults = resolve_model_defaults("grok-4.3")
    prepared = prepare_request(
        model_name="grok-4.3",
        content="Analyze",
        reasoning=ReasoningMode.MAX,
        defaults=defaults,
        tools=None,
    )

    assert prepared.payload["reasoning_effort"] == "high"


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


def test_prepare_request_sets_reasoning_effort_for_grok_0709_alias() -> None:
    defaults = resolve_model_defaults("grok-4-0709")
    prepared = prepare_request(
        model_name="grok-4-0709",
        content="Analyze",
        reasoning=ReasoningMode.MEDIUM,
        defaults=defaults,
        tools=None,
    )

    payload = prepared.payload
    assert payload["reasoning_effort"] == "medium"


def test_prepare_request_sets_reasoning_effort_none_when_disabled_and_supported() -> None:
    defaults = resolve_model_defaults("grok-4.3")
    prepared = prepare_request(
        model_name="grok-4.3",
        content="Analyze",
        reasoning=ReasoningMode.DISABLED,
        defaults=defaults,
        tools=None,
    )

    payload = prepared.payload
    assert payload["reasoning_effort"] == "none"


def test_prepare_request_sets_reasoning_effort_none_for_legacy_non_reasoning_alias() -> None:
    defaults = resolve_model_defaults("grok-4-fast-non-reasoning")
    prepared = prepare_request(
        model_name="grok-4-fast-non-reasoning",
        content="Analyze",
        reasoning=ReasoningMode.DISABLED,
        defaults=defaults,
        tools=None,
    )

    payload = prepared.payload
    assert payload["reasoning_effort"] == "none"


def test_prepare_request_prepends_system_message() -> None:
    defaults = resolve_model_defaults("grok-4.3")
    prepared = prepare_request(
        model_name="grok-4.3",
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
    defaults = resolve_model_defaults("grok-4.3")
    prepared = prepare_request(
        model_name="grok-4.3",
        content="Return JSON",
        reasoning=ReasoningMode.DISABLED,
        defaults=defaults,
        tools=None,
        response_format={"type": "json_object"},
    )

    payload = prepared.payload
    assert payload["response_format"] == {"type": "json_object"}


def test_prepare_request_omits_reasoning_effort_for_grok_build() -> None:
    defaults = resolve_model_defaults("grok-build-0.1")
    prepared = prepare_request(
        model_name="grok-build-0.1",
        content="Return JSON",
        reasoning=ReasoningMode.HIGH,
        defaults=defaults,
        tools=None,
    )

    payload = prepared.payload
    assert "reasoning_effort" not in payload


def test_prepare_request_omits_reasoning_effort_for_grok_code_fast_alias() -> None:
    defaults = resolve_model_defaults("grok-code-fast-1")
    prepared = prepare_request(
        model_name="grok-code-fast-1",
        content="Return JSON",
        reasoning=ReasoningMode.HIGH,
        defaults=defaults,
        tools=None,
    )

    payload = prepared.payload
    assert "reasoning_effort" not in payload


def test_resolve_defaults_for_grok41_fast_non_reasoning() -> None:
    defaults = resolve_model_defaults("grok-4-1-fast-non-reasoning")

    assert defaults.default_reasoning == ReasoningMode.DISABLED
    assert defaults.accepted_reasoning_efforts == frozenset({"none", "minimal", "low", "medium", "high"})


def test_resolve_defaults_for_grok43() -> None:
    defaults = resolve_model_defaults("grok-4.3")

    assert defaults.default_reasoning == ReasoningMode.LOW
    assert defaults.accepted_reasoning_efforts == frozenset({"none", "minimal", "low", "medium", "high"})


def test_resolve_defaults_for_grok_0709_alias() -> None:
    defaults = resolve_model_defaults("grok-4-0709")

    assert defaults.default_reasoning == ReasoningMode.MEDIUM
    assert defaults.accepted_reasoning_efforts == frozenset({"none", "minimal", "low", "medium", "high"})


def test_resolve_defaults_for_grok_build() -> None:
    defaults = resolve_model_defaults("grok-build-0.1")

    assert defaults.default_reasoning == ReasoningMode.ENABLED
    assert defaults.accepted_reasoning_efforts == frozenset()


def test_resolve_defaults_for_grok_code_fast_alias() -> None:
    defaults = resolve_model_defaults("grok-code-fast-1")

    assert defaults.default_reasoning == ReasoningMode.ENABLED
    assert defaults.accepted_reasoning_efforts == frozenset()


@pytest.mark.parametrize(
    ("reasoning", "expected_effort"),
    [
        (ReasoningMode.LOW, "low"),
        (ReasoningMode.MEDIUM, "medium"),
        (ReasoningMode.HIGH, "high"),
        (ReasoningMode.ENABLED, "high"),
        (ReasoningMode.DYNAMIC, "high"),
    ],
)
def test_prepare_request_maps_only_supported_grok45_efforts(
    reasoning: ReasoningMode,
    expected_effort: str,
) -> None:
    prepared = prepare_request(
        model_name="grok-4.5",
        content="Analyze",
        reasoning=reasoning,
        defaults=resolve_model_defaults("grok-4.5"),
        tools=None,
    )

    assert prepared.payload["reasoning_effort"] == expected_effort


def test_resolve_defaults_for_grok46() -> None:
    defaults = resolve_model_defaults("grok-4.6")

    assert defaults.default_reasoning == ReasoningMode.HIGH
    assert defaults.accepted_reasoning_efforts == frozenset({"low", "medium", "high", "xhigh"})
    assert not defaults.normalize_higher_efforts_to_high


@pytest.mark.parametrize(
    ("reasoning", "expected_effort"),
    [
        (ReasoningMode.LOW, "low"),
        (ReasoningMode.MEDIUM, "medium"),
        (ReasoningMode.HIGH, "high"),
        (ReasoningMode.XHIGH, "xhigh"),
        (ReasoningMode.ENABLED, "high"),
        (ReasoningMode.DYNAMIC, "high"),
    ],
)
def test_grok47_chat_request_preserves_effort_tools_and_structured_output(
    reasoning: ReasoningMode,
    expected_effort: str,
) -> None:
    tools = [{"type": "function", "function": {"name": "inspect", "parameters": {"type": "object"}}}]
    response_format = {
        "type": "json_schema",
        "json_schema": {"name": "result", "schema": {"type": "object"}},
    }
    prepared = prepare_request(
        model_name="grok-4.7",
        content="Analyze",
        reasoning=reasoning,
        defaults=resolve_model_defaults("grok-4.7"),
        tools=tools,
        response_format=response_format,
    )

    assert prepared.payload == {
        "model": "grok-4.7",
        "messages": [{"role": "user", "content": "Analyze"}],
        "tools": tools,
        "tool_choice": "auto",
        "reasoning_effort": expected_effort,
        "response_format": response_format,
    }


@pytest.mark.asyncio
async def test_grok47_architect_sends_tools_and_phase_structured_output() -> None:
    class FakeCompletions:
        def __init__(self) -> None:
            self.payload: dict[str, object] | None = None

        def create(self, **payload: object) -> SimpleNamespace:
            self.payload = payload
            message = SimpleNamespace(content='{"agents":[]}', tool_calls=None)
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    completions = FakeCompletions()
    architect = XaiArchitect(model_name="grok-4.7")
    architect.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    tools = [{"type": "function", "function": {"name": "inspect", "parameters": {"type": "object"}}}]

    result = await architect.analyze(
        {"formatted_prompt": "Choose agents", "_structured_output_phase": "phase2"},
        tools=tools,
    )

    assert result["findings"] == '{"agents":[]}'
    assert completions.payload is not None
    assert completions.payload["model"] == "grok-4.7"
    assert completions.payload["reasoning_effort"] == "high"
    assert completions.payload["tools"] == tools
    assert completions.payload["tool_choice"] == "auto"
    assert completions.payload["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
@pytest.mark.parametrize("reasoning", [ReasoningMode.DISABLED, ReasoningMode.MINIMAL])
async def test_grok47_rejects_unsupported_effort_before_client_dispatch(
    reasoning: ReasoningMode,
) -> None:
    class FakeCompletions:
        def __init__(self) -> None:
            self.calls = 0

        def create(self, **_payload: object) -> None:
            self.calls += 1

    completions = FakeCompletions()
    architect = XaiArchitect(model_name="grok-4.7", reasoning=reasoning)
    architect.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))

    result = await architect.analyze({"formatted_prompt": "Analyze"})

    assert "not supported for xAI model 'grok-4.7'" in result["error"]
    assert completions.calls == 0


@pytest.mark.parametrize(
    ("reasoning", "expected_effort"),
    [
        (ReasoningMode.LOW, "low"),
        (ReasoningMode.MEDIUM, "medium"),
        (ReasoningMode.HIGH, "high"),
        (ReasoningMode.XHIGH, "xhigh"),
        (ReasoningMode.ENABLED, "high"),
        (ReasoningMode.DYNAMIC, "high"),
    ],
)
def test_prepare_request_maps_documented_grok46_efforts(
    reasoning: ReasoningMode,
    expected_effort: str,
) -> None:
    prepared = prepare_request(
        model_name="grok-4.6",
        content="Analyze",
        reasoning=reasoning,
        defaults=resolve_model_defaults("grok-4.6"),
        tools=None,
    )

    assert prepared.payload["reasoning_effort"] == expected_effort


@pytest.mark.parametrize(
    "reasoning",
    [
        ReasoningMode.DISABLED,
        ReasoningMode.MINIMAL,
        ReasoningMode.MAX,
        ReasoningMode.TEMPERATURE,
    ],
)
def test_prepare_request_rejects_unsupported_grok46_efforts(reasoning: ReasoningMode) -> None:
    with pytest.raises(ValueError, match="not supported for xAI model 'grok-4.6'"):
        prepare_request(
            model_name="grok-4.6",
            content="Analyze",
            reasoning=reasoning,
            defaults=resolve_model_defaults("grok-4.6"),
            tools=None,
        )


@pytest.mark.parametrize(
    "reasoning",
    [
        ReasoningMode.DISABLED,
        ReasoningMode.MINIMAL,
        ReasoningMode.XHIGH,
        ReasoningMode.MAX,
        ReasoningMode.TEMPERATURE,
    ],
)
def test_prepare_request_rejects_unsupported_grok45_efforts(reasoning: ReasoningMode) -> None:
    with pytest.raises(ValueError, match="not supported for xAI model 'grok-4.5'"):
        prepare_request(
            model_name="grok-4.5",
            content="Analyze",
            reasoning=reasoning,
            defaults=resolve_model_defaults("grok-4.5"),
            tools=None,
        )


@pytest.mark.parametrize(
    ("model_name", "reasoning"),
    [
        ("grok-4.20-0309-reasoning", ReasoningMode.ENABLED),
        ("grok-4.20-0309-non-reasoning", ReasoningMode.DISABLED),
    ],
)
def test_prepare_request_uses_grok420_identity_without_invented_effort(
    model_name: str,
    reasoning: ReasoningMode,
) -> None:
    prepared = prepare_request(
        model_name=model_name,
        content="Analyze",
        reasoning=reasoning,
        defaults=resolve_model_defaults(model_name),
        tools=None,
    )

    assert prepared.payload["model"] == model_name
    assert "reasoning_effort" not in prepared.payload


@pytest.mark.parametrize(
    ("model_name", "reasoning"),
    [
        ("grok-4.20-0309-reasoning", ReasoningMode.DISABLED),
        ("grok-4.20-0309-reasoning", ReasoningMode.HIGH),
        ("grok-4.20-0309-non-reasoning", ReasoningMode.ENABLED),
        ("grok-4.20-0309-non-reasoning", ReasoningMode.HIGH),
    ],
)
def test_prepare_request_rejects_non_fixed_grok420_reasoning_modes(
    model_name: str,
    reasoning: ReasoningMode,
) -> None:
    fixed_mode = resolve_model_defaults(model_name).default_reasoning.value
    with pytest.raises(ValueError, match=f"fixed reasoning mode.*{fixed_mode}"):
        prepare_request(
            model_name=model_name,
            content="Analyze",
            reasoning=reasoning,
            defaults=resolve_model_defaults(model_name),
            tools=None,
        )


def test_xai_architect_keeps_grok46_default_pending_evaluation() -> None:
    architect = XaiArchitect()

    assert architect.model_name == "grok-4.6"
    assert architect.reasoning == ReasoningMode.HIGH
