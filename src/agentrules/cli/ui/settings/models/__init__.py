"""Model preset configuration flows."""

from __future__ import annotations

from collections.abc import Mapping

import questionary

from agentrules.cli.context import CliContext
from agentrules.cli.services import configuration
from agentrules.cli.ui.styles import CLI_STYLE, model_display_choice, navigation_choice
from agentrules.core.configuration import model_presets

from .researcher import configure_researcher_phase
from .utils import build_model_choice_state, current_labels, select_variant


def configure_models(context: CliContext) -> None:
    """Interactive flow for configuring model presets per phase."""

    console = context.console
    console.print("\n[bold]Configure model presets per phase[/bold]")
    console.print(
        "Select a phase to adjust its model preset. Choose 'Reset to default' inside the phase menu to revert.\n"
    )

    updated = False

    while True:
        provider_keys = configuration.get_provider_keys()
        active = configuration.get_active_presets()
        researcher_mode = configuration.get_researcher_mode()
        tavily_available = configuration.has_tavily_credentials()

        phase_choices = _build_phase_choices(active, researcher_mode, tavily_available)
        phase_choices.append(navigation_choice("Done", value="__DONE__"))

        phase_selection = questionary.select(
            "Select phase to configure:",
            choices=phase_choices,
            qmark="🧠",
            style=CLI_STYLE,
        ).ask()

        if phase_selection is None:
            console.print("[yellow]Model configuration cancelled.[/]")
            return
        if phase_selection == "__DONE__":
            break

        phase = phase_selection
        title = model_presets.get_phase_title(phase)
        presets = configuration.get_available_presets_for_phase(phase, provider_keys)
        if not presets:
            console.print(f"[yellow]No presets available for {title}; configure provider keys first.[/]")
            continue

        default_key = model_presets.get_default_preset_key(phase)
        current_key = active.get(phase, default_key)

        if phase == "researcher":
            if configure_researcher_phase(
                context,
                presets,
                current_key,
                default_key,
                researcher_mode,
                tavily_available,
            ):
                updated = True
            continue

        try:
            if _configure_general_phase(
                context,
                phase,
                title,
                presets,
                current_key,
                default_key,
            ):
                updated = True
        except _ConfigurationCancelled:
            return

    if updated:
        active = configuration.get_active_presets()
        overrides = {phase: key for phase, key in active.items() if phase in model_presets.PHASE_SEQUENCE and key}
        configuration.apply_model_overrides(overrides)
        configuration.apply_model_overrides()
        console.print("[green]Model selections saved.[/]")
    else:
        console.print("[dim]No model presets changed.[/]")


def _build_phase_choices(
    active: Mapping[str, str | None],
    researcher_mode: str,
    tavily_available: bool,
) -> list[questionary.Choice | questionary.Separator]:
    phase_choices: list[questionary.Choice | questionary.Separator] = []
    handled_phases: set[str] = set()

    for phase in model_presets.PHASE_SEQUENCE:
        if phase in handled_phases:
            continue

        if phase == "phase1" and "researcher" in model_presets.PHASE_SEQUENCE:
            header_title = model_presets.get_phase_title("phase1")
            phase_choices.append(questionary.Separator(header_title))

            general_key = active.get("phase1", model_presets.get_default_preset_key("phase1"))
            general_model, general_provider = current_labels(general_key)
            phase_choices.append(
                model_display_choice("├─ General Agents", general_model, general_provider, value="phase1")
            )

            researcher_key = active.get("researcher", model_presets.get_default_preset_key("researcher"))
            researcher_model, researcher_provider = current_labels(researcher_key)
            if researcher_mode == "off":
                researcher_model = "Disabled"
                researcher_provider = ""
            else:
                mode_suffix = " (auto)" if researcher_mode == "auto" else " (forced)"
                if researcher_model != "Not configured":
                    researcher_model = f"{researcher_model}{mode_suffix}"
                if researcher_mode == "auto" and not tavily_available:
                    researcher_model += " – awaiting Tavily key"
            researcher_title = model_presets.get_phase_title("researcher")
            phase_choices.append(
                model_display_choice(
                    f"└─ {researcher_title}",
                    researcher_model,
                    researcher_provider,
                    value="researcher",
                )
            )

            handled_phases.update({"phase1", "researcher"})
            continue

        title = model_presets.get_phase_title(phase)
        current_key = active.get(phase, model_presets.get_default_preset_key(phase))
        model_label, provider_label = current_labels(current_key)
        phase_choices.append(model_display_choice(title, model_label, provider_label, value=phase))
        handled_phases.add(phase)

    return phase_choices


def _configure_general_phase(
    context: CliContext,
    phase: str,
    title: str,
    presets: list[model_presets.PresetInfo],
    current_key: str | None,
    default_key: str | None,
) -> bool:
    console = context.console
    default_info = model_presets.get_preset_info(default_key) if default_key else None
    if default_info:
        reset_title = f"Reset to default ({default_info.label} – {default_info.provider_display})"
    else:
        reset_title = "Reset to default"

    state = build_model_choice_state(
        presets,
        current_key,
        default_key,
        include_reset=True,
        reset_title=reset_title,
    )

    selection = questionary.select(
        f"{title}:",
        choices=state.choices,
        default=state.default_value,
        qmark="🧠",
        style=CLI_STYLE,
    ).ask()

    if selection is None:
        console.print("[yellow]Model configuration cancelled.[/]")
        raise _ConfigurationCancelled

    if selection in state.group_selection_map:
        group_selection = state.group_selection_map[selection]
        variant_choice = select_variant(group_selection)
        if variant_choice is None:
            console.print("[yellow]Model configuration cancelled.[/]")
            raise _ConfigurationCancelled
        selection = variant_choice

    if selection == "__RESET__":
        configuration.save_phase_model(phase, None)
        console.print(f"[green]{title} reset to default preset.[/]")
    else:
        configuration.save_phase_model(phase, selection)
        preset_info = model_presets.get_preset_info(selection)
        if preset_info:
            console.print(f"[green]{title} now uses {preset_info.label} [{preset_info.provider_display}].[/]")
        else:
            console.print(f"[green]{title} preset updated.[/]")

    return True


class _ConfigurationCancelled(Exception):
    """Internal sentinel for handling cancellations."""


__all__ = ["configure_models"]
