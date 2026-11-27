"""Gemini researcher tool calls keep the provider's conversation state intact."""

from __future__ import annotations

import json
from datetime import datetime
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, patch

import pytest
from google.genai import types

from agentrules.core.agents.base import ReasoningMode
from agentrules.core.agents.factory.factory import ArchitectFactory
from agentrules.core.agents.gemini import GeminiArchitect
from agentrules.core.analysis.phase_1 import Phase1Analysis
from agentrules.core.configuration import model_presets


class _TwoTurnModels:
    def __init__(
        self,
        call_ids: tuple[str | None, ...] = ("research-call-1",),
        function_args: dict[str, Any] | None = None,
    ) -> None:
        self.calls: list[dict[str, Any]] = []
        self.model_turn = types.Content(
            role="model",
            parts=[
                types.Part(
                    function_call=types.FunctionCall(
                        id=call_id,
                        name="tavily_web_search",
                        args=function_args or {"query": "flask release"},
                    ),
                    thought_signature=b"signed-thinking-state",
                )
                for call_id in call_ids
            ],
        )

    def generate_content(self, *, model: str, contents: Any, config: Any) -> Any:
        self.calls.append({"model": model, "contents": contents, "config": config})
        content = self.model_turn if len(self.calls) == 1 else types.Content(
            role="model", parts=[types.Part(text="Flask release verified")]
        )
        return SimpleNamespace(candidates=[SimpleNamespace(content=content)], text=None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("preset_key", "wire_model", "thinking_level"),
    [
        ("gemini-pro", "gemini-3.8-flash", "MEDIUM"),
        ("gemini-4-neon-reasoning-xhigh", "gemini-4-neon", "XHIGH"),
    ],
)
async def test_researcher_replays_signed_tool_turn_at_configured_thinking_level(
    monkeypatch, preset_key: str, wire_model: str, thinking_level: str,
) -> None:
    monkeypatch.setattr(
        model_presets,
        "datetime",
        SimpleNamespace(now=lambda tz: datetime(2026, 12, 1, tzinfo=tz)),
    )
    config = model_presets.get_model_config_for_preset_key(preset_key)
    assert config is not None
    models = _TwoTurnModels()
    architect = ArchitectFactory.create_architect(config, "Researcher", "Research dependencies", [], "{context}")
    assert isinstance(architect, GeminiArchitect)
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
    assert [call["model"] for call in models.calls] == [wire_model, wire_model]
    for call in models.calls:
        thinking = call["config"].thinking_config
        assert thinking.thinking_level == thinking_level
        assert thinking.thinking_budget is None
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
@pytest.mark.parametrize(
    ("call_ids", "error_detail"),
    [
        (("research-call-1", None), "missing its required ID"),
        (("research-call-1", "research-call-1"), "duplicate call ID"),
    ],
    ids=["missing-id", "duplicate-id"],
)
async def test_phase1_skips_invalid_gemini_tool_turn_before_search(
    call_ids: tuple[str | None, ...], error_detail: str,
) -> None:
    models = _TwoTurnModels(call_ids=call_ids)
    architect = GeminiArchitect(model_name="gemini-3.8-flash", reasoning=ReasoningMode.MEDIUM)
    architect.client = cast(Any, SimpleNamespace(models=models))
    findings = [
        {"findings": "Dependency discovery complete"},
        {"findings": "Structure discovery complete"},
        {"findings": "Tech stack discovery complete"},
    ]
    required_agents = [SimpleNamespace(analyze=AsyncMock(return_value=result)) for result in findings]
    search = AsyncMock(return_value='{"results": []}')

    with (
        patch("agentrules.core.analysis.phase_1.get_architect_for_phase", side_effect=required_agents),
        patch("agentrules.core.analysis.phase_1.get_researcher_architect", return_value=architect),
        patch("agentrules.core.agents.gemini.architect.resolve_tool_config", return_value=[]),
        patch("agentrules.core.analysis.phase_1._run_tavily_search", new=search),
    ):
        result = await Phase1Analysis().run([], {})

    research = result["documentation_research"]
    assert research["status"] == "skipped"
    assert error_detail in research["error"]
    search.assert_not_awaited()
    assert research["executed_tools"] == []
    assert len(models.calls) == 1
    assert result["initial_findings"] == findings
    for agent in required_agents[1:]:
        assert agent.analyze.await_args.args[0]["research_agent_error"] == research["error"]


@pytest.mark.asyncio
async def test_researcher_returns_matching_gemini_error_response_for_failed_tool() -> None:
    models = _TwoTurnModels(function_args={"query": "flask release", "max_results": "invalid"})
    architect = GeminiArchitect(model_name="gemini-3.8-flash", reasoning=ReasoningMode.MEDIUM)
    architect.client = cast(Any, SimpleNamespace(models=models))
    analysis = Phase1Analysis(researcher_enabled=False)
    analysis.researcher_architect = architect

    with patch("agentrules.core.agents.gemini.architect.resolve_tool_config", return_value=[]):
        result = await analysis._run_researcher_with_tools({}, [])

    assert len(models.calls) == 2
    history = models.calls[1]["contents"]
    response = history[2].parts[0].function_response
    assert response.id == "research-call-1"
    assert response.name == "tavily_web_search"
    assert "invalid literal" in response.response["error"]
    assert result["executed_tools"][0]["error"] == response.response["error"]
