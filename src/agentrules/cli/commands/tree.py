"""Implementation of the `tree` subcommand."""

from __future__ import annotations

from pathlib import Path

import typer

from ..bootstrap import bootstrap_runtime
from ..services.tree_preview import export_tree_to_path, generate_tree_snapshot

DEFAULT_PATH = Path.cwd()

def _validate_positive(ctx: typer.Context, param: typer.CallbackParam, value: int | None) -> int | None:
    if value is None:
        return None
    if value < 1:
        raise typer.BadParameter("must be greater than zero", ctx=ctx, param=param)
    return value


PATH_ARGUMENT = typer.Argument(
    DEFAULT_PATH,
    exists=True,
    dir_okay=True,
    file_okay=False,
    resolve_path=True,
)

MAX_DEPTH_OPTION = typer.Option(
    None,
    "--max-depth",
    "-d",
    help="Maximum directory depth to traverse.",
    callback=_validate_positive,
)

PREVIEW_LINES_OPTION = typer.Option(
    None,
    "--preview-lines",
    "-n",
    help="Limit the number of lines shown in the console preview.",
    callback=_validate_positive,
)

SAVE_OPTION = typer.Option(
    None,
    "--save",
    "-o",
    help=(
        "Optional path to export the full tree (Markdown). Relative paths resolve inside the target directory."
    ),
)


def register(app: typer.Typer) -> None:
    """Register the `tree` subcommand with the provided Typer app."""

    @app.command()
    def tree(  # type: ignore[func-returns-value]
        path: Path = PATH_ARGUMENT,
        max_depth: int = MAX_DEPTH_OPTION,
        preview_lines: int | None = PREVIEW_LINES_OPTION,
        save: Path | None = SAVE_OPTION,
    ) -> None:
        """Show the exclusion-aware project tree and optionally save it to disk."""

        context = bootstrap_runtime()
        console = context.console

        snapshot = generate_tree_snapshot(path, max_depth=max_depth)

        tree_lines = snapshot.as_preview(preview_lines)
        total_lines = len(snapshot.lines)
        shown_lines = len(tree_lines)

        console.print(f"[bold]Filtered project tree for:[/] {path}")
        console.print(f"[dim]Traversal depth:[/] {snapshot.max_depth}")
        if preview_lines is not None and total_lines > shown_lines:
            console.print(
                f"[yellow]Showing first {shown_lines - 1 if shown_lines else 0} of {total_lines} lines (truncated).[/]"
            )
        else:
            console.print(f"[dim]Total lines: {total_lines}[/]")

        if tree_lines:
            console.print("```")
            console.print("\n".join(tree_lines))
            console.print("```")
        else:
            console.print("[dim]No entries after applying exclusions.[/]")

        if snapshot.respect_gitignore:
            if snapshot.gitignore_used:
                if snapshot.gitignore_path:
                    console.print(f"[dim].gitignore patterns applied from {snapshot.gitignore_path}.[/]")
                else:
                    console.print("[dim].gitignore respected but no file found at project root.[/]")
            else:
                console.print("[dim].gitignore respected but no patterns detected.[/]")
        else:
            console.print("[dim].gitignore handling disabled in settings.[/]")

        if save is not None:
            output_path = save if save.is_absolute() else path / save
            exported = export_tree_to_path(snapshot.lines, output_path)
            console.print(f"[green]Full tree exported to:[/] {exported}")
        elif preview_lines is not None and total_lines > shown_lines:
            console.print("[dim]Use --save to export the full tree to Markdown.[/]")
