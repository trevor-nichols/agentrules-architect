from __future__ import annotations

import sys
from pathlib import Path

import pytest

from agentrules.config.agents import MODEL_PRESETS
from agentrules.core.agents.base import ReasoningMode
from agentrules.core.agents.codex.architect import CodexArchitect
from agentrules.core.agents.factory.factory import ArchitectFactory
from agentrules.core.configuration.manager import ConfigManager
from agentrules.core.configuration.repository import TomlConfigRepository

FAKE_SERVER = Path(__file__).resolve().parents[2] / "fakes" / "codex_app_server.py"


def _build_config_manager(tmp_path: Path) -> ConfigManager:
    manager = ConfigManager(repository=TomlConfigRepository(tmp_path / "config.toml"), environ={})
    manager.set_codex_cli_path(sys.executable)
    manager.set_codex_managed_home(str(tmp_path / "codex-home"))
    return manager


def _build_architect(tmp_path: Path) -> CodexArchitect:
    return CodexArchitect(
        model_name="gpt-5.3-codex",
        reasoning=ReasoningMode.MEDIUM,
        name="Codex Tester",
        role="repository analysis",
        responsibilities=["Inspect the codebase"],
        prompt_template="{context}",
        system_prompt="Use concise bullets.",
        model_config=MODEL_PRESETS["codex-gpt-5.3-codex"]["config"],
        config_manager=_build_config_manager(tmp_path),
        command=(sys.executable, "-u", str(FAKE_SERVER)),
        request_timeout_seconds=2.0,
    )


def test_factory_creates_codex_architect() -> None:
    architect = ArchitectFactory.create_architect(
        model_config=MODEL_PRESETS["codex-gpt-5.3-codex"]["config"],
        name="Codex Factory Agent",
        role="analysis",
        responsibilities=["Review the repository"],
        prompt_template="{context}",
        system_prompt="Use concise bullets.",
    )

    assert isinstance(architect, CodexArchitect)


def test_codex_prepare_request_sets_launch_overrides_and_output_schema(tmp_path: Path) -> None:
    architect = _build_architect(tmp_path)

    prepared = architect._prepare_request(
        "Inspect the architecture",
        system_prompt="Use concise bullets.",
        phase_name="phase4",
        cwd=str(tmp_path),
    )

    assert prepared.launch_config.config_overrides["developer_instructions"] == "Use concise bullets."
    assert prepared.thread_params["approvalPolicy"] == "never"
    assert prepared.thread_params["sandbox"] == "read-only"
    assert prepared.thread_params["ephemeral"] is True
    assert prepared.turn_params["sandboxPolicy"]["type"] == "readOnly"
    assert prepared.turn_params["summary"] == "concise"
    assert prepared.turn_params["outputSchema"]["properties"]["analysis"]["type"] == "string"


@pytest.mark.asyncio
async def test_codex_analyze_returns_plain_text_findings(tmp_path: Path) -> None:
    architect = _build_architect(tmp_path)

    result = await architect.analyze(
        {
            "formatted_prompt": "Inspect the main module.",
            "_codex_cwd": str(tmp_path),
        }
    )

    assert result["agent"] == "Codex Tester"
    assert result["error"] if "error" in result else None is None
    assert "Codex analyzed: Inspect the main module." in result["findings"]


@pytest.mark.asyncio
async def test_codex_phase_request_parses_structured_output(tmp_path: Path) -> None:
    architect = _build_architect(tmp_path)

    result = await architect.create_analysis_plan({}, prompt="Plan the repository analysis.")

    assert result["error"] is None
    assert result["plan"] == "Analyze the repository in focused batches."
    assert result["structured_output"]["reasoning"] == "The fake runtime returned a deterministic phase 2 plan."
    assert result["agents"][0]["id"] == "agent_1"


@pytest.mark.asyncio
async def test_codex_phase_request_reports_invalid_structured_output(tmp_path: Path) -> None:
    architect = _build_architect(tmp_path)

    result = await architect.synthesize_findings({}, prompt="BAD_SCHEMA_JSON")

    assert result["analysis"] == "No synthesis generated"
    assert "invalid structured output" in (result["error"] or "")


@pytest.mark.asyncio
async def test_codex_analyze_maps_failed_turn_to_error(tmp_path: Path) -> None:
    architect = _build_architect(tmp_path)

    result = await architect.analyze(
        {
            "formatted_prompt": "TURN_FAIL",
            "_codex_cwd": str(tmp_path),
        }
    )

    assert "Fake Codex turn failure" in result["error"]
    assert "Simulated failure" in result["error"]
