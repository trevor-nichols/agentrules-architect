from __future__ import annotations

import os
from pathlib import Path

import pytest

from agentrules.cli.services.claude_code_runtime import get_claude_code_runtime_diagnostics
from agentrules.config.agents import MODEL_PRESETS
from agentrules.core.agents.base import ReasoningMode
from agentrules.core.agents.claude_code.architect import ClaudeCodeArchitect
from agentrules.core.configuration.manager import ConfigManager
from agentrules.core.configuration.repository import TomlConfigRepository

LIVE_FLAG = "AGENTRULES_RUN_CLAUDE_CODE_LIVE"


def _build_live_config_manager(tmp_path: Path) -> ConfigManager:
    manager = ConfigManager(repository=TomlConfigRepository(tmp_path / "config.toml"))
    if cli_path := os.getenv("AGENTRULES_CLAUDE_CODE_CLI"):
        manager.set_claude_code_cli_path(cli_path)
    return manager


def _select_live_model() -> tuple[str, object | None, ReasoningMode]:
    explicit_model = os.getenv("AGENTRULES_CLAUDE_CODE_MODEL")
    if explicit_model:
        return explicit_model, None, ReasoningMode.DYNAMIC

    preferred_presets = (
        "claude-code-default",
        "claude-code-sonnet-5-reasoning-medium",
        "claude-code-sonnet-4.6",
        "claude-code-sonnet-4.6-reasoning-medium",
        "claude-code-haiku",
    )
    for preset_key in preferred_presets:
        preset = MODEL_PRESETS[preset_key]
        model_config = preset["config"]
        return model_config.model_name, model_config, model_config.reasoning

    pytest.skip("No Claude Code runtime preset is configured.")


def _is_auth_related_error(error: str | None) -> bool:
    if not error:
        return False
    normalized = error.lower()
    return any(marker in normalized for marker in ("auth", "oauth", "login", "credential", "subscription"))


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_claude_code_structured_output_smoke(tmp_path: Path) -> None:
    if os.getenv(LIVE_FLAG) != "1":
        pytest.skip(f"Set {LIVE_FLAG}=1 to enable the Claude Code live smoke.")

    manager = _build_live_config_manager(tmp_path)
    diagnostics = get_claude_code_runtime_diagnostics(config_manager=manager)
    if diagnostics.runtime_error:
        pytest.skip(f"Claude Code runtime unavailable: {diagnostics.runtime_error}")
    if diagnostics.version_error:
        pytest.skip(f"Claude Code runtime version unavailable: {diagnostics.version_error}")

    assert diagnostics.executable_path
    assert diagnostics.executable_source
    assert diagnostics.version

    model_name, model_config, reasoning = _select_live_model()
    repo_root = Path(__file__).resolve().parents[2]

    architect = ClaudeCodeArchitect(
        model_name=model_name,
        reasoning=reasoning,
        name="Claude Code Live Smoke",
        role="live runtime validation",
        responsibilities=["Verify that structured phase output works end to end."],
        prompt_template="{context}",
        system_prompt="Return concise structured output.",
        model_config=model_config,
        config_manager=manager,
    )

    result = await architect.analyze(
        {
            "formatted_prompt": (
                "Return a short phase-4 style validation that this live Claude Code smoke test can "
                "reach the authenticated runtime and satisfy the structured output schema."
            ),
            "_structured_output_phase": "phase4",
            "_claude_code_cwd": str(repo_root),
        }
    )

    if _is_auth_related_error(result.get("error")):
        pytest.skip(f"Claude Code runtime is not authenticated for live smoke: {result['error']}")

    assert result.get("error") is None
    assert isinstance(result.get("structured_output"), dict)
    structured_output = result["structured_output"]
    assert isinstance(structured_output.get("analysis"), str)
    assert structured_output["analysis"].strip()
