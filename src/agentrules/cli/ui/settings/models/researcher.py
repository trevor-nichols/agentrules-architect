"""Researcher agent model configuration."""

from __future__ import annotations

import questionary

from agentrules.cli.context import CliContext
from agentrules.cli.services import configuration
from agentrules.cli.ui.styles import CLI_STYLE, navigation_choice
from agentrules.core.configuration import model_presets
from agentrules.core.utils.provider_capabilities import uses_runtime_native_web_search

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
    offline_mode: bool,
) -> bool:
    """Handle interactive configuration for the researcher agent."""

    console = context.console
    runtime_native_available = any(uses_runtime_native_web_search(preset) for preset in presets)

    if not tavily_available and not offline_mode and not runtime_native_available:
        console.print(
            "[yellow]Add a Tavily API key under Settings → Provider API keys to enable the researcher agent.[/]"
        )
        return False

    mode_choices = [
        questionary.Choice(
            title="On" + (" [current]" if current_mode == "on" else ""),
            value="on",
        ),
        questionary.Choice(
            title="Off" + (" [current]" if current_mode == "off" else ""),
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

    desired_mode = mode_selection
    mode_changed = desired_mode != current_mode

    if desired_mode == "off":
        if mode_changed:
            configuration.save_researcher_mode("off")
            _render_mode_message(console.print, "off")
            return True
        console.print("[dim]Researcher agent already disabled.[/]")
        return False

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
            _render_researcher_requirements_notice(
                console.print,
                desired_mode=desired_mode,
                offline_mode=offline_mode,
                tavily_available=tavily_available,
                selected_key=current_key,
            )
            _render_mode_message(console.print, desired_mode)
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
        selected_key = default_key if selection == "__RESET__" else selection
        _render_researcher_requirements_notice(
            console.print,
            desired_mode=desired_mode,
            offline_mode=offline_mode,
            tavily_available=tavily_available,
            selected_key=selected_key,
        )
        _render_mode_message(console.print, desired_mode)

    return preset_changed or mode_changed


def _render_mode_message(printer, mode: str) -> None:
    """Emit feedback after researcher mode changes."""

    if mode == "on":
        printer("[green]Researcher agent enabled.[/]")
    else:
        printer("[yellow]Researcher agent disabled for Phase 1.[/]")


def _render_researcher_requirements_notice(
    printer,
    *,
    desired_mode: str,
    offline_mode: bool,
    tavily_available: bool,
    selected_key: str | None,
) -> None:
    """Explain when the selected researcher preset still needs Tavily."""

    if desired_mode != "on" or offline_mode or tavily_available:
        return

    preset_info = model_presets.get_preset_info(selected_key) if selected_key else None
    if uses_runtime_native_web_search(preset_info):
        return

    printer(
        "[yellow]This researcher preset still needs Tavily web search. "
        "Add a Tavily API key or choose a Codex preset to activate runtime-native research.[/]"
    )
