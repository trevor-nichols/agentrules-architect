"""Implementation of the `analyze` subcommand."""

from __future__ import annotations

from pathlib import Path

import typer

from ..bootstrap import bootstrap_runtime
from ..services.pipeline_runner import run_pipeline

DEFAULT_ANALYZE_PATH = Path.cwd()
PATH_ARGUMENT = typer.Argument(
    DEFAULT_ANALYZE_PATH,
    exists=True,
    dir_okay=True,
    file_okay=False,
    resolve_path=True,
)


def _normalize_rules_filename_override(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    if not normalized:
        raise typer.BadParameter("Rules filename override cannot be empty.")
    if "/" in normalized or "\\" in normalized:
        raise typer.BadParameter("Rules filename override must be a file name, not a path.")
    return normalized


def register(app: typer.Typer) -> None:
    """Register the `analyze` subcommand with the provided Typer app."""

    @app.command()
    def analyze(  # type: ignore[func-returns-value]
        path: Path = PATH_ARGUMENT,
        offline: bool = typer.Option(False, "--offline", help="Run using offline dummy architects (no API calls)."),
        rules_filename: str | None = typer.Option(
            None,
            "--rules-filename",
            help="Override the output rules filename for this run (for example CLAUDE.md).",
        ),
    ) -> None:
        """Analyze a project directory and generate rules artifacts."""

        context = bootstrap_runtime()
        success = run_pipeline(
            path,
            offline,
            context,
            rules_filename_override=_normalize_rules_filename_override(rules_filename),
        )
        if not success:
            raise typer.Exit(2)
