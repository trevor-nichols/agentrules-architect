from __future__ import annotations

import sys
from pathlib import Path

import pytest
from claude_agent_sdk import ClaudeAgentOptions

from agentrules.core.agents.base import ReasoningMode
from agentrules.core.agents.claude_code.request_builder import prepare_request
from agentrules.core.configuration.manager import ConfigManager
from agentrules.core.configuration.models import ClaudeCodeConfig
from agentrules.core.configuration.repository import TomlConfigRepository


def _build_config_manager(tmp_path: Path) -> ConfigManager:
    env = {
        "ANTHROPIC_API_KEY": "api-key",
        "ANTHROPIC_AUTH_TOKEN": "auth-token",
        "CLAUDE_CODE_OAUTH_TOKEN": "oauth-token",
        "PATH": "/usr/bin",
    }
    manager = ConfigManager(repository=TomlConfigRepository(tmp_path / "config.toml"), environ=env)
    manager.set_claude_code_cli_path(sys.executable)
    return manager


def _build_sdk_default_config_manager(tmp_path: Path) -> ConfigManager:
    env = {
        "ANTHROPIC_API_KEY": "api-key",
        "ANTHROPIC_AUTH_TOKEN": "auth-token",
        "CLAUDE_CODE_OAUTH_TOKEN": "oauth-token",
        "PATH": "/usr/bin",
    }
    return ConfigManager(repository=TomlConfigRepository(tmp_path / "config.toml"), environ=env)


def test_prepare_request_sets_oauth_runtime_options_and_sanitized_env(tmp_path: Path) -> None:
    prepared = prepare_request(
        config_manager=_build_config_manager(tmp_path),
        model_name="claude-sonnet-4-6",
        content="Inspect repository architecture.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.DISABLED,
        phase_name=None,
        cwd=str(tmp_path),
    )

    assert prepared.options["model"] == "claude-sonnet-4-6"
    assert prepared.options["cli_path"] == str(Path(sys.executable).resolve())
    assert prepared.options["cwd"] == str(tmp_path.resolve())
    assert prepared.options["permission_mode"] == "dontAsk"
    assert prepared.options["allowed_tools"] == ["Read", "Glob", "Grep"]
    assert "Bash" in prepared.options["disallowed_tools"]
    assert prepared.options["max_turns"] == 12
    assert "max_budget_usd" not in prepared.options
    assert "request_timeout_seconds" not in prepared.options
    assert prepared.execution_timeout_seconds == 300.0
    assert prepared.options["system_prompt"] == {
        "type": "preset",
        "preset": "claude_code",
        "append": "Keep responses concise.",
        "exclude_dynamic_sections": True,
    }
    assert prepared.options["env"]["CLAUDE_CODE_OAUTH_TOKEN"] == "oauth-token"
    assert "ANTHROPIC_API_KEY" not in prepared.options["env"]
    assert "ANTHROPIC_AUTH_TOKEN" not in prepared.options["env"]
    assert prepared.sanitized_env_vars == ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")


def test_prepare_request_omits_cli_path_for_sdk_default_runtime(tmp_path: Path) -> None:
    prepared = prepare_request(
        config_manager=_build_sdk_default_config_manager(tmp_path),
        model_name="claude-sonnet-4-6",
        content="Inspect repository architecture.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.DISABLED,
        phase_name=None,
        cwd=str(tmp_path),
    )

    sdk_options = ClaudeAgentOptions(**prepared.options)

    assert "cli_path" not in prepared.options
    assert sdk_options.cli_path is None


def test_prepare_request_resolves_configured_cli_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    executable = bin_dir / "claude"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))
    manager = _build_sdk_default_config_manager(tmp_path)
    manager.set_claude_code_cli_path("claude")

    prepared = prepare_request(
        config_manager=manager,
        model_name="claude-sonnet-4-6",
        content="Inspect repository architecture.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.DISABLED,
        phase_name=None,
        cwd=str(tmp_path),
    )

    assert prepared.options["cli_path"] == str(executable.resolve())


def test_prepare_request_fails_fast_when_configured_cli_path_is_missing(tmp_path: Path) -> None:
    manager = _build_sdk_default_config_manager(tmp_path)
    manager.set_claude_code_cli_path(str(tmp_path / "missing-claude"))

    with pytest.raises(ValueError, match="Configured Claude Code executable could not be resolved"):
        prepare_request(
            config_manager=manager,
            model_name="claude-sonnet-4-6",
            content="Inspect repository architecture.",
            system_prompt="Keep responses concise.",
            reasoning=ReasoningMode.DISABLED,
            phase_name=None,
            cwd=str(tmp_path),
        )


def test_prepare_request_enables_research_tools_when_tools_config_enabled(tmp_path: Path) -> None:
    prepared = prepare_request(
        config_manager=_build_config_manager(tmp_path),
        model_name="claude-sonnet-4-6",
        content="Research package docs.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.DISABLED,
        phase_name=None,
        cwd=str(tmp_path),
        tools_config={"enabled": True, "tools": None},
    )

    assert prepared.options["allowed_tools"] == ["Read", "Glob", "Grep", "WebSearch", "WebFetch"]


def test_prepare_request_maps_reasoning_and_structured_output(tmp_path: Path) -> None:
    prepared = prepare_request(
        config_manager=_build_config_manager(tmp_path),
        model_name="claude-sonnet-4-6",
        content="Plan the analysis.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.DYNAMIC,
        phase_name="phase2",
        cwd=str(tmp_path),
        effort="medium",
    )

    assert prepared.options["thinking"] == {"type": "adaptive"}
    assert prepared.options["effort"] == "medium"
    assert prepared.options["output_format"]["type"] == "json_schema"
    assert prepared.options["output_format"]["schema"]["properties"]["plan"]["type"] == "string"


def test_prepare_request_maps_xhigh_reasoning_to_max_effort(tmp_path: Path) -> None:
    prepared = prepare_request(
        config_manager=_build_config_manager(tmp_path),
        model_name="claude-opus-4-6",
        content="Deeply inspect repository architecture.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.XHIGH,
        phase_name=None,
        cwd=str(tmp_path),
    )

    assert prepared.options["effort"] == "max"


def test_prepare_request_builds_sdk_accepted_system_prompt_preset(tmp_path: Path) -> None:
    prepared = prepare_request(
        config_manager=_build_config_manager(tmp_path),
        model_name="claude-sonnet-4-6",
        content="Inspect repository architecture.",
        system_prompt="Use AgentRules phase guidance.",
        reasoning=ReasoningMode.DISABLED,
        phase_name=None,
        cwd=str(tmp_path),
    )

    sdk_options = ClaudeAgentOptions(**prepared.options)

    assert sdk_options.system_prompt == {
        "type": "preset",
        "preset": "claude_code",
        "append": "Use AgentRules phase guidance.",
        "exclude_dynamic_sections": True,
    }


def test_prepare_request_uses_configured_execution_guardrails(tmp_path: Path) -> None:
    manager = _build_config_manager(tmp_path)
    config = manager.load()
    config.claude_code = ClaudeCodeConfig(
        cli_path=sys.executable,
        max_turns=3,
        request_timeout_seconds=1.5,
        max_budget_usd=0.25,
    )
    manager.save(config)

    prepared = prepare_request(
        config_manager=manager,
        model_name="claude-sonnet-4-6",
        content="Inspect repository architecture.",
        system_prompt="Use AgentRules phase guidance.",
        reasoning=ReasoningMode.DISABLED,
        phase_name=None,
        cwd=str(tmp_path),
    )

    sdk_options = ClaudeAgentOptions(**prepared.options)

    assert sdk_options.max_turns == 3
    assert sdk_options.max_budget_usd == 0.25
    assert prepared.execution_timeout_seconds == 1.5
    assert "request_timeout_seconds" not in prepared.options


def test_prepare_request_keeps_api_key_env_when_sanitization_is_disabled(tmp_path: Path) -> None:
    manager = _build_config_manager(tmp_path)
    manager.set_claude_code_sanitize_api_key_env(False)

    prepared = prepare_request(
        config_manager=manager,
        model_name="claude-sonnet-4-6",
        content="Inspect repository architecture.",
        system_prompt="Use AgentRules phase guidance.",
        reasoning=ReasoningMode.DISABLED,
        phase_name=None,
        cwd=str(tmp_path),
    )

    assert prepared.options["env"]["ANTHROPIC_API_KEY"] == "api-key"
    assert prepared.options["env"]["ANTHROPIC_AUTH_TOKEN"] == "auth-token"
    assert prepared.sanitized_env_vars == ()
