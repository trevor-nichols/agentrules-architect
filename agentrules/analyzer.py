"""
Core orchestration logic for the CursorRules Architect analysis pipeline.

This module extracts the business workflow from the legacy ``main.py`` CLI so it
can be reused by both programmatic and Typer-based command-line interfaces.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import Sequence
from numbers import Real
from pathlib import Path

from pathspec import PathSpec
from rich.console import Console

from agentrules.cli.ui.analysis_view import AnalysisView
from agentrules.config_service import (
    get_effective_exclusions,
    get_exclusion_overrides,
    get_rules_filename,
    should_generate_cursorignore,
    should_generate_phase_outputs,
    should_respect_gitignore,
)
from config.agents import MODEL_CONFIG
from core.analysis import (
    FinalAnalysis,
    Phase1Analysis,
    Phase2Analysis,
    Phase3Analysis,
    Phase4Analysis,
    Phase5Analysis,
)
from core.analysis.events import AnalysisEvent, AnalysisEventSink
from core.utils.file_creation.cursorignore import create_cursorignore
from core.utils.file_creation.phases_output import save_phase_outputs
from core.utils.file_system.gitignore import load_gitignore_spec
from core.utils.file_system.tree_generator import get_project_tree
from core.utils.formatters.clean_cursorrules import clean_cursorrules
from core.utils.model_config_helper import get_model_config_name


class _ViewEventSink(AnalysisEventSink):
    """Translate analysis events into Rich-rendered status updates."""

    PHASE_COLORS = {
        "phase2": "blue",
        "phase3": "yellow",
    }

    def __init__(self, view: AnalysisView):
        self.view = view
        self._agents: dict[str, dict] = {}

    def publish(self, event: AnalysisEvent) -> None:
        if event.phase == "phase2" and event.type == "agent_plan":
            agents = list(event.payload.get("agents", []))
            self._cache_agents(agents)
            self.view.render_agent_plan(agents, color=self.PHASE_COLORS["phase2"])
            return

        if event.phase not in self.PHASE_COLORS:
            return

        phase_color = self.PHASE_COLORS[event.phase]
        payload = dict(event.payload)
        agent_id = payload.get("id")
        if agent_id:
            agent_info = self._agents.setdefault(agent_id, {})
            agent_info.update(payload)
        agent_name = self._resolve_agent_name(payload)

        if event.type == "agent_registered":
            detail = self._format_file_detail(payload.get("files"))
            message = f"Pending{detail}" if detail else "Pending"
            self.view.update_agent_progress(
                event.phase,
                agent_id or agent_name,
                agent_name,
                message,
                "⏳",
                phase_color,
                phase_color,
            )
            return
        if event.type == "agent_started":
            detail = self._format_file_detail(payload.get("files"))
            message = f"In progress{detail}"
            self.view.update_agent_progress(
                event.phase,
                agent_id or agent_name,
                agent_name,
                message,
                "⟳",
                phase_color,
                phase_color,
            )
        elif event.type == "agent_completed":
            message = "Completed"
            duration = payload.get("duration")
            if isinstance(duration, Real):
                message += f" in {duration:.1f}s"
            self.view.update_agent_progress(
                event.phase,
                agent_id or agent_name,
                agent_name,
                message,
                "✓",
                phase_color,
                phase_color,
            )
        elif event.type == "agent_failed":
            error = payload.get("error", "unknown error")
            duration = payload.get("duration")
            message = f"Failed: {error}"
            if isinstance(duration, Real):
                message += f" after {duration:.1f}s"
            self.view.update_agent_progress(
                event.phase,
                agent_id or agent_name,
                agent_name,
                message,
                "✗",
                "red",
                phase_color,
            )

    def _cache_agents(self, agents: list[dict]) -> None:
        for entry in agents:
            agent_id = entry.get("id")
            if agent_id:
                self._agents.setdefault(agent_id, {}).update(entry)

    def _resolve_agent_name(self, payload: dict) -> str:
        if payload.get("name"):
            return str(payload["name"])
        if payload.get("id"):
            return str(payload["id"])
        return "Agent"

    def _format_file_detail(self, files: object) -> str:
        if not files:
            return ""
        try:
            count = len(files)  # type: ignore[arg-type]
        except TypeError:
            return ""
        label = "file" if count == 1 else "files"
        return f" · {count} {label}"

logger = logging.getLogger("project_extractor")


class ProjectAnalyzer:
    """High-level coordinator for the six-phase analysis pipeline."""

    def __init__(self, directory: Path, console: Console | None = None):
        self.directory = directory
        self.console = console or Console()

        self.phase1_results: dict = {}
        self.phase2_results: dict = {}
        self.phase3_results: dict = {}
        self.phase4_results: dict = {}
        self.consolidated_report: dict = {}
        self.final_analysis: dict = {}

        self.exclusion_overrides = None
        self.effective_exclusions: tuple[set[str], set[str], set[str]] = (
            set(),
            set(),
            set(),
        )
        self.gitignore_spec: PathSpec | None = None
        self.gitignore_path: Path | None = None
        self.respect_gitignore: bool = True

        self.phase1_analyzer = Phase1Analysis()
        self.phase2_analyzer = Phase2Analysis()
        self.phase3_analyzer = Phase3Analysis()
        self.phase4_analyzer = Phase4Analysis()
        self.phase5_analyzer = Phase5Analysis()
        self.final_analyzer = FinalAnalysis()

    def _apply_event_sink(self, sink: AnalysisEventSink | None) -> None:
        if hasattr(self.phase2_analyzer, "set_event_sink"):
            self.phase2_analyzer.set_event_sink(sink)
        if hasattr(self.phase3_analyzer, "set_event_sink"):
            self.phase3_analyzer.set_event_sink(sink)

    async def run_phase1(self, tree: list[str], package_info: dict) -> dict:
        return await self.phase1_analyzer.run(tree, package_info)

    async def run_phase2(self, phase1_results: dict, tree: Sequence[str]) -> dict:
        return await self.phase2_analyzer.run(phase1_results, tree)

    async def run_phase3(self, analysis_plan: dict, tree: Sequence[str]) -> dict:
        return await self.phase3_analyzer.run(analysis_plan, list(tree), self.directory)

    async def run_phase4(self, phase3_results: dict) -> dict:
        return await self.phase4_analyzer.run(phase3_results)

    async def run_phase5(self, all_results: dict) -> dict:
        return await self.phase5_analyzer.run(all_results)

    async def run_final_analysis(
        self,
        consolidated_report: dict,
        tree: Sequence[str] | None = None,
    ) -> dict:
        return await self.final_analyzer.run(consolidated_report, tree)

    async def analyze(self) -> str:
        metrics_start_time = time.time()
        view = AnalysisView(self.console)
        event_sink = _ViewEventSink(view)
        self._apply_event_sink(event_sink)

        self.exclusion_overrides = get_exclusion_overrides()
        exclude_dirs, exclude_files, exclude_exts = get_effective_exclusions()
        self.effective_exclusions = (exclude_dirs, exclude_files, exclude_exts)
        self.respect_gitignore = should_respect_gitignore()
        self.gitignore_spec = None
        self.gitignore_path = None
        if self.respect_gitignore:
            gitignore_loaded = load_gitignore_spec(self.directory)
            if gitignore_loaded:
                self.gitignore_spec = gitignore_loaded.spec
                self.gitignore_path = gitignore_loaded.path

        tree_with_delimiters = get_project_tree(
            self.directory,
            exclude_dirs=exclude_dirs,
            exclude_files=exclude_files,
            exclude_extensions=exclude_exts,
            gitignore_spec=self.gitignore_spec,
        )
        tree_for_analysis = _strip_tree_delimiters(tree_with_delimiters)

        package_info: dict = {}

        view.render_phase_header(
            "Phase 1 · Initial Discovery",
            "green",
            "Assessing structure, dependencies, and tech stack",
        )
        view.render_agent_overview(
            (
                "Structure Agent",
                "Dependency Agent",
                "Tech Stack Agent",
            ),
            color="green",
        )
        self.phase1_results = await view.run_with_spinner(
            "Running discovery agents...",
            "green",
            self.run_phase1(tree_for_analysis, package_info),
        )
        view.render_completion("Discovery agents completed", "green")

        view.render_phase_header(
            "Phase 2 · Methodical Planning",
            "blue",
            "Designing a targeted analysis plan",
        )
        self.phase2_results = await view.run_with_spinner(
            "Creating analysis plan...",
            "blue",
            self.run_phase2(self.phase1_results, tree_for_analysis),
        )
        agents = self.phase2_results.get("agents") or []
        view.render_completion("Analysis plan created", "blue")

        view.render_phase_header(
            "Phase 3 · Deep Analysis",
            "yellow",
            "Executing specialized agents across files",
        )
        if agents:
            view.start_agent_progress("phase3", agents, color="yellow")
        else:
            view.render_note("Specialized agents running on project files", style="dim")
        self.phase3_results = await view.run_with_spinner(
            "Analyzing files in depth...",
            "yellow",
            self.run_phase3(self.phase2_results, tree_for_analysis),
        )
        view.stop_agent_progress("phase3")
        view.render_completion("Deep analysis finished", "yellow")

        view.render_phase_header(
            "Phase 4 · Synthesis",
            "magenta",
            "Distilling findings into unified insights",
        )
        self.phase4_results = await view.run_with_spinner(
            "Synthesizing findings...",
            "magenta",
            self.run_phase4(self.phase3_results),
        )
        view.render_completion("Findings synthesized", "magenta")

        view.render_phase_header(
            "Phase 5 · Consolidation",
            "cyan",
            "Assembling final multi-phase report",
        )
        all_results = {
            "phase1": self.phase1_results,
            "phase2": self.phase2_results,
            "phase3": self.phase3_results,
            "phase4": self.phase4_results,
        }
        self.consolidated_report = await view.run_with_spinner(
            "Consolidating results...",
            "cyan",
            self.run_phase5(all_results),
        )
        view.render_completion("Results consolidated", "cyan")

        view.render_phase_header(
            "Final Analysis",
            "white",
            "Preparing Cursor rules output",
        )
        self.final_analysis = await view.run_with_spinner(
            "Creating rules...",
            "white",
            self.run_final_analysis(self.consolidated_report, tree_for_analysis),
        )
        view.render_completion("Cursor rules ready", "white")

        analysis_lines: list[str] = [
            f"Project Analysis Report for: {self.directory}",
            "=" * 50 + "\n",
            "## Project Structure\n",
        ]
        analysis_lines.extend(tree_with_delimiters)
        analysis_lines.append("\n")

        phase1_model = get_model_config_name(MODEL_CONFIG["phase1"])
        phase2_model = get_model_config_name(MODEL_CONFIG["phase2"])
        phase3_model = get_model_config_name(MODEL_CONFIG["phase3"])
        phase4_model = get_model_config_name(MODEL_CONFIG["phase4"])
        phase5_model = get_model_config_name(MODEL_CONFIG["phase5"])
        final_model = get_model_config_name(MODEL_CONFIG["final"])

        total_seconds = time.time() - metrics_start_time

        analysis_lines.extend(
            [
                f"Phase 1: Initial Discovery (Config: {phase1_model})",
                "-" * 30,
                json.dumps(self.phase1_results, indent=2),
                "\n",
                f"Phase 2: Methodical Planning (Config: {phase2_model})",
                "-" * 30,
                self.phase2_results.get("plan", "Error in planning phase"),
                "\n",
                f"Phase 3: Deep Analysis (Config: {phase3_model})",
                "-" * 30,
                json.dumps(self.phase3_results, indent=2),
                "\n",
                f"Phase 4: Synthesis (Config: {phase4_model})",
                "-" * 30,
                self.phase4_results.get("analysis", "Error in synthesis phase"),
                "\n",
                f"Phase 5: Consolidation (Config: {phase5_model})",
                "-" * 30,
                self.consolidated_report.get("report", "Error in consolidation phase"),
                "\n",
                f"Final Analysis (Config: {final_model})",
                "-" * 30,
                self.final_analysis.get("analysis", "Error in final analysis phase"),
                "\n",
                "Analysis Metrics",
                "-" * 30,
                f"Time taken: {total_seconds:.2f} seconds",
            ]
        )

        return "\n".join(analysis_lines)

    def persist_outputs(self, metrics_start_time: float) -> None:
        analysis_data = {
            "phase1": self.phase1_results,
            "phase2": self.phase2_results,
            "phase3": self.phase3_results,
            "phase4": self.phase4_results,
            "consolidated_report": self.consolidated_report,
            "final_analysis": self.final_analysis,
            "metrics": {"time": time.time() - metrics_start_time},
        }

        rules_filename = get_rules_filename()
        include_phase_outputs = should_generate_phase_outputs()

        exclusion_summary = None
        overrides = self.exclusion_overrides
        if overrides and not overrides.is_empty():
            dirs, files, exts = self.effective_exclusions
            exclusion_summary = {
                "added": {
                    "directories": sorted(set(overrides.add_directories)),
                    "files": sorted(set(overrides.add_files)),
                    "extensions": sorted(set(overrides.add_extensions)),
                },
                "removed": {
                    "directories": sorted(set(overrides.remove_directories)),
                    "files": sorted(set(overrides.remove_files)),
                    "extensions": sorted(set(overrides.remove_extensions)),
                },
                "effective": {
                    "directories": sorted(dirs),
                    "files": sorted(files),
                    "extensions": sorted(exts),
                },
            }

        gitignore_info = {
            "enabled": self.respect_gitignore,
            "used": self.respect_gitignore and self.gitignore_spec is not None,
            "path": str(self.gitignore_path) if self.gitignore_path else None,
        }
        if exclusion_summary is not None:
            exclusion_summary["gitignore"] = gitignore_info

        save_phase_outputs(
            self.directory,
            analysis_data,
            rules_filename,
            include_phase_files=include_phase_outputs,
            exclusion_summary=exclusion_summary,
            gitignore_spec=self.gitignore_spec,
            gitignore_info=gitignore_info,
        )

        if should_generate_cursorignore():
            success, message = create_cursorignore(str(self.directory))
            if success:
                self.console.print(f"[green]{message}[/]")
            else:
                self.console.print(f"[yellow]{message}[/]")
        else:
            self.console.print("[dim]Skipped .cursorignore generation (disabled in settings).[/]")

        success, message = clean_cursorrules(str(self.directory), filename=rules_filename)
        if success:
            self.console.print("[green]Cleaned cursor rules file: removed text before 'You are...'[/]")
        else:
            self.console.print(f"[yellow]{message}[/]")

        if include_phase_outputs:
            self.console.print(
                f"[green]Individual phase outputs saved to:[/] {self.directory}/phases_output/"
            )
        self.console.print(
            f"[green]Cursor rules created at:[/] {self.directory}/{rules_filename}"
        )
        self.console.print(
            f"[green]Cursor ignore created at:[/] {self.directory}/.cursorignore"
        )
        if include_phase_outputs:
            self.console.print(
                f"[green]Execution metrics saved to:[/] {self.directory}/phases_output/metrics.md"
            )
        else:
            self.console.print("[dim]Skipped phase report archive (disabled in settings).[/]")

        if exclusion_summary:
            added_total = sum(len(items) for items in exclusion_summary["added"].values())
            removed_total = sum(len(items) for items in exclusion_summary["removed"].values())
            details: list[str] = []
            if added_total:
                details.append(f"added {added_total} rule{'s' if added_total != 1 else ''}")
            if removed_total:
                details.append(f"removed {removed_total} default{'s' if removed_total != 1 else ''}")
            detail_text = ", ".join(details) if details else "custom overrides active"
            self.console.print(f"[dim]Exclusion overrides applied ({detail_text}).[/]")
        if self.respect_gitignore:
            if self.gitignore_spec is not None:
                if self.gitignore_path:
                    self.console.print(f"[dim]Applied .gitignore patterns from {self.gitignore_path}.[/]")
                else:
                    self.console.print("[dim]Applied project .gitignore patterns.[/]")
            else:
                self.console.print("[dim].gitignore respected but no file found in project root.[/]")
        else:
            self.console.print("[dim]Ignoring .gitignore patterns (disabled in settings).[/]")


def run_analysis(directory: Path, console: Console | None = None) -> str:
    analyzer = ProjectAnalyzer(directory, console)
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(analyzer.analyze())
    finally:
        loop.close()


def _strip_tree_delimiters(tree_with_delimiters: list[str]) -> list[str]:
    has_wrapping_tags = (
        len(tree_with_delimiters) >= 2
        and tree_with_delimiters[0] == "<project_structure>"
        and tree_with_delimiters[-1] == "</project_structure>"
    )
    if has_wrapping_tags:
        return tree_with_delimiters[1:-1]
    return tree_with_delimiters
