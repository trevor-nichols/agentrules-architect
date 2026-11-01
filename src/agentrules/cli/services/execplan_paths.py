"""Resolve ExecPlan workspace paths for CLI commands."""

from __future__ import annotations

from pathlib import Path

import typer

from agentrules.core.execplan.layout import (
    CURRENT_LAYOUT,
    LEGACY_LAYOUT,
    MIGRATE_COMMAND,
    AmbiguousExecPlanLayoutError,
    ResolvedExecPlanPaths,
    resolve_execplan_paths,
)

from ..context import CliContext


def resolve_cli_execplan_paths(
    context: CliContext,
    *,
    root: Path,
    execplans_dir: Path | None,
    registry_path: Path | None = None,
) -> ResolvedExecPlanPaths:
    """Resolve paths for a command, exiting with code 2 when the workspace is ambiguous."""

    try:
        paths = resolve_execplan_paths(root, execplans_dir=execplans_dir, registry_path=registry_path)
    except AmbiguousExecPlanLayoutError as error:
        context.console.print(f"[red]{error}[/]")
        raise typer.Exit(2) from error

    if paths.layout.is_legacy:
        context.console.print(
            f"[yellow]Using legacy {LEGACY_LAYOUT.execplans_dir.as_posix()} layout. "
            f"Run `{MIGRATE_COMMAND}` to move it to {CURRENT_LAYOUT.workspace_dir.as_posix()}/.[/]"
        )
    return paths
