"""Synchronous helpers for inspecting the local Claude Code runtime."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

from agentrules.core.configuration import (
    CLAUDE_CODE_API_KEY_ENV_VARS,
    CLAUDE_CODE_OAUTH_TOKEN_ENV_VAR,
    ConfigManager,
    get_config_manager,
)


@dataclass(frozen=True)
class ClaudeCodeRuntimeDiagnostics:
    cli_path: str | None
    executable_path: str | None
    sdk_available: bool
    auth_strategy: str
    sanitize_api_key_env: bool
    oauth_token_present: bool
    api_key_env_present_after_sanitization: bool
    version: str | None = None
    runtime_error: str | None = None
    version_error: str | None = None

    @property
    def is_available(self) -> bool:
        return self.sdk_available and self.runtime_error is None


def get_claude_code_runtime_diagnostics(
    *,
    config_manager: ConfigManager | None = None,
    timeout_seconds: float = 2.0,
) -> ClaudeCodeRuntimeDiagnostics:
    manager = config_manager or get_config_manager()
    runtime_config = manager.get_claude_code_config()
    executable_path = manager.resolve_claude_code_executable()
    sdk_available = manager.is_claude_agent_sdk_available()
    child_env = manager.build_claude_code_environment()

    version: str | None = None
    version_error: str | None = None
    runtime_error: str | None = None

    if not sdk_available:
        runtime_error = "Claude Agent SDK package could not be imported in the AgentRules environment."
    elif runtime_config.cli_path is None:
        pass
    elif executable_path is None:
        runtime_error = "Configured Claude Code executable could not be resolved from the current settings."
    else:
        try:
            completed = subprocess.run(
                [executable_path, "--version"],
                check=False,
                capture_output=True,
                env=child_env,
                text=True,
                timeout=timeout_seconds,
            )
            if completed.returncode == 0:
                version = (completed.stdout or completed.stderr).strip() or None
            else:
                version_error = (completed.stderr or completed.stdout).strip() or (
                    f"`claude --version` exited with status {completed.returncode}."
                )
        except Exception as exc:
            version_error = str(exc)

    return ClaudeCodeRuntimeDiagnostics(
        cli_path=runtime_config.cli_path,
        executable_path=executable_path,
        sdk_available=sdk_available,
        auth_strategy=runtime_config.auth_strategy,
        sanitize_api_key_env=runtime_config.sanitize_api_key_env,
        oauth_token_present=CLAUDE_CODE_OAUTH_TOKEN_ENV_VAR in child_env,
        api_key_env_present_after_sanitization=any(env_var in child_env for env_var in CLAUDE_CODE_API_KEY_ENV_VARS),
        version=version,
        runtime_error=runtime_error,
        version_error=version_error,
    )


__all__ = ["ClaudeCodeRuntimeDiagnostics", "get_claude_code_runtime_diagnostics"]
