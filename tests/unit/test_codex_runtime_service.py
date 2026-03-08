from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

from agentrules.cli.services.codex_runtime import (
    _run_sync,
    get_codex_runtime_diagnostics,
    logout_codex_runtime,
    start_codex_chatgpt_login,
)
from agentrules.core.agents.codex import CodexError
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
    assert [model.model for model in diagnostics.models] == ["gpt-5.3-codex", "gpt-5.4"]
    assert diagnostics.codex_home == str(tmp_path / "codex-home")


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
