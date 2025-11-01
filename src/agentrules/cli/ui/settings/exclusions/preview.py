"""Interactive tree preview for exclusion settings."""

from __future__ import annotations

from pathlib import Path

import questionary

from agentrules.cli.context import CliContext
from agentrules.cli.services import configuration
from agentrules.cli.services.tree_preview import export_tree_to_path, generate_tree_snapshot
from agentrules.cli.ui.styles import CLI_STYLE

_DEFAULT_PREVIEW_LIMIT = 120


def preview_filtered_tree(context: CliContext) -> None:
    """Show a filtered project tree based on current exclusion settings."""

    console = context.console

    path_answer = questionary.path(
        "Project directory to preview:",
        default=str(Path.cwd()),
        only_directories=True,
        style=CLI_STYLE,
    ).ask()

    if not path_answer:
        console.print("[yellow]Cancelled preview.[/]")
        return

    directory = Path(path_answer).expanduser().resolve()
    if not directory.exists() or not directory.is_dir():
        console.print(f"[red]Invalid directory: {directory}[/]")
        return

    current_depth = configuration.get_tree_traversal_depth()

    depth_answer = questionary.text(
        "Maximum depth to traverse:",
        default=str(current_depth),
        style=CLI_STYLE,
        validate=lambda text: (
            not text.strip()
            or (text.strip().isdigit() and int(text.strip()) > 0)
        ),
    ).ask()

    if depth_answer is None:
        console.print("[yellow]Cancelled preview.[/]")
        return

    trimmed_depth = depth_answer.strip()
    if not trimmed_depth:
        max_depth = current_depth
    else:
        max_depth = int(trimmed_depth)

    try:
        snapshot = generate_tree_snapshot(directory, max_depth=max_depth)
    except Exception as error:  # pragma: no cover - defensive logging for CLI use
        console.print(f"[red]Failed to generate tree: {error}[/]")
        return

    preview_lines = snapshot.as_preview(_DEFAULT_PREVIEW_LIMIT)
    total_lines = len(snapshot.lines)
    shown_lines = len(preview_lines)

    console.print("\n[bold]Filtered project tree preview[/bold]")
    console.print(f"[dim]Directory:[/] {directory}")
    console.print(f"[dim]Traversal depth:[/] {snapshot.max_depth}")

    if preview_lines:
        console.print("```")
        console.print("\n".join(preview_lines))
        console.print("```")
    else:
        console.print("[dim]No entries after applying exclusions.[/]")

    if total_lines > shown_lines:
        console.print(
            f"[yellow]Preview truncated to {_DEFAULT_PREVIEW_LIMIT} lines. Export for full tree.[/]"
        )

    if snapshot.respect_gitignore:
        if snapshot.gitignore_used:
            note = (
                f".gitignore patterns applied from {snapshot.gitignore_path}"
                if snapshot.gitignore_path
                else ".gitignore respected with detected patterns."
            )
        else:
            note = ".gitignore respected but no patterns detected."
    else:
        note = ".gitignore handling disabled in settings."

    console.print(f"[dim]{note}[/]")

    save_confirm = questionary.confirm(
        "Save full tree to Markdown?",
        default=False,
        style=CLI_STYLE,
    ).ask()

    if not save_confirm:
        return

    default_filename = directory / "project_structure.md"
    file_answer = questionary.text(
        "Output file path:",
        default=str(default_filename),
        style=CLI_STYLE,
        validate=lambda text: bool(text.strip()),
    ).ask()

    if not file_answer:
        console.print("[yellow]Export cancelled.[/]")
        return

    output_path = Path(file_answer).expanduser()

    try:
        exported_path = export_tree_to_path(snapshot.lines, output_path)
    except Exception as error:  # pragma: no cover - defensive logging for CLI use
        console.print(f"[red]Failed to write tree file: {error}[/]")
        return

    console.print(f"[green]Tree exported to:[/] {exported_path}")
