from __future__ import annotations

import sys
from pathlib import Path

from agentrules.core.agents.base import ReasoningMode
from agentrules.core.agents.codex.request_builder import prepare_request
from agentrules.core.configuration.manager import ConfigManager
from agentrules.core.configuration.repository import TomlConfigRepository


def _build_config_manager(tmp_path: Path) -> ConfigManager:
    manager = ConfigManager(repository=TomlConfigRepository(tmp_path / "config.toml"), environ={})
    manager.set_codex_cli_path(sys.executable)
    manager.set_codex_managed_home(str(tmp_path / "codex-home"))
    return manager


def test_prepare_request_maps_xhigh_reasoning_effort(tmp_path: Path) -> None:
    prepared = prepare_request(
        config_manager=_build_config_manager(tmp_path),
        model_name="gpt-6-codex-preview",
        content="Inspect repository architecture.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.XHIGH,
        phase_name=None,
        cwd=str(tmp_path),
    )

    assert prepared.turn_params["effort"] == "xhigh"
    assert prepared.turn_params["summary"] == "concise"


def test_prepare_request_maps_disabled_reasoning_to_none_effort(tmp_path: Path) -> None:
    prepared = prepare_request(
        config_manager=_build_config_manager(tmp_path),
        model_name="gpt-6-codex-preview",
        content="Inspect repository architecture.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.DISABLED,
        phase_name=None,
        cwd=str(tmp_path),
    )

    assert prepared.turn_params["effort"] == "none"
    assert prepared.turn_params["summary"] == "none"


def test_prepare_request_maps_enabled_reasoning_to_medium_effort(tmp_path: Path) -> None:
    prepared = prepare_request(
        config_manager=_build_config_manager(tmp_path),
        model_name="gpt-6-codex-preview",
        content="Inspect repository architecture.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.ENABLED,
        phase_name=None,
        cwd=str(tmp_path),
    )

    assert prepared.turn_params["effort"] == "medium"
    assert prepared.turn_params["summary"] == "concise"
