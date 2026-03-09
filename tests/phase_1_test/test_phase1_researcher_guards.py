"""Unit tests for Phase 1 researcher guardrails."""

from __future__ import annotations

import json
import unittest
from collections.abc import Sequence
from typing import Any
from unittest.mock import patch

from agentrules.config.prompts.phase_1_prompts import (
    DEPENDENCY_CATALOG_PROMPT,
    DEPENDENCY_KNOWLEDGE_GAP_PROMPT,
)
from agentrules.core.agents.base import ModelProvider
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
