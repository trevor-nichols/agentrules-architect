"""
Runtime configuration package for agentrules.

Exposes a cohesive facade for caller code while keeping persistence, domain
policies, and environment concerns properly segmented by module.
"""

from __future__ import annotations

from functools import lru_cache

from .constants import (
    CONFIG_DIR,
    CONFIG_FILE,
    DEFAULT_VERBOSITY,
    PROVIDER_ENV_MAP,
    TRUTHY_ENV_VALUES,
    VERBOSITY_ENV_VAR,
    VERBOSITY_PRESETS,
)
from .manager import ConfigManager
from .models import (
    CLIConfig,
    ExclusionOverrides,
    FeatureToggles,
    OutputPreferences,
    ProviderConfig,
    ResearcherMode,
)

__all__ = [
    "CLIConfig",
    "ConfigManager",
    "CONFIG_DIR",
    "CONFIG_FILE",
    "DEFAULT_VERBOSITY",
    "ExclusionOverrides",
    "FeatureToggles",
    "OutputPreferences",
    "PROVIDER_ENV_MAP",
    "ProviderConfig",
    "ResearcherMode",
    "TRUTHY_ENV_VALUES",
    "VERBOSITY_ENV_VAR",
    "VERBOSITY_PRESETS",
    "get_config_manager",
    "model_presets",
]


@lru_cache(maxsize=1)
def get_config_manager() -> ConfigManager:
    """Return the process-wide configuration manager singleton."""
    return ConfigManager()

# Import after defining get_config_manager to avoid circular imports in submodules.
from . import model_presets  # noqa: E402
