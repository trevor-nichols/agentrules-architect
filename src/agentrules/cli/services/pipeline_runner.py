"""Utilities for executing the project analysis pipeline."""

from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from typing import Any

from agentrules.cli.ui.analysis_view import AnalysisView
from agentrules.cli.ui.event_sink import ViewEventSink
from agentrules.core.configuration import get_config_manager
from agentrules.core.pipeline import (
    EffectiveExclusions,
    PipelineMetrics,
    PipelineOutputOptions,
    PipelineOutputWriter,
    PipelineResult,
    PipelineSettings,
    build_project_snapshot,
    create_default_pipeline,
)

from ..context import CliContext
from .output_validation import validate_pipeline_output_filenames


def _activate_offline_mode(context: CliContext) -> None:
    if os.getenv("OFFLINE", "0") != "1":
        return

    try:
        from agentrules.core.utils.offline import patch_factory_offline

        patch_factory_offline()
        context.console.print("[yellow]OFFLINE=1 detected: using DummyArchitects (no network calls).[/]")
    except Exception as error:  # pragma: no cover - defensive logging
        context.console.print(f"[red]Failed to enable OFFLINE mode: {error}[/]")


def run_pipeline(
    path: Path,
    offline: bool,
    context: CliContext,
    *,
    rules_filename_override: str | None = None,
) -> bool:
    """Execute the analysis pipeline for the given path."""

    if offline:
        os.environ["OFFLINE"] = "1"

    _activate_offline_mode(context)

    config_manager = get_config_manager()
    resolved_rules_filename = config_manager.resolve_rules_filename(override=rules_filename_override)
    rules_tree_max_depth = config_manager.get_rules_tree_max_depth()
    snapshot_filename = config_manager.get_snapshot_filename()
    generate_snapshot = config_manager.should_generate_snapshot()
    generate_cursorignore = config_manager.should_generate_cursorignore()
    try:
        validate_pipeline_output_filenames(
            target_directory=path,
            rules_filename=resolved_rules_filename,
            snapshot_filename=snapshot_filename,
            generate_snapshot=generate_snapshot,
        )
    except ValueError as error:
        context.console.print(f"[red]Invalid output configuration:[/] {error}")
        context.console.print(
            f"[dim]Current values: rules={resolved_rules_filename}, snapshot={snapshot_filename}[/]"
        )
        return False

    exclusion_overrides = config_manager.get_exclusion_overrides()
    effective_dirs, effective_files, effective_exts = config_manager.get_effective_exclusions()
    settings = PipelineSettings(
        target_directory=path,
        tree_max_depth=config_manager.get_tree_max_depth(),
        respect_gitignore=config_manager.should_respect_gitignore(),
        effective_exclusions=EffectiveExclusions(
            directories=frozenset(effective_dirs),
            files=frozenset(effective_files),
            extensions=frozenset(effective_exts),
        ),
        exclusion_overrides=exclusion_overrides,
    )

    snapshot = build_project_snapshot(settings)

    researcher_enabled = config_manager.is_researcher_enabled()
    view = AnalysisView(context.console)
    event_sink = ViewEventSink(view)
    pipeline = create_default_pipeline(
        researcher_enabled=researcher_enabled,
        event_sink=event_sink,
    )

    async def _execute() -> PipelineResult:
        start_time = time.time()

        subtitle = "Assessing dependencies, research gaps, structure, and tech stack"
        view.render_phase_header("Phase 1 · Initial Discovery", "green", subtitle)
        agents_overview = ["Dependency Agent"]
        if researcher_enabled:
            agents_overview.append("Researcher Agent (optional)")
        agents_overview.extend(["Structure Agent", "Tech Stack Agent"])
        view.render_agent_overview(agents_overview, color="green")
        phase1_results = await view.run_with_spinner(
            "Running discovery agents...",
            "green",
            pipeline.run_phase1(snapshot),
        )
        view.render_completion("Discovery agents completed", "green")

        view.render_phase_header(
            "Phase 2 · Methodical Planning",
            "blue",
            "Designing a targeted analysis plan",
        )
        phase2_results = await view.run_with_spinner(
            "Creating analysis plan...",
            "blue",
            pipeline.run_phase2(phase1_results, snapshot),
        )
        raw_agents = phase2_results.get("agents")
        agent_plan: list[dict[str, Any]] = (
            [entry for entry in raw_agents if isinstance(entry, dict)]
            if isinstance(raw_agents, list)
            else []
        )
        view.render_completion("Analysis plan created", "blue")

        view.render_phase_header(
            "Phase 3 · Deep Analysis",
            "yellow",
            "Executing specialized agents across files",
        )
        if agent_plan:
            view.start_agent_progress("phase3", agent_plan, color="yellow")
        else:
            view.render_note("Specialized agents running on project files", style="dim")
        phase3_results = await view.run_with_spinner(
            "Analyzing files in depth...",
            "yellow",
            pipeline.run_phase3(phase2_results, settings, snapshot),
        )
        view.stop_agent_progress("phase3")
        view.render_completion("Deep analysis finished", "yellow")

        view.render_phase_header(
            "Phase 4 · Synthesis",
            "magenta",
            "Distilling findings into unified insights",
        )
        phase4_results = await view.run_with_spinner(
            "Synthesizing findings...",
            "magenta",
            pipeline.run_phase4(phase3_results),
        )
        view.render_completion("Findings synthesized", "magenta")

        view.render_phase_header(
            "Phase 5 · Consolidation",
            "cyan",
            "Assembling final multi-phase report",
        )
        all_results = {
            "phase1": phase1_results,
            "phase2": phase2_results,
            "phase3": phase3_results,
            "phase4": phase4_results,
        }
        consolidated_report = await view.run_with_spinner(
            "Consolidating results...",
            "cyan",
            pipeline.run_phase5(all_results),
        )
        view.render_completion("Results consolidated", "cyan")

        view.render_phase_header(
            "Final Analysis",
            "white",
            "Preparing Agent rules output",
        )
        final_analysis = await view.run_with_spinner(
            "Creating rules...",
            "white",
            pipeline.run_final(
                consolidated_report,
                snapshot,
                rules_filename=resolved_rules_filename,
            ),
        )
        view.render_completion("Agent rules ready", "white")

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

    try:
        result = asyncio.run(_execute())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(_execute())
        finally:
            loop.close()

    output_writer = PipelineOutputWriter()
    output_options = PipelineOutputOptions(
        rules_filename=resolved_rules_filename,
        rules_tree_max_depth=rules_tree_max_depth,
        snapshot_filename=snapshot_filename,
        generate_phase_outputs=config_manager.should_generate_phase_outputs(),
        generate_cursorignore=generate_cursorignore,
        generate_agent_scaffold=config_manager.should_generate_agent_scaffold(),
        generate_snapshot=generate_snapshot,
    )
    summary = output_writer.persist(result, settings, output_options)
    for message in summary.messages:
        context.console.print(message)

    context.console.print(f"\n[green]Analysis finished for:[/] {path}")
    return True
