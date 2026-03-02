"""Output generation preferences flow."""

from __future__ import annotations

import questionary

from agentrules.cli.context import CliContext
from agentrules.cli.services import configuration
from agentrules.cli.services.output_validation import (
    validate_snapshot_filename_distinct,
    validate_snapshot_filename_reserved,
)
from agentrules.cli.ui.styles import CLI_STYLE, navigation_choice, toggle_choice, value_choice


def _normalize_filename_input(text: str) -> str:
    candidate = text.strip()
    if not candidate:
        raise ValueError("File name is required.")
    if "/" in candidate or "\\" in candidate:
        raise ValueError("Must be a file name, not a path.")
    return candidate


def _validate_rules_filename_input(text: str, *, snapshot_filename: str) -> bool | str:
    try:
        candidate = _normalize_filename_input(text)
        validate_snapshot_filename_distinct(
            rules_filename=candidate,
            snapshot_filename=snapshot_filename,
        )
    except ValueError as error:
        return str(error)
    return True


def _validate_snapshot_filename_input(text: str, *, rules_filename: str) -> bool | str:
    try:
        candidate = _normalize_filename_input(text)
        validate_snapshot_filename_reserved(candidate)
        validate_snapshot_filename_distinct(
            rules_filename=rules_filename,
            snapshot_filename=candidate,
        )
    except ValueError as error:
        return str(error)
    return True


def configure_output_preferences(context: CliContext) -> None:
    """Interactive prompts for toggling generated artifacts."""

    console = context.console
    console.print("\n[bold]Configure output preferences[/bold]")
    console.print("[dim]Toggle generated artifacts after each analysis run.[/dim]\n")

    while True:
        preferences = configuration.get_output_preferences()
        rules_filename = configuration.get_rules_file_name()
        snapshot_filename = configuration.get_snapshot_file_name()
        selection = questionary.select(
            "Select preference to toggle:",
            choices=[
                toggle_choice(
                    "Generate .cursorignore after analysis",
                    preferences.generate_cursorignore,
                    value="__TOGGLE_CURSORIGNORE__",
                ),
                toggle_choice(
                    "Generate .agent planning scaffold after analysis",
                    preferences.generate_agent_scaffold,
                    value="__TOGGLE_AGENT_SCAFFOLD__",
                ),
                toggle_choice(
                    "Write per-phase reports to phases_output/",
                    preferences.generate_phase_outputs,
                    value="__TOGGLE_PHASE_OUTPUTS__",
                ),
                toggle_choice(
                    "Generate snapshot artifact after analysis",
                    preferences.generate_snapshot,
                    value="__TOGGLE_SNAPSHOT__",
                ),
                value_choice(
                    "Rules file name",
                    rules_filename,
                    value="__EDIT_RULES_FILENAME__",
                ),
                value_choice(
                    "Snapshot file name",
                    snapshot_filename,
                    value="__EDIT_SNAPSHOT_FILENAME__",
                ),
                navigation_choice("Back", value="__BACK__"),
            ],
            qmark="🗂️",
            style=CLI_STYLE,
        ).ask()

        if selection in (None, "__BACK__"):
            console.print("[dim]Leaving output preferences.[/]")
            return

        if selection == "__TOGGLE_CURSORIGNORE__":
            new_value = not preferences.generate_cursorignore
            configuration.save_generate_cursorignore_preference(new_value)
            status = "enabled" if new_value else "disabled"
            console.print(f"[green].cursorignore generation {status}.[/]")
        elif selection == "__TOGGLE_AGENT_SCAFFOLD__":
            new_value = not preferences.generate_agent_scaffold
            configuration.save_generate_agent_scaffold_preference(new_value)
            status = "enabled" if new_value else "disabled"
            console.print(f"[green].agent scaffold generation {status}.[/]")
        elif selection == "__TOGGLE_PHASE_OUTPUTS__":
            new_value = not preferences.generate_phase_outputs
            configuration.save_generate_phase_outputs_preference(new_value)
            if new_value:
                console.print("[green]Will write per-phase reports and metrics to phases_output/.[/]")
            else:
                console.print("[yellow]Per-phase reports and metrics will be skipped.[/]")
        elif selection == "__TOGGLE_SNAPSHOT__":
            new_value = not preferences.generate_snapshot
            configuration.save_generate_snapshot_preference(new_value)
            if new_value:
                console.print("[green]Snapshot artifact generation enabled.[/]")
            else:
                console.print("[yellow]Snapshot artifact generation disabled.[/]")
        elif selection == "__EDIT_RULES_FILENAME__":
            answer = questionary.text(
                "Enter rules file name (stored in project root):",
                default=rules_filename,
                qmark="🗂️",
                style=CLI_STYLE,
                validate=lambda text, snapshot_filename=snapshot_filename: _validate_rules_filename_input(
                    text,
                    snapshot_filename=snapshot_filename,
                ),
            ).ask()

            if not answer:
                console.print("[yellow]No changes made to rules file name.[/]")
                continue

            validated = _validate_rules_filename_input(answer, snapshot_filename=snapshot_filename)
            if validated is not True:
                console.print(f"[red]{validated}[/]")
                continue

            trimmed = _normalize_filename_input(answer)
            configuration.save_rules_file_name(trimmed)
            console.print(f"[green]Rules file will now be written to {trimmed}.[/]")
        elif selection == "__EDIT_SNAPSHOT_FILENAME__":
            answer = questionary.text(
                "Enter snapshot file name (stored in project root):",
                default=snapshot_filename,
                qmark="🗂️",
                style=CLI_STYLE,
                validate=lambda text, rules_filename=rules_filename: _validate_snapshot_filename_input(
                    text,
                    rules_filename=rules_filename,
                ),
            ).ask()

            if not answer:
                console.print("[yellow]No changes made to snapshot file name.[/]")
                continue

            validated = _validate_snapshot_filename_input(answer, rules_filename=rules_filename)
            if validated is not True:
                console.print(f"[red]{validated}[/]")
                continue

            trimmed = _normalize_filename_input(answer)
            configuration.save_snapshot_file_name(trimmed)
            console.print(f"[green]Snapshot file will now be written to {trimmed}.[/]")
