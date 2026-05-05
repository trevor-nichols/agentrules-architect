from __future__ import annotations

import sys
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions

from agentrules.core.agents.base import ReasoningMode
from agentrules.core.agents.claude_code.request_builder import prepare_request
from agentrules.core.configuration.manager import ConfigManager
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
    assert prepared.options["cli_path"] == sys.executable
    assert prepared.options["cwd"] == str(tmp_path.resolve())
    assert prepared.options["permission_mode"] == "dontAsk"
    assert prepared.options["allowed_tools"] == ["Read", "Glob", "Grep"]
    assert "Bash" in prepared.options["disallowed_tools"]
    assert prepared.options["system_prompt"] == {
        "type": "preset",
        "preset": "claude_code",
        "append": "Keep responses concise.",
        "exclude_dynamic_sections": True,
    }
    assert prepared.options["env"]["CLAUDE_CODE_OAUTH_TOKEN"] == "oauth-token"
    assert "ANTHROPIC_API_KEY" not in prepared.options["env"]
    assert "ANTHROPIC_AUTH_TOKEN" not in prepared.options["env"]


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
