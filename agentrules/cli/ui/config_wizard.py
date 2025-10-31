"""Interactive configuration flows for providers and model presets."""

from __future__ import annotations

from typing import Any, Optional, Tuple

import questionary

from agentrules import model_config

from ..context import CliContext, mask_secret
from ..services import configuration


def show_provider_summary(context: CliContext) -> None:
    context.console.print("\n[bold]Current Provider Configuration[/bold]")
    for state in configuration.list_provider_states():
        context.console.print(f"- {state.name.title():<10}: {mask_secret(state.api_key)}")
    context.console.print("")


def configure_provider_keys(context: CliContext) -> None:
    console = context.console
    console.print("\n[bold]Configure Provider API Keys[/bold]")
    console.print("Select a provider to update. Leave the key blank to keep the current value.\n")

    updated = False

    while True:
        states = configuration.list_provider_states()
        choices: list[questionary.Choice] = [
            questionary.Choice(
                title=f"{state.name.title()} ({state.env_var}) [{mask_secret(state.api_key)}]",
                value=state.name,
            )
            for state in states
        ]
        choices.append(questionary.Choice(title="Done", value="__DONE__"))

        selection = questionary.select(
            "Select provider to configure:",
            choices=choices,
            qmark="🔐",
        ).ask()

        if selection is None:
            console.print("[yellow]Configuration cancelled.[/]")
            return
        if selection == "__DONE__":
            break

        state = next((item for item in states if item.name == selection), None)
        if not state:
            console.print("[red]Unknown provider selected.[/]")
            continue

        current_display = mask_secret(state.api_key)
        answer = questionary.password(
            f"Enter {state.name.title()} API key ({state.env_var}) [{current_display}]:",
            qmark="🔐",
            default="",
        ).ask()

        if answer is None:
            console.print("[yellow]Configuration cancelled.[/]")
            return

        trimmed = answer.strip()
        if trimmed:
            configuration.save_provider_key(selection, trimmed)
            updated = True
            console.print(f"[green]{selection.title()} key updated.[/]")
        else:
            console.print("[dim]No changes made.[/]")

    if updated:
        console.print("[green]Provider keys updated.[/]")
    else:
        console.print("[dim]No provider keys changed.[/]")


def configure_models(context: CliContext) -> None:
    console = context.console
    console.print("\n[bold]Configure model presets per phase[/bold]")
    console.print(
        "Select a phase to adjust its model preset. Choose 'Reset to default' inside the phase menu to revert.\n"
    )

    provider_keys = configuration.get_provider_keys()
    active = configuration.get_active_presets()
    updated = False

    def _split_preset_label(label: str) -> Tuple[str, Optional[str]]:
        if " (" in label and label.endswith(")"):
            base, remainder = label.split(" (", 1)
            return base, remainder[:-1]
        return label, None

    def _variant_display_text(variant_label: Optional[str]) -> str:
        if not variant_label:
            return "Default"
        return variant_label[0].upper() + variant_label[1:]

    def _current_display(key: Optional[str]) -> str:
        info = model_config.get_preset_info(key) if key else None
        if not info:
            return "Not configured"
        return f"{info.label} [{info.provider_display}]"

    while True:
        phase_choices: list[questionary.Choice | questionary.Separator] = []
        handled_phases: set[str] = set()

        for phase in model_config.PHASE_SEQUENCE:
            if phase in handled_phases:
                continue

            if phase == "phase1" and "researcher" in model_config.PHASE_SEQUENCE:
                header_title = model_config.get_phase_title("phase1")
                phase_choices.append(questionary.Separator(header_title))

                general_key = active.get("phase1", model_config.get_default_preset_key("phase1"))
                general_label = _current_display(general_key)
                phase_choices.append(
                    questionary.Choice(
                        title=f"├─ General Agents [{general_label}]",
                        value="phase1",
                    )
                )

                researcher_key = active.get("researcher", model_config.get_default_preset_key("researcher"))
                researcher_label = _current_display(researcher_key)
                researcher_title = model_config.get_phase_title("researcher")
                phase_choices.append(
                    questionary.Choice(
                        title=f"└─ {researcher_title} [{researcher_label}]",
                        value="researcher",
                    )
                )

                handled_phases.update({"phase1", "researcher"})
                continue

            title = model_config.get_phase_title(phase)
            current_key = active.get(phase, model_config.get_default_preset_key(phase))
            display_label = _current_display(current_key)
            phase_choices.append(questionary.Choice(title=f"{title} [{display_label}]", value=phase))
            handled_phases.add(phase)

        phase_choices.append(questionary.Choice(title="Done", value="__DONE__"))

        phase_selection = questionary.select(
            "Select phase to configure:",
            choices=phase_choices,
            qmark="🧠",
        ).ask()

        if phase_selection is None:
            console.print("[yellow]Model configuration cancelled.[/]")
            return
        if phase_selection == "__DONE__":
            break

        phase = phase_selection
        title = model_config.get_phase_title(phase)
        presets = configuration.get_available_presets_for_phase(phase, provider_keys)
        if not presets:
            console.print(f"[yellow]No presets available for {title}; configure provider keys first.[/]")
            continue

        default_key = model_config.get_default_preset_key(phase)
        current_key = active.get(phase, default_key)
        default_info = model_config.get_preset_info(default_key) if default_key else None

        model_choices: list[questionary.Choice] = []
        if default_info:
            model_choices.append(
                questionary.Choice(
                    title=f"Reset to default ({default_info.label} – {default_info.provider_display})",
                    value="__RESET__",
                )
            )
        else:
            model_choices.append(questionary.Choice(title="Reset to default", value="__RESET__"))

        grouped_entries: list[dict[str, Any]] = []
        grouped_lookup: dict[tuple[str, str, str], dict[str, Any]] = {}
        for preset in presets:
            base_label, variant_label = _split_preset_label(preset.label)
            group_key = (preset.provider_slug, base_label, preset.provider_display)
            if group_key not in grouped_lookup:
                grouped_lookup[group_key] = {
                    "base_label": base_label,
                    "provider_display": preset.provider_display,
                    "variants": [],
                }
                grouped_entries.append(grouped_lookup[group_key])
            grouped_lookup[group_key]["variants"].append(
                {
                    "preset": preset,
                    "preset_key": preset.key,
                    "variant_label": variant_label,
                    "variant_display": _variant_display_text(variant_label),
                }
            )

        group_selection_map: dict[str, dict[str, Any]] = {}
        for idx, entry in enumerate(grouped_entries):
            variants = entry["variants"]
            if len(variants) == 1:
                variant = variants[0]
                title_label = f"{entry['base_label']} [{entry['provider_display']}]"
                if variant["preset_key"] == default_key:
                    title_label += " (default)"
                if variant["preset_key"] == current_key:
                    title_label += " [current]"
                model_choices.append(questionary.Choice(title=title_label, value=variant["preset_key"]))
            else:
                current_variant = next((v for v in variants if v["preset_key"] == current_key), None)
                default_variant = next((v for v in variants if v["preset_key"] == default_key), None)
                summary = f"{entry['base_label']} [{entry['provider_display']}] – {len(variants)} options"
                if current_variant:
                    summary += f" (current: {current_variant['variant_display']})"
                elif default_variant:
                    summary += f" (default: {default_variant['variant_display']})"
                group_value = f"__GROUP__{idx}"
                model_choices.append(questionary.Choice(title=summary, value=group_value))
                group_selection_map[group_value] = {
                    "entry": entry,
                    "variants": variants,
                    "current_key": current_key,
                    "default_key": default_key,
                }

        default_value = model_choices[0].value
        if current_key and any(choice.value == current_key for choice in model_choices):
            default_value = current_key
        else:
            for group_value, group_data in group_selection_map.items():
                if any(v["preset_key"] == current_key for v in group_data["variants"]):
                    default_value = group_value
                    break
            else:
                if default_key and any(choice.value == default_key for choice in model_choices):
                    default_value = default_key
                else:
                    for group_value, group_data in group_selection_map.items():
                        if any(v["preset_key"] == default_key for v in group_data["variants"]):
                            default_value = group_value
                            break

        selection = questionary.select(
            f"{title}:",
            choices=model_choices,
            default=default_value,
            qmark="🧠",
        ).ask()

        if selection is None:
            console.print("[yellow]Model configuration cancelled.[/]")
            return

        if selection in group_selection_map:
            group_data = group_selection_map[selection]
            entry = group_data["entry"]
            variants = group_data["variants"]

            variant_choices: list[questionary.Choice] = []
            for variant in variants:
                variant_title = variant["variant_display"]
                if variant["preset_key"] == group_data["default_key"]:
                    variant_title += " (default)"
                if variant["preset_key"] == group_data["current_key"]:
                    variant_title += " [current]"
                variant_choices.append(questionary.Choice(title=variant_title, value=variant["preset_key"]))

            preferred_default = group_data["current_key"] or group_data["default_key"]
            if not preferred_default or not any(choice.value == preferred_default for choice in variant_choices):
                preferred_default = variant_choices[0].value

            selection = questionary.select(
                f"{entry['base_label']} [{entry['provider_display']}] – choose variant:",
                choices=variant_choices,
                default=preferred_default,
                qmark="🧠",
            ).ask()

            if selection is None:
                console.print("[yellow]Model configuration cancelled.[/]")
                return

        if selection == "__RESET__":
            configuration.save_phase_model(phase, None)
            active.pop(phase, None)
            console.print(f"[green]{title} reset to default preset.[/]")
        else:
            configuration.save_phase_model(phase, selection)
            active[phase] = selection
            preset_info = model_config.get_preset_info(selection)
            if preset_info:
                console.print(f"[green]{title} now uses {preset_info.label} [{preset_info.provider_display}].[/]")
            else:
                console.print(f"[green]{title} preset updated.[/]")
        updated = True

    if updated:
        overrides = {phase: key for phase, key in active.items() if phase in model_config.PHASE_SEQUENCE and key}
        configuration.apply_model_overrides(overrides)
        configuration.apply_model_overrides()
        console.print("[green]Model selections saved.[/]")
    else:
        console.print("[dim]No model presets changed.[/]")
