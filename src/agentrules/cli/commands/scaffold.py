"""Implementation of the `scaffold` command group."""

from __future__ import annotations

from pathlib import Path

import typer

from agentrules.core.utils.file_creation.agent_scaffold import sync_agent_scaffold

from ..bootstrap import bootstrap_runtime

ROOT_OPTION = typer.Option(
    None,
    "--root",
    help="Repository root directory. Defaults to current working directory.",
)
CHECK_OPTION = typer.Option(
    False,
    "--check",
    help="Validate scaffold templates without writing files. Exits non-zero on drift.",
)
FORCE_OPTION = typer.Option(
    False,
    "--force",
    help="Overwrite outdated scaffold templates and create timestamped .bak backups.",
)


def register(app: typer.Typer) -> None:
    """Register the `scaffold` command group."""

    scaffold_app = typer.Typer(help="Manage ExecPlan scaffold templates (.exec_plans/PLANS.md and templates/).")
    app.add_typer(scaffold_app, name="scaffold")

    @scaffold_app.command("sync")
    def sync(  # type: ignore[func-returns-value]
        root: Path | None = ROOT_OPTION,
        check: bool = CHECK_OPTION,
        force: bool = FORCE_OPTION,
    ) -> None:
        context = bootstrap_runtime()
        console = context.console

        if check and force:
            raise typer.BadParameter("Choose either --check or --force, not both.")

        target_directory = (root or Path.cwd()).resolve()

        try:
            result = sync_agent_scaffold(
                target_directory,
                check=check,
                force=force,
            )
        except (FileNotFoundError, NotADirectoryError, ValueError, OSError) as error:
            console.print(f"[red]Scaffold sync failed: {error}[/]")
            raise typer.Exit(2) from error

        for message in result.messages:
            normalized = message.lower()
            if normalized.startswith("up-to-date"):
                style = "dim"
            elif normalized.startswith("missing") or normalized.startswith("outdated"):
                style = "yellow"
            else:
                style = "green"
            console.print(f"[{style}]{message}[/]")

        if check:
            if result.ok:
                console.print("[green]Scaffold templates are up-to-date.[/]")
                raise typer.Exit(0)
            console.print("[yellow]Scaffold templates are missing or outdated.[/]")
            raise typer.Exit(1)

        console.print("[green]Scaffold sync complete.[/]")
        raise typer.Exit(0)
