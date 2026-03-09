"""Persistence helpers for analysis pipeline outputs."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from agentrules.core.pipeline.config import PipelineResult, PipelineSettings
from agentrules.core.utils.file_creation.agent_scaffold import create_agent_scaffold
from agentrules.core.utils.file_creation.cursorignore import create_cursorignore
from agentrules.core.utils.file_creation.phases_output import save_phase_outputs
from agentrules.core.utils.file_creation.snapshot_artifact import sync_snapshot_artifact
from agentrules.core.utils.file_creation.snapshot_policy import build_snapshot_additional_exclude_paths
from agentrules.core.utils.formatters.clean_agentrules import clean_agentrules, ensure_execplans_guidance

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineOutputOptions:
    """Runtime flags that control which artifacts get materialized."""

    rules_filename: str
    rules_tree_max_depth: int
    snapshot_filename: str
    generate_phase_outputs: bool
    generate_cursorignore: bool
    generate_agent_scaffold: bool
    generate_snapshot: bool


@dataclass
class PipelineOutputSummary:
    """Aggregated status messages produced while persisting pipeline outputs."""

    messages: list[str]


class PipelineOutputWriter:
    """Persist pipeline artifacts to disk and report status messages."""

    def persist(
        self,
        result: PipelineResult,
        settings: PipelineSettings,
        options: PipelineOutputOptions,
    ) -> PipelineOutputSummary:
        """Materialize pipeline outputs and return console-friendly messages."""

        analysis_data = {
            "phase1": result.phase1,
            "phase2": result.phase2,
            "phase3": result.phase3,
            "phase4": result.phase4,
            "consolidated_report": result.consolidated_report,
            "final_analysis": result.final_analysis,
            "metrics": {"time": result.metrics.elapsed_seconds},
        }

        exclusion_summary = self._build_exclusion_summary(settings)
        gitignore_info = {
            "enabled": settings.respect_gitignore,
            "used": settings.respect_gitignore and result.snapshot.gitignore.spec is not None,
            "path": str(result.snapshot.gitignore.path) if result.snapshot.gitignore.path else None,
        }
        if exclusion_summary is not None:
            exclusion_summary["gitignore"] = gitignore_info

        cursorignore_messages: list[str] = []
        if options.generate_cursorignore:
            try:
                success, message = create_cursorignore(str(settings.target_directory))
            except Exception as error:
                logger.warning(
                    "Cursor ignore generation failed for %s: %s",
                    settings.target_directory,
                    error,
                    exc_info=True,
                )
                cursorignore_messages.append(f"[yellow]Cursor ignore generation failed:[/] {error}")
            else:
                if success:
                    cursorignore_messages.append(f"[green]{message}[/]")
                    cursorignore_messages.append(
                        f"[green]Cursor ignore created at:[/] {settings.target_directory / '.cursorignore'}"
                    )
                else:
                    cursorignore_messages.append(f"[yellow]{message}[/]")
        else:
            cursorignore_messages.append("[dim]Skipped .cursorignore generation (disabled in settings).[/]")

        agent_scaffold_messages: list[str] = []
        if options.generate_agent_scaffold:
            try:
                success, scaffold_messages = create_agent_scaffold(settings.target_directory)
            except Exception as error:
                logger.warning(
                    "Agent scaffold generation failed for %s: %s",
                    settings.target_directory,
                    error,
                    exc_info=True,
                )
                agent_scaffold_messages.append(f"[yellow]Agent scaffold generation failed:[/] {error}")
            else:
                if success:
                    for scaffold_message in scaffold_messages:
                        style = "dim" if scaffold_message.startswith("Skipped ") else "green"
                        agent_scaffold_messages.append(f"[{style}]{scaffold_message}[/]")
                else:
                    for scaffold_message in scaffold_messages:
                        agent_scaffold_messages.append(f"[yellow]{scaffold_message}[/]")
        else:
            agent_scaffold_messages.append("[dim]Skipped .agent scaffold generation (disabled in settings).[/]")

        snapshot_reference_filename: str | None = None
        snapshot_messages: list[str] = []
        snapshot_output_path = settings.target_directory / options.snapshot_filename
        if options.generate_snapshot:
            try:
                snapshot_result = sync_snapshot_artifact(
                    settings.target_directory,
                    output_path=snapshot_output_path,
                    tree_max_depth=None,
                    exclude_dirs=set(settings.effective_exclusions.directories),
                    exclude_files=set(settings.effective_exclusions.files),
                    exclude_extensions=set(settings.effective_exclusions.extensions),
                    gitignore_spec=result.snapshot.gitignore.spec,
                    additional_exclude_relative_paths=build_snapshot_additional_exclude_paths(
                        options.rules_filename,
                        options.snapshot_filename,
                    ),
                    write=True,
                )
            except Exception as error:
                logger.warning(
                    "Snapshot artifact generation failed for %s: %s",
                    settings.target_directory,
                    error,
                    exc_info=True,
                )
                if snapshot_output_path.is_file():
                    snapshot_reference_filename = options.snapshot_filename
                snapshot_messages.append(f"[yellow]Snapshot artifact generation failed:[/] {error}")
            else:
                snapshot_reference_filename = options.snapshot_filename
                if snapshot_result.changed:
                    snapshot_messages.append(
                        "[green]Snapshot artifact written to:[/] "
                        f"{snapshot_result.output_path} "
                        f"([green]+{len(snapshot_result.added_paths)}[/], "
                        f"[red]-{len(snapshot_result.removed_paths)}[/], "
                        f"{snapshot_result.preserved_comments} comments preserved)"
                    )
                else:
                    snapshot_messages.append(
                        f"[dim]Snapshot artifact already up-to-date:[/] {snapshot_result.output_path}"
                    )
        else:
            snapshot_messages.append("[dim]Skipped snapshot artifact generation (disabled in settings).[/]")

        save_phase_outputs(
            settings.target_directory,
            analysis_data,
            options.rules_filename,
            include_phase_files=options.generate_phase_outputs,
            exclusion_summary=exclusion_summary,
            gitignore_spec=result.snapshot.gitignore.spec,
            gitignore_info=gitignore_info,
            tree_max_depth=settings.tree_max_depth,
            rules_tree_max_depth=options.rules_tree_max_depth,
            snapshot_reference_filename=snapshot_reference_filename,
        )

        messages: list[str] = []
        if options.generate_phase_outputs:
            messages.append(
                f"[green]Individual phase outputs saved to:[/] {settings.target_directory / 'phases_output'}"
            )
        else:
            messages.append("[dim]Skipped phase report archive (disabled in settings).[/]")

        rules_path = settings.target_directory / options.rules_filename
        messages.append(f"[green]Agent rules created at:[/] {rules_path}")
        messages.extend(cursorignore_messages)
        messages.extend(agent_scaffold_messages)
        messages.extend(snapshot_messages)

        success, message = clean_agentrules(
            str(settings.target_directory),
            filename=options.rules_filename,
        )
        if success:
            messages.append("[green]Cleaned Agent rules file: removed text before 'You are...'[/]")
        else:
            messages.append(f"[yellow]{message}[/]")

        success, message = ensure_execplans_guidance(
            str(settings.target_directory),
            filename=options.rules_filename,
        )
        if success:
            style = "dim" if "already present" in message.lower() else "green"
            messages.append(f"[{style}]{message}[/]")
        else:
            messages.append(f"[yellow]{message}[/]")

        if options.generate_phase_outputs:
            metrics_path = settings.target_directory / "phases_output" / "metrics.md"
            messages.append(f"[green]Execution metrics saved to:[/] {metrics_path}")

        if exclusion_summary:
            messages.append(self._format_exclusion_summary(exclusion_summary))

        messages.append(self._describe_gitignore(gitignore_info))

        return PipelineOutputSummary(messages=messages)

    def _build_exclusion_summary(self, settings: PipelineSettings) -> dict | None:
        overrides = settings.exclusion_overrides
        if overrides is None or overrides.is_empty():
            return None

        return {
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
                "directories": sorted(settings.effective_exclusions.directories),
                "files": sorted(settings.effective_exclusions.files),
                "extensions": sorted(settings.effective_exclusions.extensions),
            },
        }

    def _format_exclusion_summary(self, summary: dict) -> str:
        added_total = sum(len(items) for items in summary["added"].values())
        removed_total = sum(len(items) for items in summary["removed"].values())
        details: list[str] = []
        if added_total:
            details.append(f"added {added_total} rule{'s' if added_total != 1 else ''}")
        if removed_total:
            details.append(
                f"removed {removed_total} default{'s' if removed_total != 1 else ''}"
            )
        detail_text = ", ".join(details) if details else "custom overrides active"
        return f"[dim]Exclusion overrides applied ({detail_text}).[/]"

    def _describe_gitignore(self, info: dict) -> str:
        if not info.get("enabled", True):
            return "[dim]Ignoring .gitignore patterns (disabled in settings).[/]"
        if not info.get("used"):
            return "[dim].gitignore respected but no file found in project root.[/]"
        path = info.get("path")
        if path:
            return f"[dim]Applied .gitignore patterns from {path}.[/]"
        return "[dim]Applied project .gitignore patterns.[/]"
