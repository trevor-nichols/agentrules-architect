from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock

from agentrules.config.agents import MODEL_PRESETS
from agentrules.core.agents.base import ModelProvider, ReasoningMode
from agentrules.core.agents.claude_code.architect import ClaudeCodeArchitect
from agentrules.core.agents.factory.factory import ArchitectFactory
from agentrules.core.configuration.manager import ConfigManager
from agentrules.core.configuration.repository import TomlConfigRepository
from agentrules.core.types.models import ModelConfig


def _result_message(
    *,
    result: str | None = None,
    structured_output: object | None = None,
    is_error: bool = False,
    subtype: str = "success",
    errors: list[str] | None = None,
) -> ResultMessage:
    return ResultMessage(
        subtype=subtype,
        duration_ms=10,
        duration_api_ms=8,
        is_error=is_error,
        num_turns=1,
        session_id="session-1",
        stop_reason=None,
        total_cost_usd=None,
        usage={"input_tokens": 3, "output_tokens": 5},
        result=result,
        structured_output=structured_output,
        model_usage=None,
        permission_denials=None,
        errors=errors,
        uuid=None,
    )


def _assistant_message(text: str) -> AssistantMessage:
    return AssistantMessage(
        content=[TextBlock(text=text)],
        model="claude-sonnet-4-6",
        parent_tool_use_id=None,
        error=None,
        usage=None,
        message_id=None,
        stop_reason=None,
        session_id=None,
        uuid=None,
    )


def _build_config_manager(tmp_path: Path) -> ConfigManager:
    manager = ConfigManager(repository=TomlConfigRepository(tmp_path / "config.toml"), environ={})
    manager.set_claude_code_cli_path(sys.executable)
    return manager


def _build_architect(
    tmp_path: Path,
    messages: tuple[Any, ...],
) -> ClaudeCodeArchitect:
    async def _fake_query(
        _prompt: str,
        _options: Mapping[str, Any],
        _timeout_seconds: float | None,
    ) -> tuple[Any, ...]:
        return messages

    return ClaudeCodeArchitect(
        model_name="claude-sonnet-4-6",
        reasoning=ReasoningMode.DYNAMIC,
        name="Claude Code Tester",
        role="repository analysis",
        responsibilities=["Inspect the codebase"],
        prompt_template="{context}",
        system_prompt="Use concise bullets.",
        model_config=ModelConfig(
            provider=ModelProvider.CLAUDE_CODE,
            model_name="claude-sonnet-4-6",
        ),
        config_manager=_build_config_manager(tmp_path),
        query_executor=_fake_query,
    )


def test_factory_creates_claude_code_architect() -> None:
    architect = ArchitectFactory.create_architect(
        model_config=MODEL_PRESETS["claude-code-sonnet-4.6"]["config"],
        name="Claude Code Factory Agent",
        role="analysis",
        responsibilities=["Review the repository"],
        prompt_template="{context}",
        system_prompt="Use concise bullets.",
    )

    assert isinstance(architect, ClaudeCodeArchitect)


@pytest.mark.asyncio
async def test_claude_code_analyze_returns_plain_text_findings(tmp_path: Path) -> None:
    architect = _build_architect(tmp_path, (_assistant_message("Claude Code analyzed the repo."), _result_message()))

    result = await architect.analyze(
        {
            "formatted_prompt": "Inspect the main module.",
            "_claude_code_cwd": str(tmp_path),
        }
    )

    assert result["agent"] == "Claude Code Tester"
    assert result["findings"] == "Claude Code analyzed the repo."
    assert "error" not in result


@pytest.mark.asyncio
async def test_claude_code_analyze_passes_configured_timeout_to_executor(tmp_path: Path) -> None:
    manager = _build_config_manager(tmp_path)
    config = manager.load()
    config.claude_code.request_timeout_seconds = 2.5
    manager.save(config)
    observed_timeout: dict[str, float | None] = {"value": None}

    async def _fake_query(
        _prompt: str,
        _options: Mapping[str, Any],
        timeout_seconds: float | None,
    ) -> tuple[Any, ...]:
        observed_timeout["value"] = timeout_seconds
        return (_assistant_message("Claude Code analyzed the repo."), _result_message())

    architect = ClaudeCodeArchitect(
        model_name="claude-sonnet-4-6",
        reasoning=ReasoningMode.DYNAMIC,
        name="Claude Code Tester",
        role="repository analysis",
        responsibilities=["Inspect the codebase"],
        prompt_template="{context}",
        system_prompt="Use concise bullets.",
        model_config=ModelConfig(
            provider=ModelProvider.CLAUDE_CODE,
            model_name="claude-sonnet-4-6",
        ),
        config_manager=manager,
        query_executor=_fake_query,
    )

    result = await architect.analyze({"formatted_prompt": "Inspect the main module."})

    assert result["findings"] == "Claude Code analyzed the repo."
    assert observed_timeout["value"] == 2.5


@pytest.mark.asyncio
async def test_claude_code_phase_request_uses_structured_output(tmp_path: Path) -> None:
    structured = {
        "plan": "Analyze the repository in focused batches.",
        "agents": [
            {
                "id": "agent_1",
                "name": "Runtime Agent",
                "description": "Inspect runtime code.",
                "file_assignments": ["src/agentrules/core/agents/claude_code/architect.py"],
            }
        ],
    }
    architect = _build_architect(tmp_path, (_result_message(structured_output=structured),))

    result = await architect.create_analysis_plan({}, prompt="Plan the repository analysis.")

    assert result["error"] is None
    assert result["plan"] == "Analyze the repository in focused batches."
    assert result["structured_output"] == structured
    assert result["agents"][0]["id"] == "agent_1"


@pytest.mark.asyncio
async def test_claude_code_phase_request_reports_invalid_structured_output(tmp_path: Path) -> None:
    architect = _build_architect(tmp_path, (_assistant_message("not json"), _result_message()))

    result = await architect.synthesize_findings({}, prompt="Synthesize findings.")

    assert result["analysis"] == "No synthesis generated"
    assert "invalid structured output" in (result["error"] or "")


@pytest.mark.asyncio
async def test_claude_code_analyze_maps_sdk_error_result(tmp_path: Path) -> None:
    architect = _build_architect(
        tmp_path,
        (_result_message(is_error=True, subtype="error_during_execution", errors=["SDK failed"]),),
    )

    result = await architect.analyze({"formatted_prompt": "FAIL"})

    assert result["agent"] == "Claude Code Tester"
    assert "SDK failed" in result["error"]
