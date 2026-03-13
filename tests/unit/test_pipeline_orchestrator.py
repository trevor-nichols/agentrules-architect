import unittest

from agentrules.core.pipeline.config import GitignoreSnapshot, ProjectSnapshot
from agentrules.core.pipeline.orchestrator import AnalysisPipeline


class _RecordingPhase1:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], dict, dict]] = []

    async def run(
        self,
        tree: list[str],
        package_info: dict,
        project_profile: dict | None = None,
    ) -> dict:
        profile = project_profile or {}
        self.calls.append((tree, package_info, profile))
        return {"phase": "Initial Discovery", "project_profile": profile}


class _NoopPhase2:
    async def run(self, phase1_results: dict, tree: list[str]) -> dict:
        return {"plan": "", "agents": []}


class _NoopPhase3:
    async def run(self, phase2_results: dict, tree: list[str], directory) -> dict:
        return {"phase": "Deep Analysis", "findings": []}


class _NoopPhase4:
    async def run(self, phase3_results: dict) -> dict:
        return {"analysis": ""}


class _NoopPhase5:
    async def run(self, all_results: dict) -> dict:
        return {"phase": "Consolidation", "report": ""}


class _NoopFinal:
    async def run(self, consolidated_report: dict, tree: list[str], rules_filename: str | None = None) -> dict:
        return {"analysis": ""}


class AnalysisPipelineTests(unittest.IsolatedAsyncioTestCase):
    async def test_run_phase1_forwards_project_profile_to_phase1_analysis(self) -> None:
        phase1 = _RecordingPhase1()
        pipeline = AnalysisPipeline(
            phase1=phase1,
            phase2=_NoopPhase2(),
            phase3=_NoopPhase3(),
            phase4=_NoopPhase4(),
            phase5=_NoopPhase5(),
            final=_NoopFinal(),
        )
        snapshot = ProjectSnapshot(
            tree_with_delimiters=("<project_structure>", "src/", "</project_structure>"),
            tree=("src/",),
            dependency_info={"summary": {"python": ["pyproject.toml"]}},
            gitignore=GitignoreSnapshot(spec=None, path=None),
            project_profile={"detected_types": ["python"]},
        )

        result = await pipeline.run_phase1(snapshot)

        self.assertEqual(
            phase1.calls,
            [(["src/"], {"summary": {"python": ["pyproject.toml"]}}, {"detected_types": ["python"]})],
        )
        self.assertEqual(
            result,
            {"phase": "Initial Discovery", "project_profile": {"detected_types": ["python"]}},
        )


if __name__ == "__main__":
    unittest.main()
