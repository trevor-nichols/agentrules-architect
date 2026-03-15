"""Unit tests for Phase 1 profile-aware specialized agents."""

from __future__ import annotations

import unittest
from typing import Any
from unittest.mock import patch

from agentrules.config.prompts.phase_1_prompts import get_specialized_phase1_agent_prompts
from agentrules.core.analysis.phase_1 import Phase1Analysis


class _RecordingAgent:
    def __init__(self, name: str) -> None:
        self.name = name
        self.contexts: list[dict[str, Any]] = []

    async def analyze(self, context: dict[str, Any], tools: list[Any] | None = None) -> dict[str, Any]:
        self.contexts.append(dict(context))
        return {"agent": self.name, "findings": f"{self.name} findings"}


class Phase1ProfileAgentTests(unittest.IsolatedAsyncioTestCase):
    def test_specialized_prompt_selection_uses_profile_detection_flags(self) -> None:
        profile = {
            "frontend": {"detected": True},
            "python": {"detected": True},
        }
        prompts = get_specialized_phase1_agent_prompts(profile)
        names = [str(prompt["name"]) for prompt in prompts]
        self.assertEqual(names, ["Frontend Design Agent", "Python Tooling Agent"])

    async def test_frontend_specialized_agent_runs_when_frontend_profile_detected(self) -> None:
        created_agents: dict[str, _RecordingAgent] = {}

        def _factory(*args: Any, **kwargs: Any) -> _RecordingAgent:
            name = kwargs.get("name", "Agent")
            agent = _RecordingAgent(name)
            created_agents[name] = agent
            return agent

        with patch("agentrules.core.analysis.phase_1.get_architect_for_phase", side_effect=_factory):
            analyzer = Phase1Analysis(researcher_enabled=False)
            profile = {
                "frontend": {"detected": True},
                "python": {"detected": False},
            }
            result = await analyzer.run(["src/"], {"summary": {}, "manifests": []}, profile)

        names = [entry.get("agent") for entry in result["initial_findings"] if isinstance(entry, dict)]
        self.assertIn("Frontend Design Agent", names)
        self.assertNotIn("Python Tooling Agent", names)

        dependency_context = created_agents["Dependency Agent"].contexts[0]
        self.assertEqual(dependency_context["project_profile"], profile)

        frontend_context = created_agents["Frontend Design Agent"].contexts[0]
        self.assertEqual(frontend_context["project_profile"], profile)
        self.assertEqual(frontend_context["frontend_profile"], profile["frontend"])
        self.assertNotIn("python_profile", frontend_context)

    async def test_python_specialized_agent_runs_when_python_profile_detected(self) -> None:
        created_agents: dict[str, _RecordingAgent] = {}

        def _factory(*args: Any, **kwargs: Any) -> _RecordingAgent:
            name = kwargs.get("name", "Agent")
            agent = _RecordingAgent(name)
            created_agents[name] = agent
            return agent

        with patch("agentrules.core.analysis.phase_1.get_architect_for_phase", side_effect=_factory):
            analyzer = Phase1Analysis(researcher_enabled=False)
            profile = {
                "frontend": {"detected": False},
                "python": {"detected": True},
            }
            result = await analyzer.run(["src/"], {"summary": {}, "manifests": []}, profile)

        names = [entry.get("agent") for entry in result["initial_findings"] if isinstance(entry, dict)]
        self.assertIn("Python Tooling Agent", names)
        self.assertNotIn("Frontend Design Agent", names)

        python_context = created_agents["Python Tooling Agent"].contexts[0]
        self.assertEqual(python_context["project_profile"], profile)
        self.assertEqual(python_context["python_profile"], profile["python"])
        self.assertNotIn("frontend_profile", python_context)

    async def test_specialized_agents_are_skipped_for_generic_profile(self) -> None:
        created_agents: dict[str, _RecordingAgent] = {}

        def _factory(*args: Any, **kwargs: Any) -> _RecordingAgent:
            name = kwargs.get("name", "Agent")
            agent = _RecordingAgent(name)
            created_agents[name] = agent
            return agent

        with patch("agentrules.core.analysis.phase_1.get_architect_for_phase", side_effect=_factory):
            analyzer = Phase1Analysis(researcher_enabled=False)
            profile = {
                "frontend": {"detected": False},
                "python": {"detected": False},
            }
            result = await analyzer.run(["src/"], {"summary": {}, "manifests": []}, profile)

        names = [entry.get("agent") for entry in result["initial_findings"] if isinstance(entry, dict)]
        self.assertEqual(
            names,
            ["Dependency Agent", "Structure Agent", "Tech Stack Agent"],
        )
        self.assertNotIn("Frontend Design Agent", created_agents)
        self.assertNotIn("Python Tooling Agent", created_agents)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
