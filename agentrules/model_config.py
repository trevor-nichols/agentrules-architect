"""
Helpers for mapping user configuration to model presets.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from config import agents as agent_settings
from core.agents.base import ModelProvider

from agentrules.config_service import (
    PROVIDER_ENV_MAP,
    get_current_provider_keys,
    get_model_overrides,
)


PHASE_TITLES: Dict[str, str] = {
    "phase1": "Phase 1 – Initial Discovery",
    "phase2": "Phase 2 – Methodical Planning",
    "phase3": "Phase 3 – Deep Analysis",
    "phase4": "Phase 4 – Synthesis",
    "phase5": "Phase 5 – Consolidation",
    "final": "Final Analysis",
    "researcher": "Researcher Agent",
}

PHASE_SEQUENCE: List[str] = list(agent_settings.MODEL_PRESET_DEFAULTS.keys())


@dataclass(frozen=True)
class PresetInfo:
    key: str
    label: str
    description: str
    provider: ModelProvider

    @property
    def provider_slug(self) -> str:
        return self.provider.value

    @property
    def provider_display(self) -> str:
        return _provider_display_name(self.provider)


PRESET_INFOS: Dict[str, PresetInfo] = {
    key: PresetInfo(
        key=key,
        label=meta["label"],
        description=meta["description"],
        provider=meta["provider"],
    )
    for key, meta in agent_settings.MODEL_PRESETS.items()
}


def get_phase_title(phase: str) -> str:
    return PHASE_TITLES.get(phase, phase.title())


def get_default_preset_key(phase: str) -> Optional[str]:
    return agent_settings.MODEL_PRESET_DEFAULTS.get(phase)


def get_preset_info(key: str) -> Optional[PresetInfo]:
    return PRESET_INFOS.get(key)


def get_available_presets_for_phase(
    phase: str,
    provider_keys: Optional[Dict[str, Optional[str]]] = None,
) -> List[PresetInfo]:
    provider_keys = provider_keys or get_current_provider_keys()
    default_key = get_default_preset_key(phase)
    available: List[PresetInfo] = []

    for key, info in PRESET_INFOS.items():
        if key != default_key and not _provider_available(info.provider_slug, provider_keys):
            continue
        available.append(info)

    # Ensure default preset is present even if no keys are configured yet
    if default_key and not any(p.key == default_key for p in available):
        info = get_preset_info(default_key)
        if info:
            available.insert(0, info)

    return available


def get_active_presets(overrides: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    overrides = overrides or get_model_overrides()
    active: Dict[str, str] = {}
    for phase in PHASE_SEQUENCE:
        active[phase] = overrides.get(phase, get_default_preset_key(phase))
    return active


def apply_user_overrides(overrides: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Apply user-selected model presets to the global MODEL_CONFIG.
    Returns the applied preset mapping for further inspection.
    """
    overrides = overrides or get_model_overrides()
    applied: Dict[str, str] = {}

    # reset to defaults first
    for phase, preset_key in agent_settings.MODEL_PRESET_DEFAULTS.items():
        preset = agent_settings.MODEL_PRESETS[preset_key]["config"]
        agent_settings.MODEL_CONFIG[phase] = preset
        applied[phase] = preset_key

    # apply overrides when valid
    for phase, preset_key in overrides.items():
        if phase not in agent_settings.MODEL_PRESET_DEFAULTS:
            continue
        preset = agent_settings.MODEL_PRESETS.get(preset_key)
        if not preset:
            continue
        agent_settings.MODEL_CONFIG[phase] = preset["config"]
        applied[phase] = preset_key

    return applied


def _provider_available(provider_slug: str, provider_keys: Dict[str, Optional[str]]) -> bool:
    # first check persisted keys
    if provider_keys.get(provider_slug):
        return True

    env_var = PROVIDER_ENV_MAP.get(provider_slug)
    if env_var and os.getenv(env_var):
        return True

    return False


def _provider_display_name(provider: ModelProvider) -> str:
    mapping = {
        ModelProvider.OPENAI: "OpenAI",
        ModelProvider.ANTHROPIC: "Anthropic",
        ModelProvider.GEMINI: "Google Gemini",
        ModelProvider.DEEPSEEK: "DeepSeek",
    }
    return mapping.get(provider, provider.value.title())

