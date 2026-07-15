"""Synchronous helpers for inspecting the local Claude Code runtime."""

from __future__ import annotations

from dataclasses import dataclass

from agentrules.core.configuration import (
    CLAUDE_CODE_API_KEY_ENV_VARS,
    CLAUDE_CODE_OAUTH_TOKEN_ENV_VAR,
    ConfigManager,
    get_config_manager,
)
from agentrules.core.configuration.services import claude_code as claude_code_service

_DIAGNOSTIC_GATED_MODELS = ("claude-fable-5", "claude-sonnet-5")


@dataclass(frozen=True)
class ClaudeCodeRuntimeDiagnostics:
    cli_path: str | None
    executable_path: str | None
    sdk_available: bool
    auth_strategy: str
    sanitize_api_key_env: bool
    oauth_token_present: bool
    api_key_env_present_after_sanitization: bool
    executable_source: str | None = None
    version: str | None = None
    runtime_error: str | None = None
    version_error_code: str | None = None
    version_error: str | None = None
    unavailable_model_reasons: tuple[str, ...] = ()

    @property
    def is_available(self) -> bool:
        return self.sdk_available and self.runtime_error is None


def get_claude_code_runtime_diagnostics(
    *,
    config_manager: ConfigManager | None = None,
    timeout_seconds: float = claude_code_service.CLAUDE_CODE_VERSION_PROBE_TIMEOUT_SECONDS,
) -> ClaudeCodeRuntimeDiagnostics:
    manager = config_manager or get_config_manager()
    runtime_config = manager.get_claude_code_config()
    executable_path = manager.resolve_claude_code_executable()
    executable_info = manager.resolve_claude_code_executable_info()
    executable_source = (
        executable_info.source
        if executable_info is not None and executable_info.path == executable_path
        else "configured"
        if runtime_config.cli_path is not None and executable_path is not None
        else "path"
        if executable_path is not None
        else None
    )
    sdk_available = manager.is_claude_agent_sdk_available()
    child_env = manager.build_claude_code_environment()

    version: str | None = None
    version_error_code: str | None = None
    version_error: str | None = None
    runtime_error: str | None = None
    unavailable_model_reasons: tuple[str, ...] = ()

    if not sdk_available:
        runtime_error = "Claude Agent SDK package could not be imported in the AgentRules environment."
    elif executable_path is None:
        if runtime_config.cli_path is None:
            runtime_error = "Claude Code executable could not be resolved from the SDK default runtime settings."
        else:
            runtime_error = "Configured Claude Code executable could not be resolved from the current settings."
    else:
        probe = manager.get_claude_code_runtime_version_probe(timeout_seconds=timeout_seconds)
        if probe is None:
            runtime_error = "Claude Code executable could not be resolved during the version probe."
        else:
            version = str(probe.version) if probe.version is not None else None
            version_error_code = probe.error_code
            version_error = probe.error_message
            unavailable_model_reasons = _unavailable_model_reasons(manager, probe.version)

    return ClaudeCodeRuntimeDiagnostics(
        cli_path=runtime_config.cli_path,
        executable_path=executable_path,
        sdk_available=sdk_available,
        auth_strategy=runtime_config.auth_strategy,
        sanitize_api_key_env=runtime_config.sanitize_api_key_env,
        oauth_token_present=CLAUDE_CODE_OAUTH_TOKEN_ENV_VAR in child_env,
        api_key_env_present_after_sanitization=any(env_var in child_env for env_var in CLAUDE_CODE_API_KEY_ENV_VARS),
        executable_source=executable_source,
        version=version,
        runtime_error=runtime_error,
        version_error_code=version_error_code,
        version_error=version_error,
        unavailable_model_reasons=unavailable_model_reasons,
    )


def clear_claude_code_runtime_version_probe_cache() -> None:
    """Invalidate version data before an operator-requested runtime refresh."""

    claude_code_service.clear_claude_code_version_probe_cache()


def _unavailable_model_reasons(
    manager: ConfigManager,
    runtime_version: claude_code_service.ClaudeCodeVersion | None,
) -> tuple[str, ...]:
    reasons: list[str] = []
    for model_name in _DIAGNOSTIC_GATED_MODELS:
        minimum = manager.minimum_claude_code_version_for_model(model_name)
        if minimum is None:
            continue
        if runtime_version is None:
            reasons.append(f"{model_name}: needs {minimum}+; runtime version is unverified")
        elif runtime_version < minimum:
            reasons.append(f"{model_name}: needs {minimum}+; resolved runtime is {runtime_version}")
    return tuple(reasons)


__all__ = [
    "ClaudeCodeRuntimeDiagnostics",
    "clear_claude_code_runtime_version_probe_cache",
    "get_claude_code_runtime_diagnostics",
]
