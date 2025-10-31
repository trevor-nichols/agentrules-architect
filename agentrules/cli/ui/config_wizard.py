"""Interactive configuration flows for providers and model presets."""

from __future__ import annotations

import os
from typing import Any

import questionary
from rich.table import Table

from agentrules import model_config

from ..context import CliContext, format_secret_status, mask_secret
from ..services import configuration
from .styles import (
    CLI_STYLE,
    model_display_choice,
    model_variant_choice,
    navigation_choice,
    toggle_choice,
    value_choice,
)


def _render_provider_table(context: CliContext, states: list[configuration.ProviderState]) -> None:
    table = Table(title="[bold]Provider API Keys[/bold]", show_lines=False, pad_edge=False)
    table.add_column("Provider", style="bold", no_wrap=True)
    table.add_column("Status", style="", no_wrap=True)
    table.add_column("Key", style="dim")

    for state in states:
        status_display = format_secret_status(state.api_key)
        key_display = mask_secret(state.api_key) if state.api_key else "-"
        if state.api_key:
            key_display = f"[dim]{key_display}[/]"
        else:
            key_display = "[dim]-[/]"
        table.add_row(state.name.title(), status_display, key_display)

    context.console.print("")
    context.console.print(table)
    context.console.print("")


def show_provider_summary(context: CliContext) -> None:
    states = configuration.list_provider_states()
    _render_provider_table(context, states)


def configure_settings(context: CliContext) -> None:
    console = context.console
    console.print("\n[bold]Settings[/bold]")

    while True:
        selection = questionary.select(
            "Select a settings category:",
            choices=[
                questionary.Choice(title="Provider API keys", value="providers"),
                questionary.Choice(title="Model presets per phase", value="models"),
                questionary.Choice(title="Logging verbosity", value="logging"),
                questionary.Choice(title="Output preferences", value="outputs"),
                questionary.Choice(title="Exclusion rules", value="exclusions"),
                navigation_choice("Back", value="__BACK__"),
            ],
            qmark="⚙️",
            style=CLI_STYLE,
        ).ask()

        if selection in (None, "__BACK__"):
            console.print("[dim]Leaving settings.[/]")
            return
        if selection == "providers":
            configure_provider_keys(context)
        elif selection == "models":
            configure_models(context)
        elif selection == "logging":
            configure_logging(context)
        elif selection == "outputs":
            configure_output_preferences(context)
        elif selection == "exclusions":
            configure_exclusions(context)


def configure_provider_keys(context: CliContext) -> None:
    console = context.console
    console.print("\n[bold]Configure Provider API Keys[/bold]")
    console.print("Select a provider to update. Leave the key blank to keep the current value.")

    updated = False

    while True:
        states = configuration.list_provider_states()
        _render_provider_table(context, states)
        choices: list[questionary.Choice] = [
            questionary.Choice(title=state.name.title(), value=state.name)
            for state in states
        ]
        choices.append(navigation_choice("Done", value="__DONE__"))

        selection = questionary.select(
            "Select provider to configure:",
            choices=choices,
            qmark="🔐",
            style=CLI_STYLE,
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
            f"Enter {state.name.title()} API key [{current_display}]",
            qmark="🔐",
            default="",
            style=CLI_STYLE,
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


def configure_logging(context: CliContext) -> None:
    console = context.console
    console.print("\n[bold]Configure logging verbosity[/bold]")
    console.print(
        "Choose how much detail agentrules prints during analysis. Environment variable"
        " [cyan]AGENTRULES_LOG_LEVEL[/cyan] takes precedence if set.\n"
    )

    env_override = os.getenv("AGENTRULES_LOG_LEVEL")
    if env_override:
        console.print(
            f"[yellow]Active override detected:[/] AGENTRULES_LOG_LEVEL={env_override!r}."
            " Update or unset the variable to change levels here.\n"
        )

    choices = [
        questionary.Choice(title="Quiet – only warnings and errors", value="quiet"),
        questionary.Choice(title="Standard – progress updates (default)", value="standard"),
        questionary.Choice(title="Verbose – include debug diagnostics", value="verbose"),
        navigation_choice("Reset to default", value="__RESET__"),
        navigation_choice("Cancel", value="__CANCEL__"),
    ]

    current = configuration.get_logging_preference() or "standard"
    default_choice = current if current in {"quiet", "standard", "verbose"} else "standard"

    selection = questionary.select(
        "Select logging verbosity:",
        choices=choices,
        default=default_choice,
        qmark="🪵",
        style=CLI_STYLE,
    ).ask()

    if selection in (None, "__CANCEL__"):
        console.print("[yellow]No changes made to logging verbosity.[/]")
        return
    if selection == "__RESET__":
        configuration.save_logging_preference(None)
        console.print("[green]Logging verbosity reset to default (standard).[/]")
        return

    configuration.save_logging_preference(selection)
    if selection == "quiet":
        console.print("[green]Logging set to quiet. Only warnings and errors will display.[/]")
    elif selection == "verbose":
        console.print("[green]Logging set to verbose. Debug output will be shown.[/]")
    else:
        console.print("[green]Logging set to standard verbosity.[/]")


def configure_output_preferences(context: CliContext) -> None:
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


def _render_exclusion_summary(context: CliContext) -> dict:
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


def _prompt_exclusion_value(kind: str, default: str | None = None) -> str | None:
    label_map = {
        "directories": "Directory name",
        "files": "Filename",
        "extensions": "Extension (with or without dot)",
    }
    qmark_map = {
        "directories": "📁",
        "files": "📄",
        "extensions": "🔣",
    }

    question = label_map.get(kind, "Value")
    qmark = qmark_map.get(kind, "?")

    def _validate(text: str) -> bool:
        stripped = text.strip()
        if not stripped:
            return False
        if kind == "directories" and ("/" in stripped or "\\" in stripped):
            return False
        if kind == "extensions" and ("/" in stripped or "\\" in stripped or " " in stripped):
            return False
        return True

    answer = questionary.text(
        question + ":",
        default=default or "",
        qmark=qmark,
        style=CLI_STYLE,
        validate=lambda text: _validate(text) or f"Enter a valid {question.lower()}",
    ).ask()

    return answer.strip() if answer else None


def configure_exclusions(context: CliContext) -> None:
    console = context.console
    console.print("\n[bold]Configure exclusion rules[/bold]")
    console.print(
        "Adjust which files and directories are sent to the agents. Defaults stay intact unless overridden.\n"
    )

    while True:
        _render_exclusion_summary(context)

        current_gitignore = configuration.is_gitignore_respected()

        category = questionary.select(
            "Choose exclusion category:",
            choices=[
                questionary.Choice(title="Directories", value="directories"),
                questionary.Choice(title="Files", value="files"),
                questionary.Choice(title="Extensions", value="extensions"),
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

        value = _prompt_exclusion_value(category)
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


def configure_models(context: CliContext) -> None:
    console = context.console
    console.print("\n[bold]Configure model presets per phase[/bold]")
    console.print(
        "Select a phase to adjust its model preset. Choose 'Reset to default' inside the phase menu to revert.\n"
    )

    provider_keys = configuration.get_provider_keys()
    active = configuration.get_active_presets()
    updated = False

    def _split_preset_label(label: str) -> tuple[str, str | None]:
        if " (" in label and label.endswith(")"):
            base, remainder = label.split(" (", 1)
            return base, remainder[:-1]
        return label, None

    def _variant_display_text(variant_label: str | None) -> str:
        if not variant_label:
            return "Default"
        return variant_label[0].upper() + variant_label[1:]

    def _current_labels(key: str | None) -> tuple[str, str]:
        info = model_config.get_preset_info(key) if key else None
        if not info:
            return "Not configured", ""
        return info.label, info.provider_display

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
                general_model, general_provider = _current_labels(general_key)
                phase_choices.append(
                    model_display_choice(
                        "├─ General Agents",
                        general_model,
                        general_provider,
                        value="phase1",
                    )
                )

                researcher_key = active.get("researcher", model_config.get_default_preset_key("researcher"))
                researcher_model, researcher_provider = _current_labels(researcher_key)
                researcher_title = model_config.get_phase_title("researcher")
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

            title = model_config.get_phase_title(phase)
            current_key = active.get(phase, model_config.get_default_preset_key(phase))
            model_label, provider_label = _current_labels(current_key)
            phase_choices.append(
                model_display_choice(title, model_label, provider_label, value=phase)
            )
            handled_phases.add(phase)

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
                model_choices.append(
                    model_display_choice(
                        title_label,
                        variant["preset"].label,
                        variant["preset"].provider_display,
                        value=variant["preset_key"],
                    )
                )
            else:
                current_variant = next((v for v in variants if v["preset_key"] == current_key), None)
                default_variant = next((v for v in variants if v["preset_key"] == default_key), None)
                summary = f"{entry['base_label']} — {len(variants)} options"
                if current_variant:
                    summary += f" (current: {current_variant['variant_display']})"
                elif default_variant:
                    summary += f" (default: {default_variant['variant_display']})"
                group_value = f"__GROUP__{idx}"
                model_choices.append(
                    model_display_choice(
                        summary,
                        entry["base_label"],
                        entry["provider_display"],
                        value=group_value,
                    )
                )
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
            style=CLI_STYLE,
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
                variant_choices.append(
                    model_variant_choice(
                        variant_title,
                        variant["variant_display"],
                        entry["provider_display"],
                        value=variant["preset_key"],
                    )
                )

            preferred_default = group_data["current_key"] or group_data["default_key"]
            if not preferred_default or not any(choice.value == preferred_default for choice in variant_choices):
                preferred_default = variant_choices[0].value

            selection = questionary.select(
                f"{entry['base_label']} [{entry['provider_display']}] – choose variant:",
                choices=variant_choices,
                default=preferred_default,
                qmark="🧠",
                style=CLI_STYLE,
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
