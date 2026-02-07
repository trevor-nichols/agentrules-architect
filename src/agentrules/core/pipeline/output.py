"""Persistence helpers for analysis pipeline outputs."""

from __future__ import annotations

from dataclasses import dataclass

from agentrules.core.pipeline.config import PipelineResult, PipelineSettings
from agentrules.core.utils.file_creation.agent_scaffold import create_agent_scaffold
from agentrules.core.utils.file_creation.cursorignore import create_cursorignore
from agentrules.core.utils.file_creation.phases_output import save_phase_outputs
from agentrules.core.utils.formatters.clean_agentrules import clean_agentrules, ensure_execplans_guidance


@dataclass(frozen=True)
class PipelineOutputOptions:
    """Runtime flags that control which artifacts get materialized."""

    rules_filename: str
    generate_phase_outputs: bool
    generate_cursorignore: bool
    generate_agent_scaffold: bool


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

        save_phase_outputs(
            settings.target_directory,
            analysis_data,
            options.rules_filename,
            include_phase_files=options.generate_phase_outputs,
            exclusion_summary=exclusion_summary,
            gitignore_spec=result.snapshot.gitignore.spec,
            gitignore_info=gitignore_info,
            tree_max_depth=settings.tree_max_depth,
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

        if options.generate_cursorignore:
            success, message = create_cursorignore(str(settings.target_directory))
            if success:
                messages.append(f"[green]{message}[/]")
                messages.append(
                    f"[green]Cursor ignore created at:[/] {settings.target_directory / '.cursorignore'}"
                )
            else:
                messages.append(f"[yellow]{message}[/]")
        else:
            messages.append("[dim]Skipped .cursorignore generation (disabled in settings).[/]")

        if options.generate_agent_scaffold:
            success, scaffold_messages = create_agent_scaffold(settings.target_directory)
            if success:
                for scaffold_message in scaffold_messages:
                    style = "dim" if scaffold_message.startswith("Skipped ") else "green"
                    messages.append(f"[{style}]{scaffold_message}[/]")
            else:
                for scaffold_message in scaffold_messages:
                    messages.append(f"[yellow]{scaffold_message}[/]")
        else:
            messages.append("[dim]Skipped .agent scaffold generation (disabled in settings).[/]")

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
