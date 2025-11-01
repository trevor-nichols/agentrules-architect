"""
Configuration management for the agentrules CLI.

Stores API keys and user preferences in ``~/.config/agentrules/config.toml`` (or the
platform equivalent) so the interactive CLI can persist settings between runs.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, cast

try:  # Python 3.11+ ships tomllib in the standard library
    import tomllib as tomli  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - exercised on older interpreters
    import tomli  # type: ignore[no-redef]
import tomli_w
from platformdirs import user_config_dir

from agentrules.config.exclusions import EXCLUDED_DIRS, EXCLUDED_EXTENSIONS, EXCLUDED_FILES
from agentrules.core.utils.constants import DEFAULT_RULES_FILENAME

CONFIG_DIR = Path(os.getenv("AGENTRULES_CONFIG_DIR", user_config_dir("agentrules", "cursorrules")))
CONFIG_FILE = CONFIG_DIR / "config.toml"
DEFAULT_VERBOSITY = "quiet"

PROVIDER_ENV_MAP = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "xai": "XAI_API_KEY",
    "tavily": "TAVILY_API_KEY",
}

VERBOSITY_ENV_VAR = "AGENTRULES_LOG_LEVEL"
VERBOSITY_PRESETS = {
    "quiet": logging.WARNING,
    "standard": logging.INFO,
    "verbose": logging.DEBUG,
}

TRUTHY_ENV_VALUES = {"1", "true", "yes", "on"}

ResearcherMode = Literal["auto", "on", "off"]


@dataclass
class ProviderConfig:
    api_key: str | None = None


@dataclass
class OutputPreferences:
    generate_cursorignore: bool = False
    generate_phase_outputs: bool = True
    rules_filename: str = DEFAULT_RULES_FILENAME


@dataclass
class ExclusionOverrides:
    respect_gitignore: bool = True
    add_directories: list[str] = field(default_factory=list)
    remove_directories: list[str] = field(default_factory=list)
    add_files: list[str] = field(default_factory=list)
    remove_files: list[str] = field(default_factory=list)
    add_extensions: list[str] = field(default_factory=list)
    remove_extensions: list[str] = field(default_factory=list)
    tree_max_depth: int | None = None

    def is_empty(self) -> bool:
        override_lists = (
            self.add_directories,
            self.remove_directories,
            self.add_files,
            self.remove_files,
            self.add_extensions,
            self.remove_extensions,
        )
        depth_overridden = self.tree_max_depth is not None
        return self.respect_gitignore and not any(override_lists) and not depth_overridden


@dataclass
class FeatureToggles:
    researcher_mode: ResearcherMode = "auto"

    def is_default(self) -> bool:
        return self.researcher_mode == "auto"


@dataclass
class CLIConfig:
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    models: dict[str, str] = field(default_factory=dict)
    verbosity: str | None = None
    outputs: OutputPreferences = field(default_factory=OutputPreferences)
    exclusions: ExclusionOverrides = field(default_factory=ExclusionOverrides)
    features: FeatureToggles = field(default_factory=FeatureToggles)

    @classmethod
    def from_dict(cls, payload: dict) -> CLIConfig:
        providers = {
            provider: ProviderConfig(**values) if isinstance(values, dict) else ProviderConfig(api_key=values)
            for provider, values in payload.get("providers", {}).items()
        }
        models = {
            phase: preset
            for phase, preset in payload.get("models", {}).items()
            if isinstance(phase, str) and isinstance(preset, str)
        }
        verbosity = payload.get("verbosity")
        if verbosity is not None and not isinstance(verbosity, str):
            verbosity = None
        outputs_payload = payload.get("outputs")
        outputs = OutputPreferences(
            generate_cursorignore=_coerce_bool(
                outputs_payload.get("generate_cursorignore") if isinstance(outputs_payload, dict) else None,
                default=False,
            ),
            generate_phase_outputs=_coerce_bool(
                outputs_payload.get("generate_phase_outputs") if isinstance(outputs_payload, dict) else None,
                default=True,
            ),
            rules_filename=_normalize_rules_filename(
                outputs_payload.get("rules_filename") if isinstance(outputs_payload, dict) else None,
                default=DEFAULT_RULES_FILENAME,
            ),
        )
        exclusions_payload = payload.get("exclusions")
        exclusions = ExclusionOverrides(
            respect_gitignore=_coerce_bool(
                exclusions_payload.get("respect_gitignore") if isinstance(exclusions_payload, dict) else None,
                default=True,
            ),
            add_directories=_coerce_string_list(exclusions_payload, "directories"),
            remove_directories=_coerce_string_list(exclusions_payload, "remove_directories"),
            add_files=_coerce_string_list(exclusions_payload, "files"),
            remove_files=_coerce_string_list(exclusions_payload, "remove_files"),
            add_extensions=_coerce_string_list(exclusions_payload, "extensions"),
            remove_extensions=_coerce_string_list(exclusions_payload, "remove_extensions"),
            tree_max_depth=_coerce_positive_int(
                exclusions_payload.get("tree_max_depth")
                if isinstance(exclusions_payload, dict)
                else None,
                minimum=1,
                default=None,
            ),
        )
        features_payload = payload.get("features")
        features = FeatureToggles(
            researcher_mode=_normalize_researcher_mode(
                features_payload.get("researcher_mode") if isinstance(features_payload, dict) else None,
                default="auto",
            )
        )
        return cls(
            providers=providers,
            models=models,
            verbosity=verbosity,
            outputs=outputs,
            exclusions=exclusions,
            features=features,
        )

    def to_dict(self) -> dict:
        payload: dict[str, object] = {
            "providers": {
                name: {"api_key": cfg.api_key}
                for name, cfg in self.providers.items()
                if cfg.api_key
            }
        }
        if self.models:
            payload["models"] = dict(self.models)
        if self.verbosity:
            payload["verbosity"] = self.verbosity
        outputs_payload: dict[str, object] = {}
        if self.outputs.generate_cursorignore:
            outputs_payload["generate_cursorignore"] = True
        if not self.outputs.generate_phase_outputs:
            outputs_payload["generate_phase_outputs"] = False
        if self.outputs.rules_filename != DEFAULT_RULES_FILENAME:
            outputs_payload["rules_filename"] = self.outputs.rules_filename
        if outputs_payload:
            payload["outputs"] = outputs_payload
        if not self.exclusions.is_empty():
            exclusions_payload: dict[str, object] = {
                "directories": list(self.exclusions.add_directories),
                "remove_directories": list(self.exclusions.remove_directories),
                "files": list(self.exclusions.add_files),
                "remove_files": list(self.exclusions.remove_files),
                "extensions": list(self.exclusions.add_extensions),
                "remove_extensions": list(self.exclusions.remove_extensions),
            }
            if not self.exclusions.respect_gitignore:
                exclusions_payload["respect_gitignore"] = False
            if self.exclusions.tree_max_depth is not None:
                exclusions_payload["tree_max_depth"] = self.exclusions.tree_max_depth
            payload["exclusions"] = exclusions_payload
        if not self.features.is_default():
            features_payload = payload.setdefault("features", {})
            features_dict = cast(dict[str, object], features_payload)
            features_dict["researcher_mode"] = self.features.researcher_mode
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


def set_provider_key(provider: str, api_key: str | None) -> CLIConfig:
    config = load_config()
    config.providers[provider] = ProviderConfig(api_key=api_key)
    save_config(config)
    apply_config_to_environment(config)
    return config


def set_phase_model(phase: str, preset_key: str | None) -> CLIConfig:
    config = load_config()
    if preset_key and preset_key.strip():
        config.models[phase] = preset_key.strip()
    else:
        config.models.pop(phase, None)
    save_config(config)
    return config


def set_researcher_mode(mode: str | None) -> CLIConfig:
    config = load_config()
    config.features.researcher_mode = _normalize_researcher_mode(mode, default="auto")
    save_config(config)
    return config


def get_researcher_mode(default: ResearcherMode = "auto") -> ResearcherMode:
    config = load_config()
    normalized = _normalize_researcher_mode(config.features.researcher_mode, default=default)
    if normalized != config.features.researcher_mode:
        config.features.researcher_mode = normalized
        save_config(config)
    return normalized


def has_tavily_credentials(config: CLIConfig | None = None) -> bool:
    config = config or load_config()
    stored = config.providers.get("tavily")
    if stored and stored.api_key:
        return True
    env_var = PROVIDER_ENV_MAP.get("tavily")
    return bool(env_var and os.getenv(env_var))


def is_researcher_enabled(config: CLIConfig | None = None) -> bool:
    config = config or load_config()
    mode = _normalize_researcher_mode(config.features.researcher_mode, default="auto")

    offline_flag = os.getenv("OFFLINE")
    if offline_flag and offline_flag.strip().lower() in TRUTHY_ENV_VALUES:
        return True

    if mode == "on":
        return True
    if mode == "off":
        return False
    return has_tavily_credentials(config)


def set_logging_verbosity(verbosity: str | None) -> CLIConfig:
    config = load_config()
    config.verbosity = _normalize_verbosity_label(verbosity) or None
    save_config(config)
    return config


def get_logging_verbosity() -> str | None:
    config = load_config()
    return config.verbosity


def get_output_preferences() -> OutputPreferences:
    config = load_config()
    return config.outputs


def get_exclusion_overrides() -> ExclusionOverrides:
    config = load_config()
    return config.exclusions


def set_generate_cursorignore(enabled: bool) -> CLIConfig:
    config = load_config()
    config.outputs.generate_cursorignore = bool(enabled)
    save_config(config)
    return config


def should_generate_cursorignore(default: bool = False) -> bool:
    config = load_config()
    if config.outputs is None:
        return default
    return bool(config.outputs.generate_cursorignore)


def set_generate_phase_outputs(enabled: bool) -> CLIConfig:
    config = load_config()
    config.outputs.generate_phase_outputs = bool(enabled)
    save_config(config)
    return config


def should_generate_phase_outputs(default: bool = True) -> bool:
    config = load_config()
    if config.outputs is None:
        return default
    return bool(config.outputs.generate_phase_outputs)


def get_rules_filename(default: str = DEFAULT_RULES_FILENAME) -> str:
    config = load_config()
    filename = config.outputs.rules_filename if config.outputs else None
    normalized = _normalize_rules_filename(filename, default=default)
    if normalized != filename:
        config.outputs.rules_filename = normalized
        save_config(config)
    return normalized


def set_rules_filename(name: str) -> CLIConfig:
    config = load_config()
    config.outputs.rules_filename = _normalize_rules_filename(name, default=DEFAULT_RULES_FILENAME)
    save_config(config)
    return config


def get_effective_exclusions() -> tuple[set[str], set[str], set[str]]:
    config = load_config()
    overrides = config.exclusions
    dirs = _apply_overrides(set(EXCLUDED_DIRS), overrides.add_directories, overrides.remove_directories)
    files = _apply_overrides(set(EXCLUDED_FILES), overrides.add_files, overrides.remove_files)
    exts = _apply_overrides(set(EXCLUDED_EXTENSIONS), overrides.add_extensions, overrides.remove_extensions)
    return dirs, files, exts


def add_exclusion_entry(kind: str, value: str) -> str | None:
    config = load_config()
    overrides = config.exclusions
    normalized = _normalize_exclusion_value(kind, value)
    if normalized is None:
        return None

    add_attr, remove_attr = _exclusion_attr_names(kind)
    add_list = getattr(overrides, add_attr)
    remove_list = getattr(overrides, remove_attr)

    if normalized not in add_list:
        add_list.append(normalized)
    if normalized in remove_list:
        remove_list.remove(normalized)

    save_config(config)
    return normalized


def remove_exclusion_entry(kind: str, value: str) -> str | None:
    config = load_config()
    overrides = config.exclusions
    normalized = _normalize_exclusion_value(kind, value)
    if normalized is None:
        return None

    add_attr, remove_attr = _exclusion_attr_names(kind)
    add_list = getattr(overrides, add_attr)
    remove_list = getattr(overrides, remove_attr)

    if normalized in add_list:
        add_list.remove(normalized)
    else:
        if normalized not in remove_list:
            remove_list.append(normalized)

    save_config(config)
    return normalized


def reset_exclusions() -> CLIConfig:
    config = load_config()
    config.exclusions = ExclusionOverrides()
    save_config(config)
    return config


def set_respect_gitignore(enabled: bool) -> CLIConfig:
    config = load_config()
    config.exclusions.respect_gitignore = bool(enabled)
    save_config(config)
    return config


def should_respect_gitignore(default: bool = True) -> bool:
    config = load_config()
    if config.exclusions is None:
        return default
    return bool(config.exclusions.respect_gitignore)


def get_tree_max_depth(default: int = 4) -> int:
    config = load_config()
    overrides = config.exclusions
    depth = overrides.tree_max_depth
    if depth is None:
        return max(default, 1)
    return max(depth, 1)


def set_tree_max_depth(value: int | None) -> CLIConfig:
    if value is not None and value < 1:
        raise ValueError("tree depth must be at least 1")
    config = load_config()
    config.exclusions.tree_max_depth = value
    save_config(config)
    return config


def reset_tree_max_depth() -> CLIConfig:
    config = load_config()
    config.exclusions.tree_max_depth = None
    save_config(config)
    return config


def _coerce_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        return default
    return default


def _coerce_positive_int(
    value: object,
    *,
    minimum: int = 1,
    default: int | None = None,
) -> int | None:
    if value is None:
        return default
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value if value >= minimum else default
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return default
        if stripped.isdigit():
            parsed = int(stripped)
            return parsed if parsed >= minimum else default
        try:
            parsed = int(float(stripped))
        except ValueError:
            return default
        return parsed if parsed >= minimum else default
    return default
    if isinstance(value, int | float):
        return bool(value)
    return default


def _coerce_string_list(payload: object, key: str) -> list[str]:
    if not isinstance(payload, dict):
        return []
    value = payload.get(key)
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        if isinstance(item, str):
            stripped = item.strip()
            if stripped:
                result.append(stripped)
    return result


def _normalize_rules_filename(value: object, *, default: str) -> str:
    if isinstance(value, str) and value.strip():
        candidate = value.strip()
        if "/" in candidate or "\\" in candidate:
            # Disallow directory separators to keep the output within the target project root.
            return default
        return candidate
    return default


def _apply_overrides(
    base: set[str],
    additions: list[str],
    removals: list[str],
) -> set[str]:
    updated = set(base)
    for item in additions:
        if item:
            updated.add(item)
    for item in removals:
        if item in updated:
            updated.remove(item)
    return updated


def _normalize_exclusion_value(kind: str, value: str) -> str | None:
    if not value:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None

    if kind == "extensions":
        if "/" in cleaned or "\\" in cleaned:
            return None
        if not cleaned.startswith('.'):
            cleaned = f".{cleaned}"
        return cleaned

    if kind == "files":
        # Allow relative file names but ensure no directories to keep rule simple
        if "\n" in cleaned:
            return None
        return cleaned

    if kind == "directories":
        # For directories, forbid path separators to keep it a single directory name
        if "/" in cleaned or "\\" in cleaned:
            return None
        return cleaned

    return cleaned


def _exclusion_attr_names(kind: str) -> tuple[str, str]:
    mapping = {
        "directories": ("add_directories", "remove_directories"),
        "files": ("add_files", "remove_files"),
        "extensions": ("add_extensions", "remove_extensions"),
    }
    if kind not in mapping:
        raise ValueError(f"Unknown exclusion kind: {kind}")
    return mapping[kind]


def _normalize_researcher_mode(value: object, *, default: ResearcherMode) -> ResearcherMode:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"auto", "on", "off"}:
            return normalized  # type: ignore[return-value]
    return default


def _normalize_verbosity_label(label: str | None) -> str | None:
    if not label:
        return None
    normalized = label.strip().lower()
    if normalized in VERBOSITY_PRESETS:
        return normalized
    if normalized in {"warn", "warning"}:
        return "quiet"
    if normalized in {"info", "default", "standard"}:
        return "standard"
    if normalized in {"debug", "verbose"}:
        return "verbose"
    return None


def resolve_log_level(default: int | None = None) -> int:
    env_value = os.getenv(VERBOSITY_ENV_VAR)
    label = _normalize_verbosity_label(env_value)
    if label is None:
        label = _normalize_verbosity_label(get_logging_verbosity())

    if label is None:
        fallback = VERBOSITY_PRESETS[DEFAULT_VERBOSITY]
        return fallback if default is None else default

    level = VERBOSITY_PRESETS.get(label)
    if level is not None:
        return level

    fallback = VERBOSITY_PRESETS[DEFAULT_VERBOSITY]
    return fallback if default is None else default


def apply_config_to_environment(config: CLIConfig | None = None) -> None:
    config = config or load_config()
    for provider, cfg in config.providers.items():
        env_var = PROVIDER_ENV_MAP.get(provider)
        if not env_var or not cfg.api_key:
            continue
        if provider == "gemini":
            os.environ.pop("GEMINI_API_KEY", None)
        if not os.getenv(env_var):
            os.environ[env_var] = cfg.api_key


def get_current_provider_keys() -> dict[str, str | None]:
    config = load_config()
    keys: dict[str, str | None] = {}
    for provider in PROVIDER_ENV_MAP.keys():
        cfg = config.providers.get(provider, ProviderConfig())
        keys[provider] = cfg.api_key
    return keys


def get_model_overrides() -> dict[str, str]:
    config = load_config()
    return dict(config.models)
