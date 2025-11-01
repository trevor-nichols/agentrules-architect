"""Researcher agent model configuration."""

from __future__ import annotations

import questionary

from agentrules.cli.context import CliContext
from agentrules.cli.services import configuration
from agentrules.cli.ui.styles import CLI_STYLE, navigation_choice
from agentrules.core.configuration import model_presets

from .utils import (
    build_model_choice_state,
    current_labels,
    select_variant,
)


def configure_researcher_phase(
    context: CliContext,
    presets: list[model_presets.PresetInfo],
    current_key: str | None,
    default_key: str | None,
    current_mode: str,
    tavily_available: bool,
) -> bool:
    """Handle interactive configuration for the researcher agent."""

    console = context.console

    mode_choices = [
        questionary.Choice(
            title="Auto – enable when Tavily key is available"
            + (" [current]" if current_mode == "auto" else ""),
            value="auto",
        ),
        questionary.Choice(
            title="Force on – always run the researcher agent"
            + (" [current]" if current_mode == "on" else ""),
            value="on",
        ),
        questionary.Choice(
            title="Disable researcher agent"
            + (" [current]" if current_mode == "off" else ""),
            value="off",
        ),
        navigation_choice("Cancel", value="__CANCEL__"),
    ]

    mode_selection = questionary.select(
        "Researcher agent mode:",
        choices=mode_choices,
        default=current_mode,
        qmark="🔍",
        style=CLI_STYLE,
    ).ask()

    if mode_selection in (None, "__CANCEL__"):
        console.print("[yellow]Researcher configuration cancelled.[/]")
        return False

    if mode_selection == "off":
        if current_mode != "off":
            configuration.save_researcher_mode("off")
            console.print("[yellow]Researcher agent disabled for Phase 1.[/]")
            return True
        console.print("[dim]Researcher agent already disabled.[/]")
        return False

    desired_mode = mode_selection
    mode_changed = desired_mode != current_mode

    default_info = model_presets.get_preset_info(default_key) if default_key else None
    current_label, _ = current_labels(current_key)

    keep_title = "Keep current preset"
    if current_label and current_label != "Not configured":
        keep_title = f"Keep current preset ({current_label})"

    initial_choices = [questionary.Choice(title=keep_title, value="__KEEP__")]
    reset_title = "Reset to default"
    if default_info:
        reset_title = f"Reset to default ({default_info.label} – {default_info.provider_display})"
    initial_choices.append(questionary.Choice(title=reset_title, value="__RESET__"))

    state = build_model_choice_state(
        presets,
        current_key,
        default_key,
        include_reset=False,
        reset_title="",
        initial_choices=initial_choices,
    )

    selection = questionary.select(
        "Researcher preset:",
        choices=state.choices,
        default="__KEEP__",
        qmark="🧠",
        style=CLI_STYLE,
    ).ask()

    if selection is None:
        console.print("[yellow]Researcher configuration cancelled.[/]")
        return False

    if selection in state.group_selection_map:
        group_selection = state.group_selection_map[selection]
        variant_choice = select_variant(group_selection)
        if variant_choice is None:
            console.print("[yellow]Researcher configuration cancelled.[/]")
            return False
        selection = variant_choice

    if selection == "__KEEP__":
        if mode_changed:
            configuration.save_researcher_mode(desired_mode)
            _render_mode_message(console.print, desired_mode, tavily_available)
            return True
        console.print("[dim]No changes made to researcher settings.[/]")
        return False

    preset_changed = False
    if selection == "__RESET__":
        configuration.save_phase_model("researcher", None)
        console.print("[green]Researcher preset reset to default.[/]")
        preset_changed = True
    else:
        configuration.save_phase_model("researcher", selection)
        preset_info = model_presets.get_preset_info(selection)
        if preset_info:
            console.print(
                f"[green]Researcher agent will use {preset_info.label} [{preset_info.provider_display}].[/]"
            )
        else:
            console.print("[green]Researcher preset updated.[/]")
        preset_changed = True

    if mode_changed:
        configuration.save_researcher_mode(desired_mode)
        _render_mode_message(console.print, desired_mode, tavily_available)

    return preset_changed or mode_changed


def _render_mode_message(printer, mode: str, tavily_available: bool) -> None:
    """Emit feedback after researcher mode changes."""

    if mode == "auto":
        if tavily_available:
            printer("[green]Researcher mode set to auto; runs when Tavily search is available.[/]")
        else:
            printer("[yellow]Researcher mode set to auto. Add a Tavily API key to enable runs.[/]")
    else:
        printer("[green]Researcher mode set to forced on.[/]")
