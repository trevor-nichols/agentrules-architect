"""
Core orchestration logic for the CursorRules Architect analysis pipeline.

This module extracts the business workflow from the legacy ``main.py`` CLI so it
can be reused by both programmatic and Typer-based command-line interfaces.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from config.agents import MODEL_CONFIG
from config.exclusions import EXCLUDED_DIRS, EXCLUDED_EXTENSIONS, EXCLUDED_FILES
from core.analysis import (
    FinalAnalysis,
    Phase1Analysis,
    Phase2Analysis,
    Phase3Analysis,
    Phase4Analysis,
    Phase5Analysis,
)
from core.utils.file_creation.cursorignore import create_cursorignore
from core.utils.file_creation.phases_output import save_phase_outputs
from core.utils.formatters.clean_cursorrules import clean_cursorrules
from core.utils.model_config_helper import get_model_config_name
from core.utils.file_system.tree_generator import get_project_tree

logger = logging.getLogger("project_extractor")


class ProjectAnalyzer:
    """High-level coordinator for the six-phase analysis pipeline."""

    def __init__(self, directory: Path, console: Optional[Console] = None):
        self.directory = directory
        self.console = console or Console()

        self.phase1_results: Dict = {}
        self.phase2_results: Dict = {}
        self.phase3_results: Dict = {}
        self.phase4_results: Dict = {}
        self.consolidated_report: Dict = {}
        self.final_analysis: Dict = {}

        self.phase1_analyzer = Phase1Analysis()
        self.phase2_analyzer = Phase2Analysis()
        self.phase3_analyzer = Phase3Analysis()
        self.phase4_analyzer = Phase4Analysis()
        self.phase5_analyzer = Phase5Analysis()
        self.final_analyzer = FinalAnalysis()

    async def run_phase1(self, tree: List[str], package_info: Dict) -> Dict:
        return await self.phase1_analyzer.run(tree, package_info)

    async def run_phase2(self, phase1_results: Dict, tree: List[str]) -> Dict:
        return await self.phase2_analyzer.run(phase1_results, tree)

    async def run_phase3(self, analysis_plan: Dict, tree: List[str]) -> Dict:
        return await self.phase3_analyzer.run(analysis_plan, tree, self.directory)

    async def run_phase4(self, phase3_results: Dict) -> Dict:
        return await self.phase4_analyzer.run(phase3_results)

    async def run_phase5(self, all_results: Dict) -> Dict:
        return await self.phase5_analyzer.run(all_results)

    async def run_final_analysis(self, consolidated_report: Dict, tree: List[str] | None = None) -> Dict:
        return await self.final_analyzer.run(consolidated_report, tree)

    async def analyze(self) -> str:
        start_time = time.time()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            self.console.print("\n[bold green]Phase 1: Initial Discovery[/bold green]")
            self.console.print(
                "[dim]Running three concurrent agents: Structure Agent, Dependency Agent, and Tech Stack Agent...[/dim]"
            )

            task1 = progress.add_task("[green]Running analysis agents...", total=1)
            tree_with_delimiters = get_project_tree(self.directory)
            tree_for_analysis = _strip_tree_delimiters(tree_with_delimiters)

            package_info: Dict = {}
            self.phase1_results = await self.run_phase1(tree_for_analysis, package_info)

            progress.update(task1, completed=1)
            progress.stop_task(task1)
            progress.remove_task(task1)
            self.console.print("[green]✓[/green] Phase 1 complete: All three agents have finished their analysis")

            self.console.print("\n[bold blue]Phase 2: Methodical Planning[/bold blue]")
            self.console.print("[dim]Creating a detailed plan for deeper analysis...[/dim]")

            task2 = progress.add_task("[blue]Creating analysis plan...", total=1)
            self.phase2_results = await self.run_phase2(self.phase1_results, tree_for_analysis)

            progress.update(task2, completed=1)
            progress.stop_task(task2)
            progress.remove_task(task2)
            self.console.print("[blue]✓[/blue] Phase 2 complete: Analysis plan created")

            self.console.print("\n[bold yellow]Phase 3: Deep Analysis[/bold yellow]")

            agent_count = len(self.phase2_results.get("agents", []))
            if agent_count > 0:
                self.console.print(f"[dim]Running {agent_count} specialized analysis agents on their assigned files...[/dim]")
            else:
                self.console.print("[dim]Running specialized analysis on project files...[/dim]")

            task3 = progress.add_task("[yellow]Analyzing files in depth...", total=1)
            self.phase3_results = await self.run_phase3(self.phase2_results, tree_for_analysis)

            progress.update(task3, completed=1)
            progress.stop_task(task3)
            progress.remove_task(task3)
            self.console.print("[yellow]✓[/yellow] Phase 3 complete: In-depth analysis finished")

            self.console.print("\n[bold magenta]Phase 4: Synthesis[/bold magenta]")
            self.console.print("[dim]Synthesizing findings from all previous analyses...[/dim]")

            task4 = progress.add_task("[magenta]Synthesizing findings...", total=1)
            self.phase4_results = await self.run_phase4(self.phase3_results)

            progress.update(task4, completed=1)
            progress.stop_task(task4)
            progress.remove_task(task4)
            self.console.print("[magenta]✓[/magenta] Phase 4 complete: Findings synthesized")

            self.console.print("\n[bold cyan]Phase 5: Consolidation[/bold cyan]")
            self.console.print("[dim]Consolidating all results into a comprehensive report...[/dim]")

            task5 = progress.add_task("[cyan]Consolidating results...", total=1)
            all_results = {
                "phase1": self.phase1_results,
                "phase2": self.phase2_results,
                "phase3": self.phase3_results,
                "phase4": self.phase4_results,
            }
            self.consolidated_report = await self.run_phase5(all_results)

            progress.update(task5, completed=1)
            progress.stop_task(task5)
            progress.remove_task(task5)
            self.console.print("[cyan]✓[/cyan] Phase 5 complete: Results consolidated")

            self.console.print("\n[bold white]Final Analysis[/bold white]")
            self.console.print("[dim]Creating final analysis for Cursor IDE...[/dim]")

            task6 = progress.add_task("[white]Creating rules...", total=1)
            self.final_analysis = await self.run_final_analysis(self.consolidated_report, tree_for_analysis)

            progress.update(task6, completed=1)
            progress.stop_task(task6)
            progress.remove_task(task6)
            self.console.print("[white]✓[/white] Final Analysis complete: Cursor rules created")

        analysis_lines: List[str] = [
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
                f"Time taken: {time.time() - start_time:.2f} seconds",
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

        save_phase_outputs(self.directory, analysis_data)

        success, message = create_cursorignore(str(self.directory))
        if success:
            self.console.print(f"[green]{message}[/]")
        else:
            self.console.print(f"[yellow]{message}[/]")

        success, message = clean_cursorrules(str(self.directory))
        if success:
            self.console.print("[green]Cleaned cursor rules file: removed text before 'You are...'[/]")
        else:
            self.console.print(f"[yellow]{message}[/]")

        self.console.print(f"[green]Individual phase outputs saved to:[/] {self.directory}/phases_output/")
        self.console.print(f"[green]Cursor rules created at:[/] {self.directory}/.cursorrules")
        self.console.print(f"[green]Cursor ignore created at:[/] {self.directory}/.cursorignore")
        self.console.print(f"[green]Execution metrics saved to:[/] {self.directory}/phases_output/metrics.md")


def run_analysis(directory: Path, console: Optional[Console] = None) -> str:
    analyzer = ProjectAnalyzer(directory, console)
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(analyzer.analyze())
    finally:
        loop.close()


def _strip_tree_delimiters(tree_with_delimiters: List[str]) -> List[str]:
    if len(tree_with_delimiters) >= 2 and tree_with_delimiters[0] == "<project_structure>" and tree_with_delimiters[-1] == "</project_structure>":
        return tree_with_delimiters[1:-1]
    return tree_with_delimiters

