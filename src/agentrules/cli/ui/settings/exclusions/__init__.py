"""Interactive flow for managing exclusion rules."""

from __future__ import annotations

import questionary

from agentrules.cli.context import CliContext
from agentrules.cli.services import configuration
from agentrules.cli.ui.styles import CLI_STYLE, navigation_choice, toggle_choice

from .editor import prompt_exclusion_value
from .preview import preview_filtered_tree
from .summary import render_exclusion_summary


def configure_exclusions(context: CliContext) -> None:
    """Interactive prompts for adjusting exclusion rules."""

    console = context.console
    console.print("\n[bold]Configure exclusion rules[/bold]")
    console.print(
        "Adjust which files and directories are sent to the agents. Defaults stay intact unless overridden.\n"
    )

    while True:
        render_exclusion_summary(context)

        current_gitignore = configuration.is_gitignore_respected()

        category = questionary.select(
            "Choose exclusion category:",
            choices=[
                questionary.Choice(title="Directories", value="directories"),
                questionary.Choice(title="Files", value="files"),
                questionary.Choice(title="Extensions", value="extensions"),
                questionary.Choice(title="Tree traversal depth", value="__TREE_DEPTH__"),
                questionary.Choice(title="Preview filtered tree", value="__PREVIEW__"),
                toggle_choice(
                    "Respect .gitignore",
                    current_gitignore,
                    value="__TOGGLE_GITIGNORE__",
                ),
                navigation_choice("Reset to defaults", value="__RESET__"),
                navigation_choice("Back", value="__BACK__"),
            ],
            qmark="🚫",
            style=CLI_STYLE,
        ).ask()

        if category in (None, "__BACK__"):
            console.print("[dim]Leaving exclusion settings.[/]")
            return

        if category == "__TOGGLE_GITIGNORE__":
            configuration.save_respect_gitignore(not current_gitignore)
            status_text = "enabled" if not current_gitignore else "disabled"
            console.print(f"[green].gitignore handling {status_text}.[/]")
            continue
        if category == "__TREE_DEPTH__":
            _configure_tree_depth(context)
            continue
        if category == "__PREVIEW__":
            preview_filtered_tree(context)
            continue

        if category == "__RESET__":
            configuration.reset_custom_exclusions()
            console.print("[green]Exclusions reset to defaults.[/]")
            continue

        action = questionary.select(
            f"Modify {category}:",
            choices=[
                questionary.Choice(title="Add", value="add"),
                questionary.Choice(title="Remove", value="remove"),
                navigation_choice("Cancel", value="__CANCEL__"),
            ],
            qmark="➕" if category != "extensions" else "🔣",
            style=CLI_STYLE,
        ).ask()

        if action in (None, "__CANCEL__"):
            console.print("[yellow]No changes made.[/]")
            continue

        value = prompt_exclusion_value(category)
        if not value:
            console.print("[yellow]No changes made.[/]")
            continue

        effective_key = {
            "directories": "directories",
            "files": "files",
            "extensions": "extensions",
        }[category]

        if action == "add":
            normalized = configuration.add_custom_exclusion(category, value)
            if not normalized:
                console.print("[yellow]Value was not added. Ensure it is formatted correctly.[/]")
                continue
            latest = configuration.get_exclusion_settings()
            effective_values = latest["effective"][effective_key]
            if normalized in effective_values:
                console.print(f"[green]'{normalized}' will be excluded from analysis.[/]")
            else:
                console.print(f"[yellow]No change detected for '{normalized}'.[/]")
        elif action == "remove":
            normalized = configuration.remove_custom_exclusion(category, value)
            if not normalized:
                console.print("[yellow]Value was not updated. Ensure it is formatted correctly.[/]")
                continue
            latest = configuration.get_exclusion_settings()
            effective_values = latest["effective"][effective_key]
            if normalized in effective_values:
                console.print(f"[yellow]'{normalized}' remains excluded (already default).[/]")
            else:
                console.print(f"[green]'{normalized}' will no longer be excluded.[/]")


def _configure_tree_depth(context: CliContext) -> None:
    console = context.console
    current_depth = configuration.get_tree_traversal_depth()
    overrides = configuration.get_exclusion_settings()["overrides"]
    prompt_default = str(overrides.tree_max_depth or current_depth)

    answer = questionary.text(
        "Enter maximum tree depth (positive integer). Type 'reset' to restore default.",
        default=prompt_default,
        qmark="🌳",
        style=CLI_STYLE,
    ).ask()

    if answer is None:
        console.print("[yellow]No changes made.[/]")
        return

    trimmed = answer.strip().lower()
    if not trimmed:
        console.print("[yellow]No changes made.[/]")
        return

    if trimmed in {"reset", "default"}:
        configuration.reset_tree_traversal_depth()
        console.print("[green]Tree traversal depth reset to default.[/]")
        return

    try:
        depth_value = int(trimmed)
    except ValueError:
        console.print("[red]Depth must be a whole number of 1 or greater.[/]")
        return

    if depth_value < 1:
        console.print("[red]Depth must be at least 1.[/]")
        return

    configuration.save_tree_traversal_depth(depth_value)
    console.print(f"[green]Tree traversal depth set to {depth_value}.[/]")
