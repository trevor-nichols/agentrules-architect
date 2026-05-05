"""Claude Code runtime configuration helpers."""

from __future__ import annotations

import importlib.util
import os
import shutil
from collections.abc import Mapping
from pathlib import Path

from .. import constants as configuration_constants
from ..models import ClaudeCodeAuthStrategy, ClaudeCodeConfig, CLIConfig
from ..utils import (
    coerce_positive_float,
    coerce_positive_int,
    normalize_claude_code_auth_strategy,
    normalize_optional_string,
)


def get_claude_code_config(config: CLIConfig) -> ClaudeCodeConfig:
    normalized = ClaudeCodeConfig(
        cli_path=normalize_optional_string(config.claude_code.cli_path),
        auth_strategy=normalize_claude_code_auth_strategy(config.claude_code.auth_strategy, default="oauth"),
        sanitize_api_key_env=bool(config.claude_code.sanitize_api_key_env),
        max_turns=coerce_positive_int(
            config.claude_code.max_turns,
            minimum=1,
            default=configuration_constants.DEFAULT_CLAUDE_CODE_MAX_TURNS,
        )
        or configuration_constants.DEFAULT_CLAUDE_CODE_MAX_TURNS,
        request_timeout_seconds=coerce_positive_float(
            config.claude_code.request_timeout_seconds,
            minimum=0.0,
            default=configuration_constants.DEFAULT_CLAUDE_CODE_REQUEST_TIMEOUT_SECONDS,
        )
        or configuration_constants.DEFAULT_CLAUDE_CODE_REQUEST_TIMEOUT_SECONDS,
        max_budget_usd=coerce_positive_float(config.claude_code.max_budget_usd, minimum=0.0, default=None),
    )
    config.claude_code = normalized
    return normalized


def set_claude_code_cli_path(config: CLIConfig, cli_path: str | None) -> None:
    current = get_claude_code_config(config)
    config.claude_code = current.__class__(
        cli_path=normalize_optional_string(cli_path),
        auth_strategy=current.auth_strategy,
        sanitize_api_key_env=current.sanitize_api_key_env,
        max_turns=current.max_turns,
        request_timeout_seconds=current.request_timeout_seconds,
        max_budget_usd=current.max_budget_usd,
    )


def set_claude_code_auth_strategy(config: CLIConfig, strategy: str | None) -> None:
    current = get_claude_code_config(config)
    config.claude_code = current.__class__(
        cli_path=current.cli_path,
        auth_strategy=normalize_claude_code_auth_strategy(strategy, default="oauth"),
        sanitize_api_key_env=current.sanitize_api_key_env,
        max_turns=current.max_turns,
        request_timeout_seconds=current.request_timeout_seconds,
        max_budget_usd=current.max_budget_usd,
    )


def set_claude_code_sanitize_api_key_env(config: CLIConfig, enabled: bool) -> None:
    current = get_claude_code_config(config)
    config.claude_code = current.__class__(
        cli_path=current.cli_path,
        auth_strategy=current.auth_strategy,
        sanitize_api_key_env=bool(enabled),
        max_turns=current.max_turns,
        request_timeout_seconds=current.request_timeout_seconds,
        max_budget_usd=current.max_budget_usd,
    )


def get_claude_code_auth_strategy(config: CLIConfig) -> ClaudeCodeAuthStrategy:
    return get_claude_code_config(config).auth_strategy


def _is_executable_file(candidate: Path) -> bool:
    return candidate.exists() and candidate.is_file() and os.access(candidate, os.X_OK)


def resolve_claude_code_executable(config: CLIConfig) -> str | None:
    cli_path = get_claude_code_config(config).cli_path
    if cli_path is None:
        return None
    expanded = os.path.expanduser(cli_path)
    if os.path.sep in expanded or (os.path.altsep and os.path.altsep in expanded):
        candidate = Path(expanded)
        if _is_executable_file(candidate):
            return str(candidate.resolve())
        return None
    return shutil.which(expanded)


def is_claude_agent_sdk_available() -> bool:
    try:
        return importlib.util.find_spec(configuration_constants.CLAUDE_AGENT_SDK_IMPORT_NAME) is not None
    except (ImportError, ValueError):
        return False


def is_claude_code_available(config: CLIConfig) -> bool:
    claude_code_config = get_claude_code_config(config)
    if not is_claude_agent_sdk_available():
        return False
    if claude_code_config.cli_path is None:
        return True
    return resolve_claude_code_executable(config) is not None


def build_claude_code_environment(
    config: CLIConfig,
    environ: Mapping[str, str],
) -> dict[str, str]:
    env = dict(environ)
    claude_code_config = get_claude_code_config(config)
    if claude_code_config.auth_strategy == "oauth" and claude_code_config.sanitize_api_key_env:
        for env_var in configuration_constants.CLAUDE_CODE_API_KEY_ENV_VARS:
            env.pop(env_var, None)
    return env
