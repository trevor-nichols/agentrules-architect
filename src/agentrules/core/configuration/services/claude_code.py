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
from typing import Literal

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


ClaudeCodeExecutableSource = Literal["configured", "sdk_bundled", "path"]
ClaudeCodeVersionProbeError = Literal["timeout", "execution", "nonzero_exit", "parse"]
_ClaudeCodeExecutableFingerprint = tuple[int, int, int, int]


@dataclass(frozen=True)
class ClaudeCodeExecutable:
    path: str
    source: ClaudeCodeExecutableSource


@dataclass(frozen=True)
class ClaudeCodeVersionProbe:
    version: ClaudeCodeVersion | None
    error_code: ClaudeCodeVersionProbeError | None = None
    error_message: str | None = None


_CLAUDE_CODE_VERSION_PATTERN = re.compile(r"(?<!\d)(\d+)\.(\d+)\.(\d+)(?!\d)")
CLAUDE_CODE_VERSION_PROBE_TIMEOUT_SECONDS = 10.0
_MINIMUM_CLAUDE_CODE_VERSIONS: tuple[tuple[str, ClaudeCodeVersion], ...] = (
    ("claude-sonnet-5", ClaudeCodeVersion(2, 1, 197)),
    ("claude-fable-5", ClaudeCodeVersion(2, 1, 170)),
    ("fable", ClaudeCodeVersion(2, 1, 170)),
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


def resolve_claude_code_executable_info(config: CLIConfig) -> ClaudeCodeExecutable | None:
    """Resolve the exact executable and describe which resolution branch selected it."""

    executable_path = resolve_claude_code_executable(config)
    if executable_path is None:
        return None
    if get_claude_code_config(config).cli_path is not None:
        return ClaudeCodeExecutable(path=executable_path, source="configured")

    bundled_path = _resolve_sdk_bundled_executable()
    if bundled_path == executable_path:
        return ClaudeCodeExecutable(path=executable_path, source="sdk_bundled")
    return ClaudeCodeExecutable(path=executable_path, source="path")


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


def _claude_code_executable_fingerprint(
    executable_path: str,
) -> _ClaudeCodeExecutableFingerprint | None:
    try:
        executable_stat = Path(executable_path).stat()
    except OSError:
        return None
    return (
        executable_stat.st_dev,
        executable_stat.st_ino,
        executable_stat.st_size,
        executable_stat.st_mtime_ns,
    )


@lru_cache(maxsize=8)
def _cached_claude_code_version_probe(
    executable_path: str,
    timeout_seconds: float,
    env_vars_to_remove: tuple[str, ...],
    _executable_fingerprint: _ClaudeCodeExecutableFingerprint | None,
) -> ClaudeCodeVersionProbe:
    child_env = os.environ.copy()
    for env_var in env_vars_to_remove:
        child_env.pop(env_var, None)

    try:
        completed = subprocess.run(
            [executable_path, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=child_env,
        )
    except subprocess.TimeoutExpired:
        return ClaudeCodeVersionProbe(
            version=None,
            error_code="timeout",
            error_message=f"Version probe timed out after {timeout_seconds:g} seconds.",
        )
    except OSError as exc:
        return ClaudeCodeVersionProbe(
            version=None,
            error_code="execution",
            error_message=f"Version probe could not execute the resolved runtime: {exc}",
        )

    if completed.returncode != 0:
        detail = _bounded_probe_output(completed.stderr or completed.stdout)
        message = f"Version probe exited with status {completed.returncode}."
        if detail:
            message = f"{message} {detail}"
        return ClaudeCodeVersionProbe(
            version=None,
            error_code="nonzero_exit",
            error_message=message,
        )
    version_text = (completed.stdout or completed.stderr).strip()
    version = parse_claude_code_version(version_text)
    if version is None:
        detail = _bounded_probe_output(version_text) or "empty output"
        return ClaudeCodeVersionProbe(
            version=None,
            error_code="parse",
            error_message=f"Version probe output did not contain a semantic version: {detail}",
        )
    return ClaudeCodeVersionProbe(version=version)


def clear_claude_code_version_probe_cache() -> None:
    """Invalidate cached Claude Code executable version probes."""

    _cached_claude_code_version_probe.cache_clear()


def probe_claude_code_executable_version(
    executable_path: str,
    timeout_seconds: float = CLAUDE_CODE_VERSION_PROBE_TIMEOUT_SECONDS,
    *,
    env_vars_to_remove: tuple[str, ...] = (),
) -> ClaudeCodeVersionProbe:
    """Return a diagnostic version probe for one resolved executable."""

    probe = _cached_claude_code_version_probe(
        executable_path,
        timeout_seconds,
        env_vars_to_remove,
        _claude_code_executable_fingerprint(executable_path),
    )
    if probe.version is None:
        clear_claude_code_version_probe_cache()
    return probe


def _bounded_probe_output(value: str | None, *, limit: int = 300) -> str:
    normalized = " ".join((value or "").split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 1]}…"


def _probe_claude_code_executable_version(
    executable_path: str,
    *,
    env_vars_to_remove: tuple[str, ...] = (),
) -> ClaudeCodeVersion | None:
    """Compatibility wrapper for callers that only need the parsed version."""

    return probe_claude_code_executable_version(
        executable_path,
        env_vars_to_remove=env_vars_to_remove,
    ).version


def get_claude_code_runtime_version(config: CLIConfig) -> ClaudeCodeVersion | None:
    executable_path = resolve_claude_code_executable(config)
    if executable_path is None:
        return None
    return _probe_claude_code_executable_version(
        executable_path,
        env_vars_to_remove=_claude_code_env_vars_to_remove(config),
    )


def get_claude_code_runtime_version_probe(
    config: CLIConfig,
    *,
    timeout_seconds: float = CLAUDE_CODE_VERSION_PROBE_TIMEOUT_SECONDS,
) -> ClaudeCodeVersionProbe | None:
    executable_path = resolve_claude_code_executable(config)
    if executable_path is None:
        return None
    return probe_claude_code_executable_version(
        executable_path,
        timeout_seconds,
        env_vars_to_remove=_claude_code_env_vars_to_remove(config),
    )


def minimum_claude_code_version_for_model(model_name: str) -> ClaudeCodeVersion | None:
    normalized = model_name.strip().lower()
    for family_prefix, minimum_version in _MINIMUM_CLAUDE_CODE_VERSIONS:
        if normalized == family_prefix or normalized.startswith(f"{family_prefix}-"):
            return minimum_version
    return None


def claude_code_model_support_error(config: CLIConfig, model_name: str) -> str | None:
    minimum_version = minimum_claude_code_version_for_model(model_name)
    if minimum_version is None:
        return None

    runtime_version = get_claude_code_runtime_version(config)
    if runtime_version is None:
        return (
            f"Model '{model_name}' requires Claude Code {minimum_version} or later, but the resolved "
            "runtime version could not be verified."
        )
    if runtime_version < minimum_version:
        return (
            f"Model '{model_name}' requires Claude Code {minimum_version} or later, "
            f"but the resolved runtime reports {runtime_version}."
        )
    return None


def is_claude_code_model_supported(config: CLIConfig, model_name: str) -> bool:
    return claude_code_model_support_error(config, model_name) is None


def build_claude_code_environment(
    config: CLIConfig,
    environ: Mapping[str, str],
) -> dict[str, str]:
    env = dict(environ)
    for env_var in _claude_code_env_vars_to_remove(config):
        env.pop(env_var, None)
    return env


def _claude_code_env_vars_to_remove(config: CLIConfig) -> tuple[str, ...]:
    claude_code_config = get_claude_code_config(config)
    if claude_code_config.auth_strategy == "oauth" and claude_code_config.sanitize_api_key_env:
        return configuration_constants.CLAUDE_CODE_API_KEY_ENV_VARS
    return ()
