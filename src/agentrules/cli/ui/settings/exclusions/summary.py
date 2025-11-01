"""Rendering helpers for exclusion settings."""

from __future__ import annotations

from rich.table import Table

from agentrules.cli.context import CliContext
from agentrules.cli.services import configuration


def render_exclusion_summary(context: CliContext) -> dict:
    """Render a Rich table summarizing current exclusion rules."""

    data = configuration.get_exclusion_settings()
    overrides = data["overrides"]
    effective = data["effective"]

    console = context.console
    console.print("\n[bold]Current exclusion rules[/bold]")
    respect_label = "[green]ON[/]" if overrides.respect_gitignore else "[red]OFF[/]"
    console.print(f"[cyan]Respect .gitignore:[/] {respect_label}\n")

    table = Table(show_header=True, header_style="bold cyan", pad_edge=False)
    table.add_column("Directories", overflow="fold")
    table.add_column("Files", overflow="fold")
    table.add_column("Extensions", overflow="fold")

    def _format_value(kind: str, value: str) -> str:
        additions = getattr(overrides, f"add_{kind}")
        if value in additions:
            return f"[green]{value}[/]"
        return f"[dim]{value}[/]"

    columns = {
        "directories": [_format_value("directories", v) for v in effective["directories"]],
        "files": [_format_value("files", v) for v in effective["files"]],
        "extensions": [_format_value("extensions", v) for v in effective["extensions"]],
    }

    max_len = max((len(values) for values in columns.values()), default=0)
    if max_len == 0:
        table.add_row("[dim]None[/]", "[dim]None[/]", "[dim]None[/]")
    else:
        keys = ("directories", "files", "extensions")
        for idx in range(max_len):
            row = [columns[key][idx] if idx < len(columns[key]) else "" for key in keys]
            table.add_row(*row)

    console.print(table)

    tree_depth = configuration.get_tree_traversal_depth()
    if overrides.tree_max_depth is None:
        console.print(f"[dim]Tree traversal depth:[/] {tree_depth}")
    else:
        console.print(f"[green]Tree traversal depth:[/] {tree_depth} (custom override)")

    added_summary: list[str] = []
    removed_summary: list[str] = []

    if overrides.add_directories or overrides.add_files or overrides.add_extensions:
        if overrides.add_directories:
            added_summary.append(f"directories (+ {len(overrides.add_directories)})")
        if overrides.add_files:
            added_summary.append(f"files (+ {len(overrides.add_files)})")
        if overrides.add_extensions:
            added_summary.append(f"extensions (+ {len(overrides.add_extensions)})")
    if overrides.remove_directories or overrides.remove_files or overrides.remove_extensions:
        if overrides.remove_directories:
            removed_summary.append(f"directories (− {len(overrides.remove_directories)})")
        if overrides.remove_files:
            removed_summary.append(f"files (− {len(overrides.remove_files)})")
        if overrides.remove_extensions:
            removed_summary.append(f"extensions (− {len(overrides.remove_extensions)})")

    if added_summary:
        console.print(f"[green]Custom additions:[/] {', '.join(added_summary)}")
    if removed_summary:
        console.print(f"[red]Removed defaults:[/] {', '.join(removed_summary)}")

    return data
