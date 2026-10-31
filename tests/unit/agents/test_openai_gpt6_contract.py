from __future__ import annotations

from typing import Any, cast

import pytest
from openai import OpenAI

from agentrules.config.agents import MODEL_PRESETS
from agentrules.core.agents.base import ReasoningMode
from agentrules.core.agents.openai import OpenAIArchitect
from agentrules.core.agents.openai.client import execute_request, set_client
from agentrules.core.agents.openai.request_builder import prepare_request


class FakeResponses:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def create(self, **payload: Any) -> dict[str, Any]:
        self.calls.append(payload)
        return {"output": [{"type": "message", "content": [{"type": "output_text", "text": "ok"}]}]}


class FakeClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


@pytest.mark.parametrize(
    ("key_prefix", "wire_model", "efforts"),
    [
        ("gpt6-astra", "gpt-6-astra", ("low", "medium", "high", "xhigh", "max")),
        ("gpt61-sol", "gpt-6.1-sol", ("low", "medium", "high", "xhigh", "max")),
        ("gpt6-sol", "gpt-6-sol", ("none", "low", "medium", "high", "xhigh", "max")),
        ("gpt6-luna", "gpt-6-luna", ("none", "low", "medium", "high", "xhigh", "max")),
    ],
)
def test_gpt6_picker_presets_dispatch_exact_wire_effort(
    key_prefix: str, wire_model: str, efforts: tuple[str, ...]
) -> None:
    fake = FakeClient()
    set_client(cast(OpenAI, fake))
    try:
        for effort in efforts:
            suffix = "default" if effort == "medium" else effort
            config = MODEL_PRESETS[f"{key_prefix}-{suffix}"]["config"]
            prepared = prepare_request(
                model_name=config.model_name,
                content="Inspect this change",
                reasoning=config.reasoning,
                temperature=config.temperature,
                tools=[{"type": "function", "name": "lookup", "parameters": {"type": "object"}}],
                text_verbosity=config.text_verbosity,
                use_responses_api=True,
                structured_text={"format": {"type": "json_schema", "name": "result", "schema": {"type": "object"}}},
            )
            execute_request(prepared)

            sent = fake.responses.calls[-1]
            assert sent["model"] == wire_model
            assert sent["reasoning"] == {"effort": effort}
            assert sent["tool_choice"] == "auto"
            assert sent["text"]["format"]["type"] == "json_schema"
    finally:
        set_client(None)


@pytest.mark.asyncio
@pytest.mark.parametrize("wire_model", ["gpt-6-astra", "gpt-6.1-sol"])
async def test_gpt6_reasoning_none_fails_before_dispatch(wire_model: str) -> None:
    fake = FakeClient()
    set_client(cast(OpenAI, fake))
    try:
        architect = OpenAIArchitect(model_name=wire_model, reasoning=ReasoningMode.DISABLED)
        result = await architect.analyze({"formatted_prompt": "Inspect this change"})
        assert "does not support reasoning effort 'none'" in result["error"]
        assert fake.responses.calls == []
    finally:
        set_client(None)


@pytest.mark.parametrize("wire_model", ["gpt-6-astra", "gpt-6.1-sol", "gpt-6-sol", "gpt-6-luna"])
def test_gpt6_rejects_minimal_effort(wire_model: str) -> None:
    with pytest.raises(ValueError, match="does not support reasoning effort 'minimal'"):
        prepare_request(
            model_name=wire_model,
            content="Inspect this change",
            reasoning=ReasoningMode.MINIMAL,
            temperature=None,
            tools=None,
            text_verbosity=None,
            use_responses_api=True,
        )
