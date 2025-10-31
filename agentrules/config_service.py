"""
Configuration management for the agentrules CLI.

Stores API keys and user preferences in ``~/.config/agentrules/config.toml`` (or the
platform equivalent) so the interactive CLI can persist settings between runs.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

import tomli
import tomli_w
from platformdirs import user_config_dir


CONFIG_DIR = Path(os.getenv("AGENTRULES_CONFIG_DIR", user_config_dir("agentrules", "cursorrules")))
CONFIG_FILE = CONFIG_DIR / "config.toml"

PROVIDER_ENV_MAP = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "tavily": "TAVILY_API_KEY",
}


@dataclass
class ProviderConfig:
    api_key: Optional[str] = None


@dataclass
class CLIConfig:
    providers: Dict[str, ProviderConfig] = field(default_factory=dict)
    models: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Dict) -> "CLIConfig":
        providers = {
            provider: ProviderConfig(**values) if isinstance(values, dict) else ProviderConfig(api_key=values)
            for provider, values in payload.get("providers", {}).items()
        }
        models = {
            phase: preset
            for phase, preset in payload.get("models", {}).items()
            if isinstance(phase, str) and isinstance(preset, str)
        }
        return cls(providers=providers, models=models)

    def to_dict(self) -> Dict:
        payload: Dict[str, object] = {
            "providers": {
                name: {"api_key": cfg.api_key}
                for name, cfg in self.providers.items()
                if cfg.api_key
            }
        }
        if self.models:
            payload["models"] = dict(self.models)
        return payload


def load_config() -> CLIConfig:
    if not CONFIG_FILE.exists():
        return CLIConfig()

    with CONFIG_FILE.open("rb") as fh:
        data = tomli.load(fh)
    return CLIConfig.from_dict(data)


def save_config(config: CLIConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("wb") as fh:
        tomli_w.dump(config.to_dict(), fh)


def set_provider_key(provider: str, api_key: Optional[str]) -> CLIConfig:
    config = load_config()
    config.providers[provider] = ProviderConfig(api_key=api_key)
    save_config(config)
    apply_config_to_environment(config)
    return config


def set_phase_model(phase: str, preset_key: Optional[str]) -> CLIConfig:
    config = load_config()
    if preset_key and preset_key.strip():
        config.models[phase] = preset_key.strip()
    else:
        config.models.pop(phase, None)
    save_config(config)
    return config


def apply_config_to_environment(config: Optional[CLIConfig] = None) -> None:
    config = config or load_config()
    for provider, cfg in config.providers.items():
        env_var = PROVIDER_ENV_MAP.get(provider)
        if not env_var or not cfg.api_key:
            continue
        if not os.getenv(env_var):
            os.environ[env_var] = cfg.api_key


def get_current_provider_keys() -> Dict[str, Optional[str]]:
    config = load_config()
    keys: Dict[str, Optional[str]] = {}
    for provider in PROVIDER_ENV_MAP.keys():
        cfg = config.providers.get(provider, ProviderConfig())
        keys[provider] = cfg.api_key
    return keys


def get_model_overrides() -> Dict[str, str]:
    config = load_config()
    return dict(config.models)
