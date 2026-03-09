from __future__ import annotations

import os
from pathlib import Path

import pytest

from agentrules.cli.services.codex_runtime import get_codex_runtime_diagnostics
from agentrules.config.agents import MODEL_PRESETS
from agentrules.core.agents.base import ModelProvider, ReasoningMode
from agentrules.core.agents.codex.architect import CodexArchitect
from agentrules.core.configuration.manager import ConfigManager
from agentrules.core.configuration.repository import TomlConfigRepository

LIVE_FLAG = "AGENTRULES_RUN_CODEX_LIVE"


def _build_live_config_manager(tmp_path: Path) -> ConfigManager:
    manager = ConfigManager(repository=TomlConfigRepository(tmp_path / "config.toml"))
    manager.set_codex_cli_path(os.getenv("AGENTRULES_CODEX_CLI", "codex"))

    strategy = os.getenv("AGENTRULES_CODEX_HOME_STRATEGY", "inherit")
    manager.set_codex_home_strategy(strategy)
    if strategy == "managed":
        managed_home = os.getenv("AGENTRULES_CODEX_MANAGED_HOME")
        if managed_home:
            manager.set_codex_managed_home(managed_home)
    return manager


def _select_live_model(available_models: set[str]) -> tuple[str, object | None, ReasoningMode]:
    explicit_model = os.getenv("AGENTRULES_CODEX_MODEL")
    if explicit_model:
        if explicit_model not in available_models:
            pytest.skip(f"Configured Codex live smoke model is unavailable: {explicit_model}")
        return explicit_model, None, ReasoningMode.MEDIUM

    for _preset_key, preset in MODEL_PRESETS.items():
        if preset["provider"] != ModelProvider.CODEX:
            continue
        model_config = preset["config"]
        if model_config.model_name in available_models:
            return model_config.model_name, model_config, model_config.reasoning

    pytest.skip("No configured Codex preset matches the runtime model catalog.")


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_codex_structured_output_smoke(tmp_path: Path) -> None:
    if os.getenv(LIVE_FLAG) != "1":
        pytest.skip(f"Set {LIVE_FLAG}=1 to enable the Codex live smoke.")

    manager = _build_live_config_manager(tmp_path)
    diagnostics = get_codex_runtime_diagnostics(
        config_manager=manager,
        include_models=True,
        refresh_account=True,
    )

    if diagnostics.runtime_error:
        pytest.skip(f"Codex runtime unavailable: {diagnostics.runtime_error}")
    if diagnostics.account is None or not diagnostics.account.is_authenticated:
        pytest.skip("Codex runtime is not authenticated for the selected CODEX_HOME.")
    if not diagnostics.models:
        pytest.skip("Codex runtime returned no visible models.")

    available_models = {model.model for model in diagnostics.models}
    model_name, model_config, reasoning = _select_live_model(available_models)
    repo_root = Path(__file__).resolve().parents[2]

    architect = CodexArchitect(
        model_name=model_name,
        reasoning=reasoning,
        name="Codex Live Smoke",
        role="live runtime validation",
        responsibilities=["Verify that structured phase output works end to end."],
        prompt_template="{context}",
        system_prompt="Return concise structured output.",
        model_config=model_config,
        config_manager=manager,
        request_timeout_seconds=120.0,
    )

    result = await architect.analyze(
        {
            "formatted_prompt": (
                "Return a short phase-4 style validation that this live Codex smoke test can "
                "reach the authenticated runtime and satisfy the structured output schema."
            ),
            "_structured_output_phase": "phase4",
            "_codex_cwd": str(repo_root),
        }
    )

    assert result.get("error") is None
    assert isinstance(result.get("structured_output"), dict)
    structured_output = result["structured_output"]
    assert isinstance(structured_output.get("analysis"), str)
    assert structured_output["analysis"].strip()
