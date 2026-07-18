"""Model preset configuration flows."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

import questionary

from agentrules.cli.context import CliContext
from agentrules.cli.services import codex_runtime, configuration
from agentrules.cli.ui.styles import CLI_STYLE, model_display_choice, navigation_choice
from agentrules.core.agents.base import ModelProvider
from agentrules.core.configuration import model_presets
from agentrules.core.utils.provider_capabilities import uses_runtime_native_web_search

from .researcher import configure_researcher_phase
from .utils import (
    build_model_choice_state,
    effective_current_labels,
    filter_deprecated_presets_for_selection,
    render_preset_deprecation_warning,
    select_variant,
)


@dataclass(frozen=True)
class _RuntimeCodexCatalog:
    visible_presets: tuple[model_presets.PresetInfo, ...]
    executable_identities: frozenset[tuple[str, str | None]] | None


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
        configured = configuration.get_configured_presets()
        active = configuration.get_active_presets()
        researcher_mode = configuration.get_researcher_mode()
        tavily_available = configuration.has_tavily_credentials()
        runtime_codex_catalog = _load_runtime_codex_catalog(provider_availability)
        runtime_codex_presets = runtime_codex_catalog.visible_presets

        offline_mode = bool(os.getenv("OFFLINE"))

        phase_choices = _build_phase_choices(
            configured,
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
        default_key = model_presets.get_default_preset_key(phase)
        configured_key = configured.get(phase, default_key)
        presets = configuration.get_available_presets_for_phase(phase, provider_availability)
        presets = _filter_claude_code_presets_for_runtime(presets, preserved_key=configured_key)
        presets = _merge_presets_with_runtime_codex(
            presets,
            runtime_codex_presets,
            executable_identities=runtime_codex_catalog.executable_identities,
            preserved_key=configured_key,
        )
        presets = filter_deprecated_presets_for_selection(presets, preserved_key=configured_key)
        if not presets:
            console.print(f"[yellow]No presets available for {title}; configure provider access first.[/]")
            continue

        selection_current_key = _normalize_codex_selection_key(configured_key, runtime_codex_presets)
        default_key = _normalize_codex_selection_key(default_key, runtime_codex_presets)

        if phase == "researcher":
            if configure_researcher_phase(
                context,
                presets,
                selection_current_key,
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
                selection_current_key,
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
    configured: Mapping[str, str | None],
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

            configured_general_key = configured.get("phase1", model_presets.get_default_preset_key("phase1"))
            general_key = active.get("phase1", model_presets.get_default_preset_key("phase1"))
            general_model, general_provider = effective_current_labels(
                configured_key=configured_general_key,
                effective_key=general_key,
            )
            phase_choices.append(
                model_display_choice("├─ General Agents", general_model, general_provider, value="phase1")
            )

            configured_researcher_key = configured.get(
                "researcher",
                model_presets.get_default_preset_key("researcher"),
            )
            researcher_key = active.get("researcher", model_presets.get_default_preset_key("researcher"))
            researcher_model, researcher_provider = describe_researcher_phase_status(
                configured_researcher_key=configured_researcher_key,
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
        configured_key = configured.get(phase, model_presets.get_default_preset_key(phase))
        current_key = active.get(phase, model_presets.get_default_preset_key(phase))
        model_label, provider_label = effective_current_labels(
            configured_key=configured_key,
            effective_key=current_key,
        )
        phase_choices.append(model_display_choice(title, model_label, provider_label, value=phase))
        handled_phases.add(phase)

    return phase_choices


def describe_researcher_phase_status(
    *,
    configured_researcher_key: str | None = None,
    researcher_key: str | None,
    researcher_mode: str,
    tavily_available: bool,
    offline_mode: bool,
    provider_availability: Mapping[str, bool],
) -> tuple[str, str]:
    """Return the researcher row labels for the model-settings menu."""

    if configured_researcher_key is None:
        configured_researcher_key = researcher_key

    researcher_model, researcher_provider = effective_current_labels(
        configured_key=configured_researcher_key,
        effective_key=researcher_key,
    )
    researcher_info = model_presets.get_preset_info(researcher_key) if researcher_key else None
    researcher_uses_native_search = uses_runtime_native_web_search(researcher_info)
    codex_available = bool(provider_availability.get(ModelProvider.CODEX.value, False))
    claude_code_available = bool(provider_availability.get(ModelProvider.CLAUDE_CODE.value, False))

    if not tavily_available and not offline_mode and not researcher_uses_native_search:
        if codex_available or claude_code_available:
            return "Needs Tavily or runtime preset", ""
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
        effective_selection = model_presets.resolve_runtime_preset_key(selection) or selection
        configuration.save_phase_model(phase, effective_selection)
        preset_info = model_presets.get_preset_info(effective_selection)
        if preset_info:
            console.print(f"[green]{title} now uses {preset_info.label} [{preset_info.provider_display}].[/]")
        else:
            console.print(f"[green]{title} preset updated.[/]")
        render_preset_deprecation_warning(console.print, selection, effective_key=effective_selection)

    return True


class _ConfigurationCancelled(Exception):
    """Internal sentinel for handling cancellations."""


def _load_runtime_codex_presets(
    provider_availability: Mapping[str, bool],
) -> tuple[model_presets.PresetInfo, ...]:
    return _load_runtime_codex_catalog(provider_availability).visible_presets


def _filter_claude_code_presets_for_runtime(
    presets: list[model_presets.PresetInfo],
    *,
    preserved_key: str | None,
) -> list[model_presets.PresetInfo]:
    runtime_version = configuration.CONFIG_MANAGER.get_claude_code_runtime_version()

    filtered: list[model_presets.PresetInfo] = []
    for preset in presets:
        if preset.provider != ModelProvider.CLAUDE_CODE:
            filtered.append(preset)
            continue

        model_config = model_presets.get_model_config_for_preset_key(preset.key)
        model_name = getattr(model_config, "model_name", None)
        if not isinstance(model_name, str) or not model_name.strip():
            filtered.append(preset)
            continue

        minimum_version = configuration.CONFIG_MANAGER.minimum_claude_code_version_for_model(model_name)
        if minimum_version is None or (runtime_version is not None and runtime_version >= minimum_version):
            filtered.append(preset)
            continue

        if preset.key == preserved_key:
            runtime_note = (
                f"runtime needs {minimum_version}+"
                if runtime_version is not None
                else f"runtime version unverified; needs {minimum_version}+"
            )
            filtered.append(
                model_presets.PresetInfo(
                    key=preset.key,
                    label=f"{preset.label} [current {runtime_note}]",
                    description=preset.description,
                    provider=preset.provider,
                )
            )

    return filtered


def _load_runtime_codex_catalog(
    provider_availability: Mapping[str, bool],
) -> _RuntimeCodexCatalog:
    codex_available = bool(provider_availability.get(ModelProvider.CODEX.value, False))
    if not codex_available:
        return _RuntimeCodexCatalog(visible_presets=(), executable_identities=None)

    try:
        diagnostics = codex_runtime.get_codex_runtime_diagnostics(include_models=True, include_hidden_models=True)
    except Exception:
        return _RuntimeCodexCatalog(visible_presets=(), executable_identities=None)
    if diagnostics.runtime_error or diagnostics.models_error:
        return _RuntimeCodexCatalog(visible_presets=(), executable_identities=None)
    if not diagnostics.models:
        return _RuntimeCodexCatalog(visible_presets=(), executable_identities=frozenset())

    catalog_entries = [
        model_presets.CodexRuntimeModelCatalogEntry(
            model=model.model,
            display_name=model.display_name,
            description=model.description or model.availability_message,
            is_default=model.is_default,
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
    visible_catalog_entries = [
        entry for entry, model in zip(catalog_entries, diagnostics.models, strict=True) if not model.hidden
    ]
    visible_presets = list(model_presets.build_codex_runtime_preset_infos(visible_catalog_entries))
    if not any(preset.key == model_presets.CODEX_RUNTIME_DEFAULT_KEY for preset in visible_presets):
        default_entry = next((entry for entry in catalog_entries if entry.is_default and entry.model.strip()), None)
        if default_entry is not None:
            default_preset = next(
                (
                    preset
                    for preset in model_presets.build_codex_runtime_preset_infos((default_entry,))
                    if preset.key == model_presets.CODEX_RUNTIME_DEFAULT_KEY
                ),
                None,
            )
            if default_preset is not None:
                visible_presets.insert(0, default_preset)
    executable_identities = model_presets.build_codex_runtime_executable_identities(catalog_entries)
    return _RuntimeCodexCatalog(
        visible_presets=tuple(visible_presets),
        executable_identities=executable_identities,
    )


def _merge_presets_with_runtime_codex(
    presets: list[model_presets.PresetInfo],
    runtime_codex_presets: tuple[model_presets.PresetInfo, ...],
    *,
    executable_identities: frozenset[tuple[str, str | None]] | None = None,
    preserved_key: str | None = None,
) -> list[model_presets.PresetInfo]:
    if not runtime_codex_presets and executable_identities is None and preserved_key is None:
        return presets

    merged: list[model_presets.PresetInfo] = [preset for preset in presets if preset.provider != ModelProvider.CODEX]
    existing_keys = {preset.key for preset in merged}
    for runtime_preset in runtime_codex_presets:
        if runtime_preset.key in existing_keys:
            continue
        merged.append(runtime_preset)
        existing_keys.add(runtime_preset.key)

    visible_runtime_identities = frozenset(
        identity
        for identity in (_codex_preset_identity(preset.key) for preset in runtime_codex_presets)
        if identity is not None
    )
    normalized_preserved_key = _normalize_codex_selection_key(preserved_key, runtime_codex_presets)
    if preserved_key is not None and preserved_key not in existing_keys:
        preserved_preset = model_presets.get_preset_info(preserved_key)
        if preserved_preset is not None and preserved_preset.provider == ModelProvider.CODEX:
            if model_presets.is_codex_runtime_default_preset_key(preserved_key):
                if executable_identities is None or executable_identities:
                    merged.append(preserved_preset)
                    existing_keys.add(preserved_preset.key)
            elif executable_identities is None:
                merged.append(preserved_preset)
                existing_keys.add(preserved_preset.key)
            else:
                identity = _codex_preset_identity(preserved_key)
                if identity is not None:
                    represented_by_visible_runtime = (
                        normalized_preserved_key != preserved_key and normalized_preserved_key in existing_keys
                    )
                    if not represented_by_visible_runtime and _is_codex_identity_executable(
                        identity,
                        executable_identities,
                    ):
                        merged.append(preserved_preset)
                        existing_keys.add(preserved_preset.key)

    for preset in presets:
        if preset.provider != ModelProvider.CODEX or preset.key in existing_keys:
            continue
        identity = _codex_preset_identity(preset.key)
        if identity is None:
            if preserved_key is not None and preset.key == preserved_key and executable_identities is None:
                merged.append(preset)
                existing_keys.add(preset.key)
                continue
            if executable_identities is not None:
                continue
            merged.append(preset)
            existing_keys.add(preset.key)
            continue
        represented_by_visible_runtime = _is_visible_runtime_representation(identity, visible_runtime_identities)
        if preserved_key is not None and preset.key == preserved_key:
            if executable_identities is None:
                merged.append(preset)
                existing_keys.add(preset.key)
            elif (
                normalized_preserved_key == preserved_key
                and _is_codex_identity_executable(identity, executable_identities)
            ):
                merged.append(preset)
                existing_keys.add(preset.key)
            continue
        if represented_by_visible_runtime:
            continue
        if executable_identities is not None:
            continue
        merged.append(preset)
        existing_keys.add(preset.key)
    return merged


def _normalize_codex_selection_key(
    key: str | None,
    runtime_codex_presets: tuple[model_presets.PresetInfo, ...],
) -> str | None:
    if key is None or not runtime_codex_presets:
        return key
    if model_presets.is_codex_runtime_default_preset_key(key):
        return (
            model_presets.CODEX_RUNTIME_DEFAULT_KEY
            if any(preset.key == model_presets.CODEX_RUNTIME_DEFAULT_KEY for preset in runtime_codex_presets)
            else key
        )
    runtime_by_model: dict[str, str] = {}
    runtime_by_exact_identity: dict[tuple[str, str | None], str] = {}
    runtime_by_normalized_identity: dict[tuple[str, str | None], str] = {}
    for runtime_preset in runtime_codex_presets:
        raw_model_name = model_presets.resolve_raw_codex_model_name_for_preset_key(runtime_preset.key)
        normalized_model_name = model_presets.resolve_codex_model_name_for_preset_key(runtime_preset.key)
        if raw_model_name is None or normalized_model_name is None:
            continue
        runtime_by_model.setdefault(normalized_model_name, runtime_preset.key)
        effort = model_presets.parse_codex_runtime_reasoning_for_preset_key(runtime_preset.key)
        runtime_by_exact_identity[(raw_model_name, effort)] = runtime_preset.key
        runtime_by_normalized_identity[(normalized_model_name, effort)] = runtime_preset.key

    raw_model_name = model_presets.resolve_raw_codex_model_name_for_preset_key(key)
    model_name = model_presets.resolve_codex_model_name_for_preset_key(key)
    if raw_model_name is None or model_name is None:
        return key
    selected_effort = model_presets.resolve_codex_reasoning_effort_for_preset_key(key)
    exact_candidate = runtime_by_exact_identity.get((raw_model_name, selected_effort))
    if exact_candidate is not None:
        return exact_candidate
    if raw_model_name != model_name:
        return key
    if selected_effort is not None:
        candidate = runtime_by_normalized_identity.get((model_name, selected_effort))
        return candidate if candidate is not None else key
    candidate = runtime_by_normalized_identity.get((model_name, None))
    if candidate is not None:
        return candidate
    return runtime_by_model.get(model_name, key)


def _codex_preset_identity(key: str | None) -> tuple[str, str | None] | None:
    model_name = model_presets.resolve_codex_model_name_for_preset_key(key)
    if model_name is None:
        return None
    return (model_name, model_presets.resolve_codex_reasoning_effort_for_preset_key(key))


def _is_visible_runtime_representation(
    identity: tuple[str, str | None],
    visible_runtime_identities: frozenset[tuple[str, str | None]],
) -> bool:
    if identity in visible_runtime_identities:
        return True
    model_name, effort = identity
    return effort is None and (model_name, None) in visible_runtime_identities


def _is_codex_identity_executable(
    identity: tuple[str, str | None],
    executable_identities: frozenset[tuple[str, str | None]],
) -> bool:
    model_name, reasoning_effort = identity
    if identity in executable_identities:
        return True
    if reasoning_effort is None:
        return False

    known_efforts = {
        effort
        for executable_model_name, effort in executable_identities
        if executable_model_name == model_name
    }
    if not known_efforts:
        return False

    explicit_efforts = {effort for effort in known_efforts if effort is not None}
    if explicit_efforts:
        return False
    return (model_name, None) in executable_identities


__all__ = ["configure_models"]
