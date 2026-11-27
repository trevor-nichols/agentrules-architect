from __future__ import annotations

import asyncio
import json
import sys
from functools import partial
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from rich.console import Console

from agentrules.cli.context import CliContext
from agentrules.cli.services.codex_runtime import (
    _run_sync,
    get_codex_runtime_diagnostics,
    logout_codex_runtime,
    start_codex_chatgpt_login,
)
from agentrules.cli.ui.settings import models as model_settings
from agentrules.core.agents.codex import CodexError
from agentrules.core.agents.codex.architect import CodexArchitect
from agentrules.core.configuration import model_presets
from agentrules.core.configuration.manager import ConfigManager
from agentrules.core.configuration.repository import TomlConfigRepository

FAKE_SERVER = Path(__file__).resolve().parents[1] / "fakes" / "codex_app_server.py"


def _build_config_manager(tmp_path: Path) -> ConfigManager:
    config_path = tmp_path / "config.toml"
    manager = ConfigManager(repository=TomlConfigRepository(config_path), environ={})
    manager.set_codex_cli_path(sys.executable)
    manager.set_codex_managed_home(str(tmp_path / "codex-home"))
    return manager


def _fake_command() -> tuple[str, ...]:
    return (sys.executable, "-u", str(FAKE_SERVER))


def test_codex_runtime_diagnostics_reports_account_and_models(tmp_path: Path) -> None:
    manager = _build_config_manager(tmp_path)

    diagnostics = get_codex_runtime_diagnostics(
        config_manager=manager,
        include_models=True,
        command=_fake_command(),
    )

    assert diagnostics.can_connect is True
    assert diagnostics.user_agent == "codex-fake/1.0"
    assert diagnostics.account is not None
    assert diagnostics.account.is_authenticated is False
    assert diagnostics.models_error is None
    assert [model.model for model in diagnostics.models] == [
        "gpt-5.3-codex", "gpt-5.4", "gpt-6-codex-preview"
    ]
    assert diagnostics.codex_home == str(tmp_path / "codex-home")


@pytest.mark.asyncio
async def test_codex_picker_saves_gpt62_catalog_selection_for_structured_requests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = _build_config_manager(tmp_path)
    request_log = tmp_path / "requests.jsonl"
    legacy_command = (*_fake_command(), "--request-log", str(request_log))
    gpt62_command = (*legacy_command, "--gpt62-catalog")
    context = CliContext(console=Console(record=True, width=120))

    monkeypatch.setattr(model_settings.configuration, "CONFIG_MANAGER", manager)
    monkeypatch.setattr(model_presets, "CONFIG_MANAGER", manager)
    monkeypatch.setattr(model_presets.agent_settings, "MODEL_CONFIG", dict(model_presets.agent_settings.MODEL_CONFIG))
    monkeypatch.setattr(
        model_settings.codex_runtime,
        "get_codex_runtime_diagnostics",
        partial(get_codex_runtime_diagnostics, config_manager=manager, command=gpt62_command),
    )

    saved_pin = "codex-runtime:gpt-6.2-sol|effort=extreme"
    pin_navigation = iter(("phase4", "__DONE__"))

    def choose_pin(message: str, *, choices: list[Any], **_kwargs: Any) -> SimpleNamespace:
        labels = {getattr(choice, "value", None): str(choice.title) for choice in choices}
        if message == "Select phase to configure:":
            choice = next(pin_navigation)
        elif "choose variant" in message:
            assert "codex-runtime:gpt-6.2-sol|effort=medium" in labels
            assert "Extreme" in labels[saved_pin]
            choice = saved_pin
        else:
            assert any("GPT-6.2 Astra" in label for label in labels.values())
            assert "Codex runtime default" in labels["codex-runtime:__default__"]
            choice = next(value for value, label in labels.items() if "GPT-6.2 Sol" in label)
        assert choice in labels
        return SimpleNamespace(ask=lambda: choice)

    monkeypatch.setattr(model_settings.questionary, "select", choose_pin)
    model_settings.configure_models(context)
    reloaded = ConfigManager(repository=TomlConfigRepository(tmp_path / "config.toml"), environ={})
    assert reloaded.get_model_overrides() == {"phase4": saved_pin}

    async def synthesize(command: tuple[str, ...]) -> dict[str, Any]:
        config = model_presets.get_model_config_for_phase("phase4", reloaded.get_model_overrides())
        assert config is not None
        architect = CodexArchitect(
            model_name=config.model_name,
            reasoning=config.reasoning,
            model_config=config,
            config_manager=reloaded,
            command=command,
            request_timeout_seconds=2.0,
        )
        return await architect.synthesize_findings({}, prompt="Synthesize the repository findings.")

    structured = await synthesize(gpt62_command)
    assert structured["structured_output"] == {"analysis": "Codex produced a structured analysis response."}
    missing = await synthesize(legacy_command)
    assert "Configured Codex model 'gpt-6.2-sol' is not available" in missing["error"]
    assert reloaded.get_model_overrides() == {"phase4": saved_pin}
    default_navigation = iter(("phase4", "__DONE__"))

    def choose_runtime_default(message: str, *, choices: list[Any], **_kwargs: Any) -> SimpleNamespace:
        if message == "Select phase to configure:":
            choice = next(default_navigation)
        else:
            choice = "codex-runtime:__default__"
            assert any(item.value == choice for item in choices if hasattr(item, "value"))
        return SimpleNamespace(ask=lambda: choice)

    monkeypatch.setattr(model_settings.questionary, "select", choose_runtime_default)
    model_settings.configure_models(context)
    assert reloaded.get_model_overrides() == {"phase4": "codex-runtime:__default__"}
    assert (await synthesize(gpt62_command))["error"] is None
    assert (await synthesize(legacy_command))["error"] is None

    requests = [json.loads(line) for line in request_log.read_text(encoding="utf-8").splitlines()]
    assert [message["params"]["model"] for message in requests if message["method"] == "thread/start"] == [
        "gpt-6.2-sol", "gpt-6.2-astra", "gpt-5.3-codex",
    ]
    turns = [message["params"] for message in requests if message["method"] == "turn/start"]
    assert [(turn["model"], turn["effort"]) for turn in turns] == [
        ("gpt-6.2-sol", "extreme"), ("gpt-6.2-astra", "high"), ("gpt-5.3-codex", "medium"),
    ]
    assert turns[0]["outputSchema"] == {
        "type": "object",
        "properties": {"analysis": {"type": "string"}, "error": {"type": ["string", "null"]}},
        "required": ["analysis", "error"],
        "additionalProperties": False,
    }


def test_codex_runtime_login_and_logout_flow(tmp_path: Path) -> None:
    manager = _build_config_manager(tmp_path)

    login = start_codex_chatgpt_login(
        config_manager=manager,
        open_browser=False,
        command=_fake_command(),
    )
    assert login.completion is not None
    assert login.completion.success is True
    assert login.account is not None
    assert login.account.email == "codex-user@example.com"

    account_after_logout = logout_codex_runtime(
        config_manager=manager,
        command=_fake_command(),
    )
    assert account_after_logout.is_authenticated is False


def test_run_sync_preserves_runtime_failures() -> None:
    async def raise_runtime_error() -> None:
        raise CodexError("boom")

    with pytest.raises(CodexError, match="boom"):
        _run_sync(raise_runtime_error())


@pytest.mark.asyncio
async def test_run_sync_supports_callers_with_existing_event_loop() -> None:
    async def succeed() -> str:
        await asyncio.sleep(0)
        return "ok"

    assert _run_sync(succeed()) == "ok"
