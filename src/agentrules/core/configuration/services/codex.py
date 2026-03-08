"""Codex runtime configuration helpers."""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable
from pathlib import Path

from .. import constants as configuration_constants
from ..models import CLIConfig, CodexConfig, CodexHomeStrategy
from ..utils import normalize_codex_home_strategy, normalize_optional_string


def get_codex_config(config: CLIConfig) -> CodexConfig:
    normalized = CodexConfig(
        cli_path=normalize_optional_string(config.codex.cli_path)
        or configuration_constants.DEFAULT_CODEX_CLI_PATH,
        home_strategy=normalize_codex_home_strategy(config.codex.home_strategy, default="managed"),
        managed_home=normalize_optional_string(config.codex.managed_home),
    )
    config.codex = normalized
    return normalized


def set_codex_cli_path(config: CLIConfig, cli_path: str | None) -> None:
    current = get_codex_config(config)
    config.codex = current.__class__(
        cli_path=normalize_optional_string(cli_path) or configuration_constants.DEFAULT_CODEX_CLI_PATH,
        home_strategy=current.home_strategy,
        managed_home=current.managed_home,
    )


def set_codex_home_strategy(config: CLIConfig, strategy: str | None) -> None:
    current = get_codex_config(config)
    config.codex = current.__class__(
        cli_path=current.cli_path,
        home_strategy=normalize_codex_home_strategy(strategy, default="managed"),
        managed_home=current.managed_home,
    )


def set_codex_managed_home(config: CLIConfig, managed_home: str | None) -> None:
    current = get_codex_config(config)
    config.codex = current.__class__(
        cli_path=current.cli_path,
        home_strategy=current.home_strategy,
        managed_home=normalize_optional_string(managed_home),
    )


def get_codex_home_strategy(config: CLIConfig) -> CodexHomeStrategy:
    return get_codex_config(config).home_strategy


def get_managed_codex_home(config: CLIConfig) -> str:
    codex_config = get_codex_config(config)
    configured = codex_config.managed_home
    if configured:
        return str(Path(configured).expanduser())
    return str(configuration_constants.CONFIG_DIR / configuration_constants.DEFAULT_CODEX_HOME_DIRNAME)


def get_effective_codex_home(
    config: CLIConfig,
    getenv: Callable[[str], str | None],
) -> str | None:
    codex_config = get_codex_config(config)
    if codex_config.home_strategy == "inherit":
        inherited = normalize_optional_string(getenv(configuration_constants.CODEX_HOME_ENV_VAR))
        if inherited:
            return str(Path(inherited).expanduser())
        return None
    return get_managed_codex_home(config)


def resolve_codex_executable(config: CLIConfig) -> str | None:
    cli_path = get_codex_config(config).cli_path
    expanded = os.path.expanduser(cli_path)
    if os.path.sep in expanded or (os.path.altsep and os.path.altsep in expanded):
        candidate = Path(expanded)
        if candidate.exists() and candidate.is_file():
            return str(candidate)
        return None
    return shutil.which(expanded)


def is_codex_available(config: CLIConfig) -> bool:
    return resolve_codex_executable(config) is not None
