"""Configuration helpers consumed by interactive CLI flows."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from agentrules.core.configuration import (
    PROVIDER_ENV_MAP,
    OutputPreferences,
    get_config_manager,
    model_presets,
)

CONFIG_MANAGER = get_config_manager()


@dataclass(frozen=True)
class ProviderState:
    """Represents a persisted provider configuration entry."""

    name: str
    env_var: str
    api_key: str | None


def list_provider_states() -> list[ProviderState]:
    keys = CONFIG_MANAGER.get_current_provider_keys()
    return [
        ProviderState(name=provider, env_var=env_var, api_key=keys.get(provider))
        for provider, env_var in PROVIDER_ENV_MAP.items()
    ]


def save_provider_key(provider: str, api_key: str | None) -> None:
    CONFIG_MANAGER.set_provider_key(provider, api_key)
    model_presets.apply_user_overrides()


def get_provider_keys() -> dict[str, str | None]:
    return CONFIG_MANAGER.get_current_provider_keys()


def get_active_presets(overrides: Mapping[str, str] | None = None) -> dict[str, str]:
    return model_presets.get_active_presets(overrides)


def get_available_presets_for_phase(
    phase: str,
    provider_keys: Mapping[str, str | None] | None = None,
):
    return model_presets.get_available_presets_for_phase(phase, provider_keys)


def save_phase_model(phase: str, preset_key: str | None) -> None:
    CONFIG_MANAGER.set_phase_model(phase, preset_key)


def get_researcher_mode() -> str:
    return CONFIG_MANAGER.get_researcher_mode()


def save_researcher_mode(mode: str | None) -> None:
    CONFIG_MANAGER.set_researcher_mode(mode)


def has_tavily_credentials() -> bool:
    return CONFIG_MANAGER.has_tavily_credentials()


def is_researcher_active() -> bool:
    return CONFIG_MANAGER.is_researcher_enabled()


def apply_model_overrides(overrides: Mapping[str, str] | None = None) -> dict[str, str]:
    return model_presets.apply_user_overrides(overrides)


def get_logging_preference() -> str | None:
    return CONFIG_MANAGER.get_logging_verbosity()


def save_logging_preference(value: str | None) -> None:
    CONFIG_MANAGER.set_logging_verbosity(value)


def get_output_preferences() -> OutputPreferences:
    return CONFIG_MANAGER.get_output_preferences()


def save_generate_cursorignore_preference(enabled: bool) -> None:
    CONFIG_MANAGER.set_generate_cursorignore(enabled)


def is_cursorignore_generation_enabled() -> bool:
    return CONFIG_MANAGER.should_generate_cursorignore()


def save_generate_phase_outputs_preference(enabled: bool) -> None:
    CONFIG_MANAGER.set_generate_phase_outputs(enabled)


def are_phase_outputs_enabled() -> bool:
    return CONFIG_MANAGER.should_generate_phase_outputs()


def get_rules_file_name() -> str:
    return CONFIG_MANAGER.get_rules_filename()


def save_rules_file_name(name: str) -> None:
    CONFIG_MANAGER.set_rules_filename(name)


def get_exclusion_settings():
    overrides = CONFIG_MANAGER.get_exclusion_overrides()
    effective_dirs, effective_files, effective_exts = CONFIG_MANAGER.get_effective_exclusions()
    return {
        "overrides": overrides,
        "effective": {
            "directories": sorted(effective_dirs),
            "files": sorted(effective_files),
            "extensions": sorted(effective_exts),
        },
    }


def add_custom_exclusion(kind: str, value: str) -> str | None:
    return CONFIG_MANAGER.add_exclusion_entry(kind, value)


def remove_custom_exclusion(kind: str, value: str) -> str | None:
    return CONFIG_MANAGER.remove_exclusion_entry(kind, value)


def reset_custom_exclusions() -> None:
    CONFIG_MANAGER.reset_exclusions()


def save_respect_gitignore(enabled: bool) -> None:
    CONFIG_MANAGER.set_respect_gitignore(enabled)


def is_gitignore_respected() -> bool:
    return CONFIG_MANAGER.should_respect_gitignore()


def get_tree_traversal_depth() -> int:
    return CONFIG_MANAGER.get_tree_max_depth()


def save_tree_traversal_depth(value: int | None) -> None:
    CONFIG_MANAGER.set_tree_max_depth(value)


def reset_tree_traversal_depth() -> None:
    CONFIG_MANAGER.reset_tree_max_depth()
