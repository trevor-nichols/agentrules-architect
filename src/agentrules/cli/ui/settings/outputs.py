"""Output generation preferences flow."""

from __future__ import annotations

import questionary

from agentrules.cli.context import CliContext
from agentrules.cli.services import configuration
from agentrules.cli.ui.styles import CLI_STYLE, navigation_choice, toggle_choice, value_choice


def configure_output_preferences(context: CliContext) -> None:
    """Interactive prompts for toggling generated artifacts."""

    console = context.console
    console.print("\n[bold]Configure output preferences[/bold]")
    console.print("[dim]Toggle generated artifacts after each analysis run.[/dim]\n")

    while True:
        preferences = configuration.get_output_preferences()
        rules_filename = configuration.get_rules_file_name()
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
                value_choice(
                    "Rules file name",
                    rules_filename,
                    value="__EDIT_RULES_FILENAME__",
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
        elif selection == "__EDIT_RULES_FILENAME__":
            answer = questionary.text(
                "Enter rules file name (stored in project root):",
                default=rules_filename,
                qmark="🗂️",
                style=CLI_STYLE,
                validate=lambda text: bool(text.strip()) and "/" not in text and "\\" not in text,
            ).ask()

            if not answer:
                console.print("[yellow]No changes made to rules file name.[/]")
                continue

            trimmed = answer.strip()
            configuration.save_rules_file_name(trimmed)
            console.print(f"[green]Rules file will now be written to {trimmed}.[/]")
