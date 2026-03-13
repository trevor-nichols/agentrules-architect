"""Core orchestration logic for the multi-phase analysis pipeline."""

from __future__ import annotations

import time

from agentrules.core.analysis import (
    FinalAnalysis,
    Phase1Analysis,
    Phase2Analysis,
    Phase3Analysis,
    Phase4Analysis,
    Phase5Analysis,
)
from agentrules.core.analysis.events import AnalysisEventSink
from agentrules.core.pipeline.config import (
    PipelineMetrics,
    PipelineResult,
    PipelineSettings,
    ProjectSnapshot,
)


class AnalysisPipeline:
    """Run the configured analysis phases and collect their outputs."""

    def __init__(
        self,
        *,
        phase1: Phase1Analysis,
        phase2: Phase2Analysis,
        phase3: Phase3Analysis,
        phase4: Phase4Analysis,
        phase5: Phase5Analysis,
        final: FinalAnalysis,
        event_sink: AnalysisEventSink | None = None,
    ) -> None:
        self._phase1 = phase1
        self._phase2 = phase2
        self._phase3 = phase3
        self._phase4 = phase4
        self._phase5 = phase5
        self._final = final
        self._event_sink = None
        self.set_event_sink(event_sink)

    def set_event_sink(self, sink: AnalysisEventSink | None) -> None:
        """Attach an event sink to phases that emit progress notifications."""

        self._event_sink = sink
        if hasattr(self._phase2, "set_event_sink"):
            self._phase2.set_event_sink(sink)
        if hasattr(self._phase3, "set_event_sink"):
            self._phase3.set_event_sink(sink)

    async def run_phase1(self, snapshot: ProjectSnapshot) -> dict[str, object]:
        tree = list(snapshot.tree)
        dependency_info = dict(snapshot.dependency_info)
        project_profile = dict(snapshot.project_profile)
        phase1_raw = await self._phase1.run(tree, dependency_info, project_profile)
        return dict(phase1_raw)

    async def run_phase2(
        self,
        phase1_results: dict[str, object],
        snapshot: ProjectSnapshot,
    ) -> dict[str, object]:
        tree = list(snapshot.tree)
        phase2_raw = await self._phase2.run(phase1_results, tree)
        return dict(phase2_raw)

    async def run_phase3(
        self,
        phase2_results: dict[str, object],
        settings: PipelineSettings,
        snapshot: ProjectSnapshot,
    ) -> dict[str, object]:
        tree = list(snapshot.tree)
        phase3_raw = await self._phase3.run(phase2_results, tree, settings.target_directory)
        return dict(phase3_raw)

    async def run_phase4(self, phase3_results: dict[str, object]) -> dict[str, object]:
        phase4_raw = await self._phase4.run(phase3_results)
        return dict(phase4_raw)

    async def run_phase5(
        self,
        all_results: dict[str, dict[str, object]],
    ) -> dict[str, object]:
        phase5_raw = await self._phase5.run(all_results)
        return dict(phase5_raw)

    async def run_final(
        self,
        consolidated_report: dict[str, object],
        snapshot: ProjectSnapshot,
        rules_filename: str | None = None,
    ) -> dict[str, object]:
        tree = list(snapshot.tree)
        final_raw = await self._final.run(
            consolidated_report,
            tree,
            rules_filename=rules_filename,
        )
        return dict(final_raw)

    async def run(self, settings: PipelineSettings, snapshot: ProjectSnapshot) -> PipelineResult:
        """Execute the sequential phase pipeline and return accumulated results."""

        start_time = time.time()

        phase1_results = await self.run_phase1(snapshot)
        phase2_results = await self.run_phase2(phase1_results, snapshot)
        phase3_results = await self.run_phase3(phase2_results, settings, snapshot)
        phase4_results = await self.run_phase4(phase3_results)

        all_results: dict[str, dict[str, object]] = {
            "phase1": phase1_results,
            "phase2": phase2_results,
            "phase3": phase3_results,
            "phase4": phase4_results,
        }
        consolidated_report = await self.run_phase5(all_results)
        final_analysis = await self.run_final(consolidated_report, snapshot)

        metrics = PipelineMetrics(elapsed_seconds=time.time() - start_time)
        return PipelineResult(
            snapshot=snapshot,
            phase1=phase1_results,
            phase2=phase2_results,
            phase3=phase3_results,
            phase4=phase4_results,
            consolidated_report=consolidated_report,
            final_analysis=final_analysis,
            metrics=metrics,
        )
