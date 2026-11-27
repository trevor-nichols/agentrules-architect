"""Unit tests for Phase 1 researcher guardrails."""

from __future__ import annotations

import json
import unittest
from collections.abc import Sequence
from typing import Any
from unittest.mock import patch

import httpx
from openai import OpenAI

from agentrules.config.prompts.phase_1_prompts import (
    DEPENDENCY_CATALOG_PROMPT,
    DEPENDENCY_KNOWLEDGE_GAP_PROMPT,
)
from agentrules.core.agents.base import ModelProvider, ReasoningMode
from agentrules.core.agents.deepseek.architect import DeepSeekArchitect
from agentrules.core.analysis.phase_1 import Phase1Analysis


class _StaticAgent:
    def __init__(self, name: str) -> None:
        self.name = name

    async def analyze(self, context: dict[str, Any], tools: Sequence[Any] | None = None) -> dict[str, Any]:
        return {"agent": self.name, "findings": {}}


class _NoToolResearcher:
    async def analyze(self, context: dict[str, Any], tools: Sequence[Any] | None = None) -> dict[str, Any]:
        return {"agent": "Researcher Agent", "findings": "fallback summary"}


class _FailingToolResearcher:
    def __init__(self) -> None:
        self.invocations = 0

    async def analyze(self, context: dict[str, Any], tools: Sequence[Any] | None = None) -> dict[str, Any]:
        self.invocations += 1
        if "tool_feedback" in context:
            return {"agent": "Researcher Agent", "findings": "tool feedback ignored"}
        return {
            "agent": "Researcher Agent",
            "findings": None,
            "tool_calls": [
                {
                    "type": "function",
                    "function": {
                        "name": "tavily_web_search",
                        "arguments": json.dumps({
                            "query": "flask",
                            "search_depth": "basic",
                            "max_results": 1,
                        })
                    },
                }
            ],
        }


class _CodexResearcher:
    provider = ModelProvider.CODEX

    def __init__(self) -> None:
        self.calls: list[Sequence[Any] | None] = []

    async def analyze(self, context: dict[str, Any], tools: Sequence[Any] | None = None) -> dict[str, Any]:
        self.calls.append(tools)
        return {"agent": "Researcher Agent", "findings": "runtime research summary"}


def _stub_architect_factory(phase: str, **kwargs: Any) -> _StaticAgent:  # pragma: no cover - helper
    name = kwargs.get("name") or f"{phase.title()} Agent"
    return _StaticAgent(name)


class Phase1ResearcherGuardrailsTests(unittest.IsolatedAsyncioTestCase):
    def test_dependency_prompt_catalog_when_researcher_disabled(self) -> None:
        with patch("agentrules.core.analysis.phase_1.get_architect_for_phase") as mock_factory:
            def _factory(*args: Any, **kwargs: Any) -> _StaticAgent:
                return _StaticAgent(kwargs.get("name", "Agent"))

            mock_factory.side_effect = _factory
            analyzer = Phase1Analysis(researcher_enabled=False)

        self.assertIsNone(analyzer.researcher_architect)
        dependency_call = mock_factory.call_args_list[0]
        dependency_kwargs = dependency_call.kwargs
        self.assertEqual(dependency_kwargs["role"], DEPENDENCY_CATALOG_PROMPT["role"])
        self.assertEqual(
            dependency_kwargs["responsibilities"],
            DEPENDENCY_CATALOG_PROMPT["responsibilities"],
        )

    def test_dependency_prompt_knowledge_gap_when_researcher_enabled(self) -> None:
        with patch("agentrules.core.analysis.phase_1.get_architect_for_phase") as mock_factory, \
                patch("agentrules.core.analysis.phase_1.get_researcher_architect", return_value=_StaticAgent("Researcher Agent")):
            def _factory(*args: Any, **kwargs: Any) -> _StaticAgent:
                return _StaticAgent(kwargs.get("name", "Agent"))

            mock_factory.side_effect = _factory
            analyzer = Phase1Analysis(researcher_enabled=True)

        self.assertIsNotNone(analyzer.researcher_architect)
        dependency_call = mock_factory.call_args_list[0]
        dependency_kwargs = dependency_call.kwargs
        self.assertEqual(dependency_kwargs["role"], DEPENDENCY_KNOWLEDGE_GAP_PROMPT["role"])
        self.assertEqual(
            dependency_kwargs["responsibilities"],
            DEPENDENCY_KNOWLEDGE_GAP_PROMPT["responsibilities"],
        )

    async def test_researcher_skipped_when_no_tools_requested(self) -> None:
        with patch("agentrules.core.analysis.phase_1.get_architect_for_phase", side_effect=_stub_architect_factory), \
                patch("agentrules.core.analysis.phase_1.get_researcher_architect", return_value=_NoToolResearcher()):
            analyzer = Phase1Analysis(researcher_enabled=True)
            result = await analyzer.run([], {})

        research_output = result["documentation_research"]
        self.assertNotEqual(research_output.get("status"), "skipped")
        self.assertIn("findings", research_output)
        self.assertEqual(research_output.get("executed_tools"), [])

    async def test_researcher_skipped_when_all_tools_fail(self) -> None:
        async def failing_tavily(query: str, depth: str, max_results: int) -> str:  # pragma: no cover - injected
            return json.dumps({"error": "service unavailable"})

        with patch("agentrules.core.analysis.phase_1.get_architect_for_phase", side_effect=_stub_architect_factory), \
                patch("agentrules.core.analysis.phase_1.get_researcher_architect", return_value=_FailingToolResearcher()), \
                patch("agentrules.core.analysis.phase_1._run_tavily_search", side_effect=failing_tavily):
            analyzer = Phase1Analysis(researcher_enabled=True)
            result = await analyzer.run([], {})

        research_output = result["documentation_research"]
        self.assertEqual(research_output["status"], "skipped")
        self.assertEqual(research_output["reason"], "researcher-tools-failed")
        executed_tools = research_output.get("executed_tools", [])
        self.assertTrue(executed_tools)
        self.assertTrue(all("error" in record for record in executed_tools))

    async def test_deepseek_replays_tool_history_and_keeps_sibling_calls_after_failure(self) -> None:
        def tool_call(call_id: str, query: str) -> dict[str, Any]:
            return {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": "tavily_web_search",
                    "arguments": json.dumps({"query": query, "max_results": 1}, indent=2),
                },
            }

        first_turn = {
            "role": "assistant",
            "content": None,
            "reasoning_content": "Read both release references.",
            "tool_calls": [tool_call("call-a", "release notes"), tool_call("call-b", "broken source")],
        }
        second_turn = {
            "role": "assistant",
            "content": "Checking a mirror.",
            "reasoning_content": "Use the mirror for the unavailable reference.",
            "tool_calls": [tool_call("call-c", "mirror")],
        }
        final_turn = {"role": "assistant", "content": "Verified release documentation."}
        turns = [first_turn, second_turn, final_turn]
        sent: list[dict[str, Any]] = []

        def fake_provider(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/v1/chat/completions")
            index = len(sent)
            sent.append(json.loads(request.content))
            return httpx.Response(200, json={
                "id": f"test-completion-{index}",
                "choices": [{
                    "index": 0,
                    "finish_reason": "stop" if index == 2 else "tool_calls",
                    "message": turns[index],
                }],
            })

        async def search(query: str, _depth: str, _max_results: int) -> str:
            if query == "broken source":
                raise ValueError("search backend unavailable")
            return json.dumps({"results": [{"title": query}]})

        researcher = DeepSeekArchitect(
            model_name="deepseek-flash", reasoning=ReasoningMode.HIGH, system_prompt="Research dependencies.",
        )
        with OpenAI(
            api_key="test-token",
            base_url="https://example.test/v1",
            http_client=httpx.Client(transport=httpx.MockTransport(fake_provider)),
        ) as client, patch(
            "agentrules.core.analysis.phase_1.get_architect_for_phase", side_effect=_stub_architect_factory,
        ), patch(
            "agentrules.core.analysis.phase_1.get_researcher_architect", return_value=researcher,
        ), patch(
            "agentrules.core.analysis.phase_1._run_tavily_search", side_effect=search,
        ):
            researcher.client = client
            result = await Phase1Analysis(researcher_enabled=True).run([], {})

        research = result["documentation_research"]
        self.assertEqual(len(sent), 3)
        prefix, first_follow_up, second_follow_up = [call["messages"] for call in sent]
        self.assertEqual([message["role"] for message in prefix], ["system", "user"])
        self.assertEqual(prefix[0]["content"], "Research dependencies.")
        self.assertEqual([call["reasoning_effort"] for call in sent], ["high"] * 3)
        self.assertEqual(first_follow_up, [
            *prefix,
            first_turn,
            {"role": "tool", "tool_call_id": "call-a", "content": json.dumps({"results": [{"title": "release notes"}]})},
            {"role": "tool", "tool_call_id": "call-b", "content": json.dumps({"error": "search backend unavailable"})},
        ])
        self.assertEqual(second_follow_up, [
            *first_follow_up,
            second_turn,
            {"role": "tool", "tool_call_id": "call-c", "content": json.dumps({"results": [{"title": "mirror"}]})},
        ])
        self.assertEqual(research["findings"], "Verified release documentation.")
        self.assertEqual([run.get("success", False) for run in research["executed_tools"]], [True, False, True])
        self.assertEqual(research["executed_tools"][1]["error"], "search backend unavailable")
        self.assertFalse(any(key.startswith("_deepseek") for key in research))
        self.assertNotIn(first_turn["reasoning_content"], json.dumps(research))

    async def test_codex_researcher_bypasses_external_tool_loop(self) -> None:
        researcher = _CodexResearcher()

        async def _unexpected_tool_loop(*args: Any, **kwargs: Any) -> dict[str, Any]:
            raise AssertionError("external tool loop should be bypassed for Codex researcher")

        with patch("agentrules.core.analysis.phase_1.get_architect_for_phase", side_effect=_stub_architect_factory), \
                patch("agentrules.core.analysis.phase_1.get_researcher_architect", return_value=researcher), \
                patch.object(Phase1Analysis, "_run_researcher_with_tools", side_effect=_unexpected_tool_loop):
            analyzer = Phase1Analysis(researcher_enabled=True)
            result = await analyzer.run([], {})

        research_output = result["documentation_research"]
        self.assertEqual(research_output.get("findings"), "runtime research summary")
        self.assertEqual(research_output.get("executed_tools"), [])
        self.assertEqual(researcher.calls, [None])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
