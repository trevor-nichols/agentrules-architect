"""Configuration helpers consumed by interactive CLI flows."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from agentrules import model_config
from agentrules.config_service import (
    PROVIDER_ENV_MAP,
    OutputPreferences,
    add_exclusion_entry,
    get_current_provider_keys,
    get_effective_exclusions,
    get_exclusion_overrides,
    get_logging_verbosity,
    get_rules_filename,
    remove_exclusion_entry,
    reset_exclusions,
    set_generate_cursorignore,
    set_generate_phase_outputs,
    set_logging_verbosity,
    set_phase_model,
    set_provider_key,
    set_respect_gitignore,
    set_rules_filename,
    should_respect_gitignore,
)
from agentrules.config_service import (
    get_output_preferences as load_output_preferences,
)
from agentrules.config_service import (
    should_generate_cursorignore as is_cursorignore_enabled,
)
from agentrules.config_service import (
    should_generate_phase_outputs as is_phase_outputs_enabled,
)


@dataclass(frozen=True)
class ProviderState:
    """Represents a persisted provider configuration entry."""

    name: str
    env_var: str
    api_key: str | None


def list_provider_states() -> list[ProviderState]:
    keys = get_current_provider_keys()
    return [
        ProviderState(name=provider, env_var=env_var, api_key=keys.get(provider))
        for provider, env_var in PROVIDER_ENV_MAP.items()
    ]


def save_provider_key(provider: str, api_key: str | None) -> None:
    set_provider_key(provider, api_key)
    model_config.apply_user_overrides()


def get_provider_keys() -> dict[str, str | None]:
    return get_current_provider_keys()


def get_active_presets(overrides: Mapping[str, str] | None = None) -> dict[str, str]:
    return model_config.get_active_presets(overrides)


def get_available_presets_for_phase(
    phase: str,
    provider_keys: Mapping[str, str | None] | None = None,
):
    return model_config.get_available_presets_for_phase(phase, provider_keys)


def save_phase_model(phase: str, preset_key: str | None) -> None:
    set_phase_model(phase, preset_key)


def apply_model_overrides(overrides: Mapping[str, str] | None = None) -> dict[str, str]:
    return model_config.apply_user_overrides(overrides)


def get_logging_preference() -> str | None:
    return get_logging_verbosity()


def save_logging_preference(value: str | None) -> None:
    set_logging_verbosity(value)


def get_output_preferences() -> OutputPreferences:
    return load_output_preferences()


def save_generate_cursorignore_preference(enabled: bool) -> None:
    set_generate_cursorignore(enabled)


def is_cursorignore_generation_enabled() -> bool:
    return is_cursorignore_enabled()


def save_generate_phase_outputs_preference(enabled: bool) -> None:
    set_generate_phase_outputs(enabled)


def are_phase_outputs_enabled() -> bool:
    return is_phase_outputs_enabled()


def get_rules_file_name() -> str:
    return get_rules_filename()


def save_rules_file_name(name: str) -> None:
    set_rules_filename(name)


def get_exclusion_settings():
    overrides = get_exclusion_overrides()
    effective_dirs, effective_files, effective_exts = get_effective_exclusions()
    return {
        "overrides": overrides,
        "effective": {
            "directories": sorted(effective_dirs),
            "files": sorted(effective_files),
            "extensions": sorted(effective_exts),
        },
    }


def add_custom_exclusion(kind: str, value: str) -> str | None:
    return add_exclusion_entry(kind, value)


def remove_custom_exclusion(kind: str, value: str) -> str | None:
    return remove_exclusion_entry(kind, value)


def reset_custom_exclusions() -> None:
    reset_exclusions()


def save_respect_gitignore(enabled: bool) -> None:
    set_respect_gitignore(enabled)


def is_gitignore_respected() -> bool:
    return should_respect_gitignore()
