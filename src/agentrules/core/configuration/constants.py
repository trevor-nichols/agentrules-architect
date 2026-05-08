"""Constants used throughout the configuration subsystem."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from platformdirs import user_config_dir

CONFIG_DIR = Path(os.getenv("AGENTRULES_CONFIG_DIR", user_config_dir("agentrules", "cursorrules")))
CONFIG_FILE = CONFIG_DIR / "config.toml"

DEFAULT_VERBOSITY = "quiet"
VERBOSITY_ENV_VAR = "AGENTRULES_LOG_LEVEL"
RULES_FILENAME_ENV_VAR = "AGENTRULES_RULES_FILENAME"
CODEX_HOME_ENV_VAR = "CODEX_HOME"
DEFAULT_CODEX_CLI_PATH = "codex"
DEFAULT_CODEX_HOME_DIRNAME = "codex"
DEFAULT_CLAUDE_CODE_CLI_PATH: str | None = None
CLAUDE_AGENT_SDK_IMPORT_NAME = "claude_agent_sdk"
DEFAULT_CLAUDE_CODE_MAX_TURNS = 12
DEFAULT_CLAUDE_CODE_REQUEST_TIMEOUT_SECONDS = 300.0
CLAUDE_CODE_OAUTH_TOKEN_ENV_VAR = "CLAUDE_CODE_OAUTH_TOKEN"
CLAUDE_CODE_API_KEY_ENV_VARS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")
VERBOSITY_PRESETS = {
    "quiet": logging.WARNING,
    "standard": logging.INFO,
    "verbose": logging.DEBUG,
}

PROVIDER_ENV_MAP = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "xai": "XAI_API_KEY",
    "tavily": "TAVILY_API_KEY",
}

TRUTHY_ENV_VALUES = {"1", "true", "yes", "on"}
