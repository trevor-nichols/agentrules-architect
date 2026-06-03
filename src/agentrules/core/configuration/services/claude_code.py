"""Claude Code runtime configuration helpers."""

from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .. import constants as configuration_constants
from ..models import ClaudeCodeAuthStrategy, ClaudeCodeConfig, CLIConfig
from ..utils import (
    coerce_positive_float,
    coerce_positive_int,
    normalize_claude_code_auth_strategy,
    normalize_optional_string,
)


@dataclass(frozen=True, order=True)
class ClaudeCodeVersion:
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


_CLAUDE_CODE_VERSION_PATTERN = re.compile(r"(?<!\d)(\d+)\.(\d+)\.(\d+)(?!\d)")
_MINIMUM_CLAUDE_CODE_VERSIONS: tuple[tuple[str, ClaudeCodeVersion], ...] = (
    ("claude-opus-4-8", ClaudeCodeVersion(2, 1, 154)),
    ("claude-opus-4-7", ClaudeCodeVersion(2, 1, 111)),
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
        return _resolve_sdk_default_executable()
    expanded = os.path.expanduser(cli_path)
    if os.path.sep in expanded or (os.path.altsep and os.path.altsep in expanded):
        candidate = Path(expanded)
        if _is_executable_file(candidate):
            return str(candidate.resolve())
        return None
    resolved = shutil.which(expanded)
    if resolved is None:
        return None
    return str(Path(resolved).resolve())


def _resolve_sdk_default_executable() -> str | None:
    bundled = _resolve_sdk_bundled_executable()
    if bundled is not None:
        return bundled

    resolved = shutil.which("claude")
    if resolved is not None:
        return str(Path(resolved).resolve())

    for candidate in _claude_code_default_locations():
        if _is_executable_file(candidate):
            return str(candidate.resolve())
    return None


def _resolve_sdk_bundled_executable() -> str | None:
    spec = importlib.util.find_spec(configuration_constants.CLAUDE_AGENT_SDK_IMPORT_NAME)
    if spec is None or spec.origin is None:
        return None

    cli_name = "claude.exe" if os.name == "nt" else "claude"
    candidate = Path(spec.origin).resolve().parent / "_bundled" / cli_name
    if _is_executable_file(candidate):
        return str(candidate.resolve())
    return None


def _claude_code_default_locations() -> tuple[Path, ...]:
    return (
        Path.home() / ".npm-global/bin/claude",
        Path("/usr/local/bin/claude"),
        Path.home() / ".local/bin/claude",
        Path.home() / "node_modules/.bin/claude",
        Path.home() / ".yarn/bin/claude",
        Path.home() / ".claude/local/claude",
    )


def is_claude_agent_sdk_available() -> bool:
    try:
        return importlib.util.find_spec(configuration_constants.CLAUDE_AGENT_SDK_IMPORT_NAME) is not None
    except (ImportError, ValueError):
        return False


def is_claude_code_available(config: CLIConfig) -> bool:
    if not is_claude_agent_sdk_available():
        return False
    return resolve_claude_code_executable(config) is not None


def parse_claude_code_version(version_text: str | None) -> ClaudeCodeVersion | None:
    if not version_text:
        return None
    match = _CLAUDE_CODE_VERSION_PATTERN.search(version_text.strip())
    if match is None:
        return None
    return ClaudeCodeVersion(*(int(part) for part in match.groups()))


@lru_cache(maxsize=8)
def _probe_claude_code_executable_version(executable_path: str) -> ClaudeCodeVersion | None:
    try:
        completed = subprocess.run(
            [executable_path, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2.0,
        )
    except Exception:
        return None

    if completed.returncode != 0:
        return None
    version_text = (completed.stdout or completed.stderr).strip()
    return parse_claude_code_version(version_text)


def get_claude_code_runtime_version(config: CLIConfig) -> ClaudeCodeVersion | None:
    executable_path = resolve_claude_code_executable(config)
    if executable_path is None:
        return None
    return _probe_claude_code_executable_version(executable_path)


def minimum_claude_code_version_for_model(model_name: str) -> ClaudeCodeVersion | None:
    normalized = model_name.strip().lower()
    for family_prefix, minimum_version in _MINIMUM_CLAUDE_CODE_VERSIONS:
        if normalized == family_prefix or normalized.startswith(f"{family_prefix}-"):
            return minimum_version
    return None


def is_claude_code_model_supported(config: CLIConfig, model_name: str) -> bool | None:
    minimum_version = minimum_claude_code_version_for_model(model_name)
    if minimum_version is None:
        return True

    runtime_version = get_claude_code_runtime_version(config)
    if runtime_version is None:
        return None
    return runtime_version >= minimum_version


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
