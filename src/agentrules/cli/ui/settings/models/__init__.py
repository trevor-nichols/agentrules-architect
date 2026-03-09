"""Model preset configuration flows."""

from __future__ import annotations

import os
from collections.abc import Mapping

import questionary

from agentrules.cli.context import CliContext
from agentrules.cli.services import codex_runtime, configuration
from agentrules.cli.ui.styles import CLI_STYLE, model_display_choice, navigation_choice
from agentrules.core.agents.base import ModelProvider
from agentrules.core.configuration import model_presets
from agentrules.core.utils.provider_capabilities import uses_runtime_native_web_search

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
        provider_availability = configuration.get_provider_availability()
        active = configuration.get_active_presets()
        researcher_mode = configuration.get_researcher_mode()
        tavily_available = configuration.has_tavily_credentials()
        runtime_codex_presets = _load_runtime_codex_presets(provider_availability)

        offline_mode = bool(os.getenv("OFFLINE"))

        phase_choices = _build_phase_choices(
            active,
            researcher_mode,
            tavily_available,
            offline_mode,
            provider_availability,
        )
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
        presets = configuration.get_available_presets_for_phase(phase, provider_availability)
        presets = _merge_presets_with_runtime_codex(presets, runtime_codex_presets)
        if not presets:
            console.print(f"[yellow]No presets available for {title}; configure provider access first.[/]")
            continue

        default_key = model_presets.get_default_preset_key(phase)
        current_key = active.get(phase, default_key)
        current_key = _normalize_codex_selection_key(current_key, runtime_codex_presets)
        default_key = _normalize_codex_selection_key(default_key, runtime_codex_presets)

        if phase == "researcher":
            if configure_researcher_phase(
                context,
                presets,
                current_key,
                default_key,
                researcher_mode,
                tavily_available,
                offline_mode,
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
    offline_mode: bool,
    provider_availability: Mapping[str, bool],
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
            researcher_model, researcher_provider = describe_researcher_phase_status(
                researcher_key=researcher_key,
                researcher_mode=researcher_mode,
                tavily_available=tavily_available,
                offline_mode=offline_mode,
                provider_availability=provider_availability,
            )
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


def describe_researcher_phase_status(
    *,
    researcher_key: str | None,
    researcher_mode: str,
    tavily_available: bool,
    offline_mode: bool,
    provider_availability: Mapping[str, bool],
) -> tuple[str, str]:
    """Return the researcher row labels for the model-settings menu."""

    researcher_model, researcher_provider = current_labels(researcher_key)
    researcher_info = model_presets.get_preset_info(researcher_key) if researcher_key else None
    researcher_uses_native_search = uses_runtime_native_web_search(researcher_info)
    codex_available = bool(provider_availability.get(ModelProvider.CODEX.value, False))

    if not tavily_available and not offline_mode and not researcher_uses_native_search:
        if codex_available:
            return "Needs Tavily or Codex preset", ""
        return "Add Tavily API key to enable", ""

    status_label = "On" if researcher_mode == "on" else "Off"
    if researcher_model == "Not configured":
        return status_label, researcher_provider
    return f"{researcher_model} ({status_label})", researcher_provider


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


def _load_runtime_codex_presets(
    provider_availability: Mapping[str, bool],
) -> tuple[model_presets.PresetInfo, ...]:
    codex_available = bool(provider_availability.get(ModelProvider.CODEX.value, False))
    if not codex_available:
        return ()

    try:
        diagnostics = codex_runtime.get_codex_runtime_diagnostics(include_models=True)
    except Exception:
        return ()
    if diagnostics.runtime_error or diagnostics.models_error or not diagnostics.models:
        return ()

    catalog_entries = [
        model_presets.CodexRuntimeModelCatalogEntry(
            model=model.model,
            display_name=model.display_name,
            description=model.description or model.availability_message,
            default_reasoning_effort=model.default_reasoning_effort,
            supported_reasoning_efforts=tuple(
                model_presets.CodexRuntimeModelReasoningOption(
                    reasoning_effort=option.reasoning_effort,
                    description=option.description,
                )
                for option in model.supported_reasoning_efforts
            ),
        )
        for model in diagnostics.models
    ]
    return tuple(model_presets.build_codex_runtime_preset_infos(catalog_entries))


def _merge_presets_with_runtime_codex(
    presets: list[model_presets.PresetInfo],
    runtime_codex_presets: tuple[model_presets.PresetInfo, ...],
) -> list[model_presets.PresetInfo]:
    if not runtime_codex_presets:
        return presets

    merged: list[model_presets.PresetInfo] = [preset for preset in presets if preset.provider != ModelProvider.CODEX]
    existing_keys = {preset.key for preset in merged}
    for runtime_preset in runtime_codex_presets:
        if runtime_preset.key in existing_keys:
            continue
        merged.append(runtime_preset)
        existing_keys.add(runtime_preset.key)
    return merged


def _normalize_codex_selection_key(
    key: str | None,
    runtime_codex_presets: tuple[model_presets.PresetInfo, ...],
) -> str | None:
    if key is None or not runtime_codex_presets:
        return key
    runtime_by_model: dict[str, str] = {}
    runtime_by_identity: dict[tuple[str, str | None], str] = {}
    for runtime_preset in runtime_codex_presets:
        model_name = model_presets.parse_codex_runtime_preset_key(runtime_preset.key)
        if model_name is None:
            continue
        runtime_by_model.setdefault(model_name, runtime_preset.key)
        effort = model_presets.parse_codex_runtime_reasoning_for_preset_key(runtime_preset.key)
        runtime_by_identity[(model_name, effort)] = runtime_preset.key

    model_name = model_presets.resolve_codex_model_name_for_preset_key(key)
    if model_name is None:
        return key
    selected_effort = model_presets.resolve_codex_reasoning_effort_for_preset_key(key)
    for effort in _preferred_codex_effort_order(selected_effort):
        candidate = runtime_by_identity.get((model_name, effort))
        if candidate is not None:
            return candidate
    return runtime_by_model.get(model_name, key)


def _preferred_codex_effort_order(selected_effort: str | None) -> tuple[str | None, ...]:
    ordered_candidates: list[str | None] = []

    def _append(value: str | None) -> None:
        if value not in ordered_candidates:
            ordered_candidates.append(value)

    _append(selected_effort)
    for value in ("medium", "high", "low", "minimal", "none", "xhigh", None):
        _append(value)
    return tuple(ordered_candidates)


__all__ = ["configure_models"]
