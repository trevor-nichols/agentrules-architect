"""Output preference helpers."""

from __future__ import annotations

from agentrules.core.utils.constants import DEFAULT_RULES_FILENAME

from ..models import CLIConfig, OutputPreferences
from ..utils import normalize_rules_filename


def get_output_preferences(config: CLIConfig) -> OutputPreferences:
    return config.outputs


def set_generate_cursorignore(config: CLIConfig, enabled: bool) -> None:
    config.outputs.generate_cursorignore = bool(enabled)


def should_generate_cursorignore(config: CLIConfig, default: bool = False) -> bool:
    return bool(config.outputs.generate_cursorignore) if config.outputs else default


def set_generate_agent_scaffold(config: CLIConfig, enabled: bool) -> None:
    config.outputs.generate_agent_scaffold = bool(enabled)


def should_generate_agent_scaffold(config: CLIConfig, default: bool = False) -> bool:
    return bool(config.outputs.generate_agent_scaffold) if config.outputs else default


def set_generate_phase_outputs(config: CLIConfig, enabled: bool) -> None:
    config.outputs.generate_phase_outputs = bool(enabled)


def should_generate_phase_outputs(config: CLIConfig, default: bool = True) -> bool:
    return bool(config.outputs.generate_phase_outputs) if config.outputs else default


def get_rules_filename(config: CLIConfig, default: str = DEFAULT_RULES_FILENAME) -> str:
    current = config.outputs.rules_filename if config.outputs else None
    normalized = normalize_rules_filename(current, default=default)
    if config.outputs:
        config.outputs.rules_filename = normalized
    return normalized


def set_rules_filename(config: CLIConfig, name: str) -> None:
    config.outputs.rules_filename = normalize_rules_filename(name, default=DEFAULT_RULES_FILENAME)
