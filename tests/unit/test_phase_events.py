import asyncio
import unittest
from pathlib import Path
from typing import cast
from unittest.mock import patch

from agentrules.core.agents.base import BaseArchitect
from agentrules.core.analysis.events import AnalysisEvent
from agentrules.core.analysis.phase_2 import Phase2Analysis
from agentrules.core.analysis.phase_3 import Phase3Analysis


class _CollectingSink:
    def __init__(self) -> None:
        self.events: list[AnalysisEvent] = []

    def publish(self, event: AnalysisEvent) -> None:
        self.events.append(event)


class PhaseEventTests(unittest.TestCase):
    def test_phase2_emits_agent_plan_event(self) -> None:
        asyncio.run(self._run_phase2_plan_event())

    def test_phase2_parser_receives_full_response_payload(self) -> None:
        asyncio.run(self._run_phase2_parser_receives_full_payload())

    async def _run_phase2_plan_event(self) -> None:
        sink = _CollectingSink()
        analysis = Phase2Analysis(events=sink)

        plan_response = {
            "plan": "<analysis_plan></analysis_plan>",
            "agents": [],
        }

        class FakePlanner:
            def __init__(self, response: dict) -> None:
                self.response = response

            async def create_analysis_plan(self, *args, **kwargs):  # type: ignore[no-untyped-def]
                return self.response

        analysis.architect = cast(BaseArchitect, FakePlanner(plan_response))

        parsed_agents = [
            {"id": "agent_1", "name": "Alpha", "file_assignments": ["a.py"]},
            {"id": "agent_2", "name": "Beta", "file_assignments": []},
        ]

        with patch("agentrules.core.analysis.phase_2.parse_agents_from_phase2", return_value=parsed_agents), patch(
            "agentrules.core.analysis.phase_2.extract_agent_fallback",
            return_value=[],
        ):
            await analysis.run({}, [])

        plan_events = [event for event in sink.events if event.type == "agent_plan"]
        self.assertEqual(len(plan_events), 1)
        payload_agents = plan_events[0].payload["agents"]
        self.assertEqual(len(payload_agents), 2)
        self.assertEqual(payload_agents[0]["name"], "Alpha")

    async def _run_phase2_parser_receives_full_payload(self) -> None:
        analysis = Phase2Analysis()
        plan_response = {"plan": "legacy plan text", "agents": [{"id": "agent_1"}]}

        class FakePlanner:
            async def create_analysis_plan(self, *args, **kwargs):  # type: ignore[no-untyped-def]
                return plan_response

        analysis.architect = cast(BaseArchitect, FakePlanner())

        with patch(
            "agentrules.core.analysis.phase_2.parse_agents_from_phase2",
            return_value=[{"id": "agent_1", "name": "Alpha", "file_assignments": []}],
        ) as parse_mock:
            await analysis.run({}, [])

        parse_mock.assert_called_once()
        assert parse_mock.call_args.args
        self.assertIs(parse_mock.call_args.args[0], plan_response)

    def test_phase3_emits_agent_lifecycle_events(self) -> None:
        asyncio.run(self._run_phase3_lifecycle_events())

    async def _run_phase3_lifecycle_events(self) -> None:
        sink = _CollectingSink()
        analysis = Phase3Analysis(events=sink)

        agents = [
            {"id": "agent_1", "name": "Alpha", "file_assignments": ["a.py"]},
            {"id": "agent_2", "name": "Beta", "file_assignments": ["b.py", "c.py"]},
        ]

        async def fake_file_contents(*args, **kwargs):  # type: ignore[no-untyped-def]
            return {}

        class FakeArchitect:
            def __init__(self, label: str) -> None:
                self.label = label

            async def analyze(self, context: dict) -> dict:  # type: ignore[no-untyped-def]
                return {"agent": self.label, "context": context}

        with patch("agentrules.core.analysis.phase_3.get_architect_for_phase") as mock_factory, patch.object(
            Phase3Analysis,
            "_get_file_contents",
            side_effect=fake_file_contents,
        ):
            mock_factory.side_effect = [FakeArchitect("Alpha"), FakeArchitect("Beta"), FakeArchitect("Gamma")]
            await analysis.run({"agents": agents}, [" file a.py"], Path("."))

        started = [e for e in sink.events if e.type == "agent_started"]
        completed = [e for e in sink.events if e.type == "agent_completed"]

        self.assertEqual(len(started), 2)
        self.assertEqual({evt.payload["id"] for evt in started}, {"agent_1", "agent_2"})
        self.assertEqual(len(completed), 2)


if __name__ == "__main__":
    unittest.main()
