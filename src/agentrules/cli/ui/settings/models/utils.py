"""Shared utilities for model preset configuration."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import cast

import questionary

from agentrules.cli.ui.styles import CLI_STYLE, model_display_choice, model_variant_choice
from agentrules.core.configuration import model_presets


@dataclass
class VariantOption:
    preset: model_presets.PresetInfo
    preset_key: str
    variant_label: str | None
    variant_display: str


@dataclass
class GroupSelection:
    base_label: str
    provider_display: str
    variants: list[VariantOption]
    current_key: str | None
    default_key: str | None


@dataclass
class ModelChoiceState:
    choices: list[questionary.Choice]
    group_selection_map: dict[str, GroupSelection]
    default_value: str


def split_preset_label(label: str) -> tuple[str, str | None]:
    if " (" in label and label.endswith(")"):
        base, remainder = label.split(" (", 1)
        return base, remainder[:-1]
    return label, None


def variant_display_text(variant_label: str | None) -> str:
    if not variant_label:
        return "Default"
    return variant_label[0].upper() + variant_label[1:]


def current_labels(key: str | None) -> tuple[str, str]:
    info = model_presets.get_preset_info(key) if key else None
    if not info:
        return "Not configured", ""
    return info.label, info.provider_display


def build_model_choice_state(
    presets: Sequence[model_presets.PresetInfo],
    current_key: str | None,
    default_key: str | None,
    *,
    include_reset: bool,
    reset_title: str,
    initial_choices: Iterable[questionary.Choice] | None = None,
) -> ModelChoiceState:
    """Construct grouped questionary choices for a preset list."""

    model_choices: list[questionary.Choice] = list(initial_choices or [])
    if include_reset:
        model_choices.append(questionary.Choice(title=reset_title, value="__RESET__"))

    grouped_entries: list[GroupSelection] = []
    grouped_lookup: dict[tuple[str, str, str], GroupSelection] = {}

    for preset in presets:
        base_label, variant_label = split_preset_label(preset.label)
        group_key = (preset.provider_slug, base_label, preset.provider_display)
        if group_key not in grouped_lookup:
            grouped_lookup[group_key] = GroupSelection(
                base_label=base_label,
                provider_display=preset.provider_display,
                variants=[],
                current_key=current_key,
                default_key=default_key,
            )
            grouped_entries.append(grouped_lookup[group_key])
        grouped_lookup[group_key].variants.append(
            VariantOption(
                preset=preset,
                preset_key=preset.key,
                variant_label=variant_label,
                variant_display=variant_display_text(variant_label),
            )
        )

    group_selection_map: dict[str, GroupSelection] = {}
    for idx, entry in enumerate(grouped_entries):
        variants = entry.variants
        if len(variants) == 1:
            variant = variants[0]
            title_label = f"{entry.base_label} [{entry.provider_display}]"
            if variant.preset_key == default_key:
                title_label += " (default)"
            if variant.preset_key == current_key:
                title_label += " [current]"
            model_choices.append(
                model_display_choice(
                    title_label,
                    variant.preset.label,
                    variant.preset.provider_display,
                    value=variant.preset_key,
                )
            )
        else:
            current_variant = next((v for v in variants if v.preset_key == current_key), None)
            default_variant = next((v for v in variants if v.preset_key == default_key), None)
            summary = f"{entry.base_label} — {len(variants)} options"
            if current_variant:
                summary += f" (current: {current_variant.variant_display})"
            elif default_variant:
                summary += f" (default: {default_variant.variant_display})"
            group_value = f"__GROUP__{idx}"
            model_choices.append(
                model_display_choice(
                    summary,
                    entry.base_label,
                    entry.provider_display,
                    value=group_value,
                )
            )
            group_selection_map[group_value] = entry

    fallback_value = "__RESET__"
    if model_choices:
        fallback_value = cast(str, model_choices[0].value)

    default_value = fallback_value
    if current_key and any(choice.value == current_key for choice in model_choices):
        default_value = current_key
    else:
        for group_value, entry in group_selection_map.items():
            if any(v.preset_key == current_key for v in entry.variants):
                default_value = group_value
                break
        else:
            if default_key and any(choice.value == default_key for choice in model_choices):
                default_value = default_key
            else:
                for group_value, entry in group_selection_map.items():
                    if any(v.preset_key == default_key for v in entry.variants):
                        default_value = group_value
                        break

    return ModelChoiceState(
        choices=model_choices,
        group_selection_map=group_selection_map,
        default_value=default_value,
    )


def select_variant(group_selection: GroupSelection) -> str | None:
    """Prompt for a specific variant inside a grouped choice."""

    variant_choices: list[questionary.Choice] = []
    for variant in group_selection.variants:
        variant_title = variant.variant_display
        if variant.preset_key == group_selection.default_key:
            variant_title += " (default)"
        if variant.preset_key == group_selection.current_key:
            variant_title += " [current]"
        variant_choices.append(
            model_variant_choice(
                variant_title,
                variant.variant_display,
                group_selection.provider_display,
                value=variant.preset_key,
            )
        )

    preferred_default = group_selection.current_key or group_selection.default_key
    if not preferred_default or not any(choice.value == preferred_default for choice in variant_choices):
        preferred_default = variant_choices[0].value if variant_choices else None

    if not variant_choices or preferred_default is None:
        return None

    return questionary.select(
        f"{group_selection.base_label} [{group_selection.provider_display}] – choose variant:",
        choices=variant_choices,
        default=preferred_default,
        qmark="🧠",
        style=CLI_STYLE,
    ).ask()
