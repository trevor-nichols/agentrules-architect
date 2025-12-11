"""Shared bootstrap helpers for CLI commands."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

from agentrules.core.configuration import get_config_manager, model_presets
from agentrules.core.logging import configure_logging

from .context import CliContext

CONFIG_MANAGER = get_config_manager()


def _load_env_files() -> None:
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)


def bootstrap_runtime() -> CliContext:
    """Configure logging, load configuration, and return a CLI context."""

    log_level = CONFIG_MANAGER.resolve_log_level()
    configure_logging(level=log_level)
    # Apply persisted config; do not ingest .env so config.toml is the single source of truth.
    CONFIG_MANAGER.apply_config_to_environment()
    model_presets.apply_user_overrides()

    console = Console()
    return CliContext(console=console)
