"""High-level facade for runtime configuration operations."""

from __future__ import annotations

from collections.abc import MutableMapping

from agentrules.core.utils.constants import DEFAULT_RULES_FILENAME

from .environment import EnvironmentManager
from .models import CLIConfig, ExclusionOverrides, OutputPreferences, ResearcherMode
from .repository import ConfigRepository, TomlConfigRepository
from .services import exclusions, features, outputs, phase_models, providers
from .services import logging as logging_service


class ConfigManager:
    """Coordinates persistence, policy helpers, and environment behavior."""

    def __init__(
        self,
        repository: ConfigRepository | None = None,
        environ: MutableMapping[str, str] | None = None,
    ) -> None:
        self._repository = repository or TomlConfigRepository()
        self._environment = EnvironmentManager(environ)

    # ------------------------------------------------------------------
    # Core persistence helpers
    # ------------------------------------------------------------------
    def load(self) -> CLIConfig:
        return self._repository.load()

    def save(self, config: CLIConfig) -> None:
        self._repository.save(config)

    def apply_config_to_environment(self, config: CLIConfig | None = None) -> None:
        cfg = config or self._repository.load()
        self._environment.apply_provider_credentials(cfg)

    # ------------------------------------------------------------------
    # Provider credentials
    # ------------------------------------------------------------------
    def set_provider_key(self, provider: str, api_key: str | None) -> CLIConfig:
        config = self._repository.load()
        providers.set_provider_key(config, provider, api_key)
        if provider == "tavily":
            if api_key:
                features.set_researcher_mode(config, "on")
            else:
                features.set_researcher_mode(config, "off")
        self._repository.save(config)
        self._environment.apply_provider_credentials(config)
        return config

    def get_current_provider_keys(self) -> dict[str, str | None]:
        config = self._repository.load()
        return providers.current_provider_keys(config)

    def has_tavily_credentials(self, config: CLIConfig | None = None) -> bool:
        cfg = config or self._repository.load()
        return providers.has_tavily_credentials(cfg, self._environment.getenv)

    # ------------------------------------------------------------------
    # Phase model overrides
    # ------------------------------------------------------------------
    def set_phase_model(self, phase: str, preset_key: str | None) -> CLIConfig:
        config = self._repository.load()
        phase_models.set_phase_model(config, phase, preset_key)
        self._repository.save(config)
        return config

    def get_model_overrides(self) -> dict[str, str]:
        config = self._repository.load()
        return phase_models.get_model_overrides(config)

    # ------------------------------------------------------------------
    # Researcher feature toggles
    # ------------------------------------------------------------------
    def set_researcher_mode(self, mode: str | None) -> CLIConfig:
        config = self._repository.load()
        features.set_researcher_mode(config, mode)
        self._repository.save(config)
        return config

    def get_researcher_mode(self, default: ResearcherMode = "off") -> ResearcherMode:
        config = self._repository.load()
        previous = config.features.researcher_mode
        normalized = features.get_researcher_mode(config, default)
        if normalized != previous:
            self._repository.save(config)
        return normalized

    def is_researcher_enabled(self) -> bool:
        config = self._repository.load()
        has_credentials = self.has_tavily_credentials(config)
        offline_mode = self._environment.is_truthy("OFFLINE")
        return features.is_researcher_enabled(
            config,
            offline_mode=offline_mode,
            has_tavily_credentials=has_credentials,
        )

    # ------------------------------------------------------------------
    # Logging preferences
    # ------------------------------------------------------------------
    def set_logging_verbosity(self, verbosity: str | None) -> CLIConfig:
        config = self._repository.load()
        logging_service.set_logging_verbosity(config, verbosity)
        self._repository.save(config)
        return config

    def get_logging_verbosity(self) -> str | None:
        config = self._repository.load()
        return logging_service.get_logging_verbosity(config)

    def resolve_log_level(self, default: int | None = None) -> int:
        config = self._repository.load()
        return self._environment.resolve_log_level(config, default)

    # ------------------------------------------------------------------
    # Output preferences
    # ------------------------------------------------------------------
    def get_output_preferences(self) -> OutputPreferences:
        config = self._repository.load()
        return outputs.get_output_preferences(config)

    def set_generate_cursorignore(self, enabled: bool) -> CLIConfig:
        config = self._repository.load()
        outputs.set_generate_cursorignore(config, enabled)
        self._repository.save(config)
        return config

    def should_generate_cursorignore(self, default: bool = False) -> bool:
        config = self._repository.load()
        return outputs.should_generate_cursorignore(config, default)

    def set_generate_agent_scaffold(self, enabled: bool) -> CLIConfig:
        config = self._repository.load()
        outputs.set_generate_agent_scaffold(config, enabled)
        self._repository.save(config)
        return config

    def should_generate_agent_scaffold(self, default: bool = False) -> bool:
        config = self._repository.load()
        return outputs.should_generate_agent_scaffold(config, default)

    def set_generate_phase_outputs(self, enabled: bool) -> CLIConfig:
        config = self._repository.load()
        outputs.set_generate_phase_outputs(config, enabled)
        self._repository.save(config)
        return config

    def should_generate_phase_outputs(self, default: bool = True) -> bool:
        config = self._repository.load()
        return outputs.should_generate_phase_outputs(config, default)

    def get_rules_filename(self, default: str | None = None) -> str:
        config = self._repository.load()
        fallback = default if default is not None else DEFAULT_RULES_FILENAME
        previous = config.outputs.rules_filename
        normalized = outputs.get_rules_filename(config, fallback)
        if normalized != previous:
            self._repository.save(config)
        return normalized

    def set_rules_filename(self, name: str) -> CLIConfig:
        config = self._repository.load()
        outputs.set_rules_filename(config, name)
        self._repository.save(config)
        return config

    # ------------------------------------------------------------------
    # Exclusions management
    # ------------------------------------------------------------------
    def get_exclusion_overrides(self) -> ExclusionOverrides:
        config = self._repository.load()
        return exclusions.get_exclusion_overrides(config)

    def get_effective_exclusions(self) -> tuple[set[str], set[str], set[str]]:
        config = self._repository.load()
        return exclusions.get_effective_exclusions(config)

    def add_exclusion_entry(self, kind: str, value: str) -> str | None:
        config = self._repository.load()
        normalized = exclusions.add_exclusion_entry(config, kind, value)
        if normalized is not None:
            self._repository.save(config)
        return normalized

    def remove_exclusion_entry(self, kind: str, value: str) -> str | None:
        config = self._repository.load()
        normalized = exclusions.remove_exclusion_entry(config, kind, value)
        if normalized is not None:
            self._repository.save(config)
        return normalized

    def reset_exclusions(self) -> CLIConfig:
        config = self._repository.load()
        exclusions.reset_exclusions(config)
        self._repository.save(config)
        return config

    def set_respect_gitignore(self, enabled: bool) -> CLIConfig:
        config = self._repository.load()
        exclusions.set_respect_gitignore(config, enabled)
        self._repository.save(config)
        return config

    def should_respect_gitignore(self, default: bool = True) -> bool:
        config = self._repository.load()
        return exclusions.should_respect_gitignore(config, default)

    def get_tree_max_depth(self, default: int = 5) -> int:
        config = self._repository.load()
        return exclusions.get_tree_max_depth(config, default)

    def set_tree_max_depth(self, value: int | None) -> CLIConfig:
        config = self._repository.load()
        exclusions.set_tree_max_depth(config, value)
        self._repository.save(config)
        return config

    def reset_tree_max_depth(self) -> CLIConfig:
        config = self._repository.load()
        exclusions.reset_tree_max_depth(config)
        self._repository.save(config)
        return config
