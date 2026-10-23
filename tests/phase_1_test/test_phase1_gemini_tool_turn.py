"""Gemini researcher tool calls keep the provider's conversation state intact."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

import pytest
from google.genai import types

from agentrules.core.agents.base import ReasoningMode
from agentrules.core.agents.gemini import GeminiArchitect
from agentrules.core.analysis.phase_1 import Phase1Analysis


class _TwoTurnModels:
    def __init__(self, call_id: str | None = "research-call-1") -> None:
        self.calls: list[dict[str, Any]] = []
        self.model_turn = types.Content(
            role="model",
            parts=[
                types.Part(
                    function_call=types.FunctionCall(
                        id=call_id,
                        name="tavily_web_search",
                        args={"query": "flask release"},
                    ),
                    thought_signature=b"signed-thinking-state",
                )
            ],
        )

    def generate_content(self, *, model: str, contents: Any, config: Any) -> Any:
        self.calls.append({"model": model, "contents": contents, "config": config})
        content = self.model_turn if len(self.calls) == 1 else types.Content(
            role="model", parts=[types.Part(text="Flask release verified")]
        )
        return SimpleNamespace(candidates=[SimpleNamespace(content=content)], text=None)


@pytest.mark.asyncio
async def test_researcher_preserves_gemini_call_identity_and_thought_signature() -> None:
    models = _TwoTurnModels()
    architect = GeminiArchitect(model_name="gemini-3.8-flash", reasoning=ReasoningMode.MEDIUM)
    architect.client = cast(Any, SimpleNamespace(models=models))
    analysis = Phase1Analysis(researcher_enabled=False)
    analysis.researcher_architect = architect

    async def search(_query: str, _depth: str, _max_results: int) -> str:
        return json.dumps({"results": [{"title": "Flask release"}]})

    with patch("agentrules.core.agents.gemini.architect.resolve_tool_config", return_value=[]), patch(
        "agentrules.core.analysis.phase_1._run_tavily_search", side_effect=search
    ):
        result = await analysis._run_researcher_with_tools({"dependency_summary": {"flask": "latest"}}, [])

    assert result["findings"] == "Flask release verified"
    assert result["executed_tools"][0]["success"] is True
    assert len(models.calls) == 2
    history = models.calls[1]["contents"]
    assert isinstance(history, list)
    assert "flask" in history[0].parts[0].text
    assert history[1].model_dump(mode="json", exclude_none=True) == models.model_turn.model_dump(
        mode="json", exclude_none=True
    )
    assert history[1].parts[0].thought_signature == b"signed-thinking-state"
    reply = history[2]
    function_response = reply.parts[0].function_response
    assert function_response.id == "research-call-1"
    assert function_response.name == "tavily_web_search"
    assert function_response.response == {"results": [{"title": "Flask release"}]}
    assert len(reply.parts) == 1
    assert reply.parts[0].text is None


@pytest.mark.asyncio
async def test_researcher_rejects_gemini38_call_without_id_before_second_request() -> None:
    models = _TwoTurnModels(call_id=None)
    architect = GeminiArchitect(model_name="gemini-3.8-flash", reasoning=ReasoningMode.MEDIUM)
    architect.client = cast(Any, SimpleNamespace(models=models))
    analysis = Phase1Analysis(researcher_enabled=False)
    analysis.researcher_architect = architect

    async def search(_query: str, _depth: str, _max_results: int) -> str:
        return json.dumps({"results": []})

    with patch("agentrules.core.agents.gemini.architect.resolve_tool_config", return_value=[]), patch(
        "agentrules.core.analysis.phase_1._run_tavily_search", side_effect=search
    ), pytest.raises(ValueError, match="missing its required ID"):
        await analysis._run_researcher_with_tools({}, [])

    assert len(models.calls) == 1
