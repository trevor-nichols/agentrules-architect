"""Configuration helpers consumed by interactive CLI flows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from agentrules import model_config
from agentrules.config_service import (
    PROVIDER_ENV_MAP,
    get_current_provider_keys,
    set_phase_model,
    set_provider_key,
)


@dataclass(frozen=True)
class ProviderState:
    """Represents a persisted provider configuration entry."""

    name: str
    env_var: str
    api_key: Optional[str]


def list_provider_states() -> list[ProviderState]:
    keys = get_current_provider_keys()
    return [
        ProviderState(name=provider, env_var=env_var, api_key=keys.get(provider))
        for provider, env_var in PROVIDER_ENV_MAP.items()
    ]


def save_provider_key(provider: str, api_key: Optional[str]) -> None:
    set_provider_key(provider, api_key)
    model_config.apply_user_overrides()


def get_provider_keys() -> Dict[str, Optional[str]]:
    return get_current_provider_keys()


def get_active_presets(overrides: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    return model_config.get_active_presets(overrides)


def get_available_presets_for_phase(
    phase: str,
    provider_keys: Optional[Dict[str, Optional[str]]] = None,
):
    return model_config.get_available_presets_for_phase(phase, provider_keys)


def save_phase_model(phase: str, preset_key: Optional[str]) -> None:
    set_phase_model(phase, preset_key)


def apply_model_overrides(overrides: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    return model_config.apply_user_overrides(overrides)
