"""
Runtime configuration package for agentrules.

Exposes a cohesive facade for caller code while keeping persistence, domain
policies, and environment concerns properly segmented by module.
"""

from __future__ import annotations

from functools import lru_cache

from .constants import (
    CODEX_HOME_ENV_VAR,
    CONFIG_DIR,
    CONFIG_FILE,
    DEFAULT_CODEX_CLI_PATH,
    DEFAULT_CODEX_HOME_DIRNAME,
    DEFAULT_VERBOSITY,
    PROVIDER_ENV_MAP,
    RULES_FILENAME_ENV_VAR,
    TRUTHY_ENV_VALUES,
    VERBOSITY_ENV_VAR,
    VERBOSITY_PRESETS,
)
from .manager import ConfigManager
from .models import (
    CLIConfig,
    CodexConfig,
    CodexHomeStrategy,
    ExclusionOverrides,
    FeatureToggles,
    OutputPreferences,
    ProviderConfig,
    ResearcherMode,
)

__all__ = [
    "CLIConfig",
    "CODEX_HOME_ENV_VAR",
    "ConfigManager",
    "CONFIG_DIR",
    "CONFIG_FILE",
    "CodexConfig",
    "CodexHomeStrategy",
    "DEFAULT_CODEX_CLI_PATH",
    "DEFAULT_CODEX_HOME_DIRNAME",
    "DEFAULT_VERBOSITY",
    "ExclusionOverrides",
    "FeatureToggles",
    "OutputPreferences",
    "PROVIDER_ENV_MAP",
    "ProviderConfig",
    "ResearcherMode",
    "RULES_FILENAME_ENV_VAR",
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
