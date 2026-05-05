from __future__ import annotations

import os
import sys
from pathlib import Path

from agentrules.cli.services.claude_code_runtime import ClaudeCodeRuntimeDiagnostics
from agentrules.cli.services.configuration import ClaudeCodeRuntimeState
from agentrules.cli.ui.settings.claude_code import build_runtime_guidance
from agentrules.core.configuration import ConfigManager
from agentrules.core.configuration.repository import TomlConfigRepository


def _build_config_manager(tmp_path: Path, env: dict[str, str] | None = None) -> ConfigManager:
    return ConfigManager(
        repository=TomlConfigRepository(tmp_path / "config.toml"),
        environ=env or {},
    )


def test_claude_code_runtime_state_exposes_config_and_availability(tmp_path: Path, monkeypatch) -> None:
    from agentrules.cli.services import configuration

    manager = _build_config_manager(tmp_path)
    monkeypatch.setattr(manager, "is_claude_code_available", lambda: True)
    manager.set_claude_code_cli_path(sys.executable)
    monkeypatch.setattr(configuration, "CONFIG_MANAGER", manager)

    state = configuration.get_claude_code_runtime_state()

    assert state.cli_path == sys.executable
    assert state.auth_strategy == "oauth"
    assert state.sanitize_api_key_env is True
    assert state.executable_path == str(Path(sys.executable).resolve())
    assert state.is_available is True


def test_claude_code_runtime_state_uses_sdk_default_when_path_is_unset(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from agentrules.cli.services import configuration

    manager = _build_config_manager(tmp_path)
    monkeypatch.setattr(manager, "is_claude_code_available", lambda: True)
    monkeypatch.setattr(manager, "is_claude_agent_sdk_available", lambda: True)
    monkeypatch.setattr(configuration, "CONFIG_MANAGER", manager)

    state = configuration.get_claude_code_runtime_state()

    assert state.cli_path is None
    assert state.executable_path is None
    assert state.is_available is True


def test_claude_code_diagnostics_use_sanitized_child_environment(tmp_path: Path, monkeypatch) -> None:
    from agentrules.cli.services.claude_code_runtime import get_claude_code_runtime_diagnostics

    manager = _build_config_manager(
        tmp_path,
        env={
            "ANTHROPIC_API_KEY": "api-key",
            "ANTHROPIC_AUTH_TOKEN": "auth-token",
            "CLAUDE_CODE_OAUTH_TOKEN": "oauth-token",
            "PATH": os.environ.get("PATH", ""),
        },
    )
    manager.set_claude_code_cli_path(sys.executable)
    monkeypatch.setattr(manager, "is_claude_agent_sdk_available", lambda: True)

    diagnostics = get_claude_code_runtime_diagnostics(config_manager=manager)

    assert diagnostics.executable_path == str(Path(sys.executable).resolve())
    assert diagnostics.sdk_available is True
    assert diagnostics.is_available is True
    assert diagnostics.oauth_token_present is True
    assert diagnostics.api_key_env_present_after_sanitization is False
    assert diagnostics.version is not None


def test_claude_code_diagnostics_report_missing_executable(tmp_path: Path, monkeypatch) -> None:
    from agentrules.cli.services.claude_code_runtime import get_claude_code_runtime_diagnostics

    manager = _build_config_manager(tmp_path)
    manager.set_claude_code_cli_path(str(tmp_path / "missing-claude"))
    monkeypatch.setattr(manager, "is_claude_agent_sdk_available", lambda: True)

    diagnostics = get_claude_code_runtime_diagnostics(config_manager=manager)

    assert diagnostics.executable_path is None
    assert diagnostics.is_available is False
    assert "could not be resolved" in (diagnostics.runtime_error or "")


def test_claude_code_diagnostics_treat_sdk_default_as_available(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from agentrules.cli.services.claude_code_runtime import get_claude_code_runtime_diagnostics

    manager = _build_config_manager(
        tmp_path,
        env={"CLAUDE_CODE_OAUTH_TOKEN": "oauth-token"},
    )
    monkeypatch.setattr(manager, "is_claude_agent_sdk_available", lambda: True)

    diagnostics = get_claude_code_runtime_diagnostics(config_manager=manager)

    assert diagnostics.cli_path is None
    assert diagnostics.executable_path is None
    assert diagnostics.sdk_available is True
    assert diagnostics.is_available is True
    assert diagnostics.runtime_error is None
    assert diagnostics.version is None


def test_claude_code_diagnostics_report_missing_sdk(tmp_path: Path, monkeypatch) -> None:
    from agentrules.cli.services.claude_code_runtime import get_claude_code_runtime_diagnostics

    manager = _build_config_manager(tmp_path)
    monkeypatch.setattr(manager, "is_claude_agent_sdk_available", lambda: False)

    diagnostics = get_claude_code_runtime_diagnostics(config_manager=manager)

    assert diagnostics.sdk_available is False
    assert diagnostics.is_available is False
    assert "SDK package" in (diagnostics.runtime_error or "")


def test_claude_code_runtime_guidance_explains_oauth_and_api_key_sanitization() -> None:
    state = ClaudeCodeRuntimeState(
        cli_path=None,
        auth_strategy="oauth",
        sanitize_api_key_env=True,
        executable_path=None,
        is_available=True,
    )
    diagnostics = ClaudeCodeRuntimeDiagnostics(
        cli_path=None,
        executable_path=None,
        sdk_available=True,
        auth_strategy="oauth",
        sanitize_api_key_env=True,
        oauth_token_present=False,
        api_key_env_present_after_sanitization=False,
        version="1.0.0",
    )

    guidance = build_runtime_guidance(state, diagnostics)

    assert any("SDK default runtime" in note for note in guidance)
    assert any("claude auth login" in note for note in guidance)
    assert any("claude setup-token" in note for note in guidance)
    assert any("CLAUDE_CODE_OAUTH_TOKEN" in note for note in guidance)
    assert any("Anthropic API-key environment variables are stripped" in note for note in guidance)
    assert any("choose a Claude Code preset" in note for note in guidance)


def test_claude_code_runtime_guidance_warns_when_sanitization_disabled() -> None:
    state = ClaudeCodeRuntimeState(
        cli_path="claude",
        auth_strategy="oauth",
        sanitize_api_key_env=False,
        executable_path="/usr/local/bin/claude",
        is_available=True,
    )
    diagnostics = ClaudeCodeRuntimeDiagnostics(
        cli_path="claude",
        executable_path="/usr/local/bin/claude",
        sdk_available=True,
        auth_strategy="oauth",
        sanitize_api_key_env=False,
        oauth_token_present=True,
        api_key_env_present_after_sanitization=True,
        version="1.0.0",
    )

    guidance = build_runtime_guidance(state, diagnostics)

    assert any("API-key precedence" in note for note in guidance)
