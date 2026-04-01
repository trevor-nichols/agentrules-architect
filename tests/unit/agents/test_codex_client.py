from __future__ import annotations

import asyncio
import sys
from collections import deque
from pathlib import Path
from typing import Literal
from unittest.mock import AsyncMock, patch

import pytest

from agentrules.core.agents.codex import (
    CodexAppServerClient,
    CodexAppServerProcess,
    CodexNotification,
    CodexProcessLaunchConfig,
)
from agentrules.core.agents.codex.process import DEFAULT_CODEX_SUBPROCESS_STREAM_LIMIT

FAKE_SERVER = Path(__file__).resolve().parents[2] / "fakes" / "codex_app_server.py"


def _build_client(tmp_path: Path, *, timeout: float = 2.0) -> CodexAppServerClient:
    launch_config = CodexProcessLaunchConfig(
        executable_path=sys.executable,
        codex_home=str(tmp_path / "codex-home"),
        cwd=str(tmp_path),
    )
    process = CodexAppServerProcess(
        launch_config,
        command=(sys.executable, "-u", str(FAKE_SERVER)),
    )
    return CodexAppServerClient(process, request_timeout_seconds=timeout)


class _RecordingEvent(asyncio.Event):
    def __init__(self) -> None:
        super().__init__()
        self.wait_calls = 0

    async def wait(self) -> Literal[True]:
        self.wait_calls += 1
        return await super().wait()


@pytest.mark.asyncio
async def test_codex_client_initializes_and_reads_account(tmp_path: Path) -> None:
    async with _build_client(tmp_path) as client:
        assert client.initialize_result is not None
        assert client.initialize_result.user_agent == "codex-fake/1.0"

        account = await client.read_account()
        assert account.is_authenticated is False
        assert account.requires_openai_auth is True
        assert account.email is None


@pytest.mark.asyncio
async def test_codex_client_buffers_notifications_before_response_is_consumed(tmp_path: Path) -> None:
    async with _build_client(tmp_path) as client:
        page = await client.list_models(limit=1, include_hidden=False)
        assert [model.model for model in page.models] == ["gpt-5.3-codex"]
        assert page.next_cursor == "1"

        notification = await client.wait_for_notification("server/heartbeat")
        assert notification.params["cursor"] == "0"
        assert notification.params["count"] == 1


@pytest.mark.asyncio
async def test_codex_client_lists_all_models_across_pages(tmp_path: Path) -> None:
    async with _build_client(tmp_path) as client:
        visible_models = await client.list_all_models(limit=1)
        assert [model.model for model in visible_models] == ["gpt-5.3-codex", "gpt-5.4"]

        all_models = await client.list_all_models(limit=2, include_hidden=True)
        assert [model.model for model in all_models] == ["gpt-5.3-codex", "gpt-5.4", "gpt-5.2-codex"]


@pytest.mark.asyncio
async def test_codex_client_chatgpt_login_and_logout(tmp_path: Path) -> None:
    async with _build_client(tmp_path) as client:
        login = await client.start_chatgpt_login()
        assert login.login_id == "login-1"
        assert login.auth_url == "https://chatgpt.com/fake-auth/login-1"

        completion = await client.wait_for_login_completion(login.login_id)
        assert completion.success is True

        update = await client.wait_for_notification("account/updated")
        assert update.params["authMode"] == "chatgpt"

        account = await client.read_account(refresh_token=True)
        assert account.is_authenticated is True
        assert account.email == "codex-user@example.com"
        assert account.plan_type == "pro"

        await client.logout()
        logout_update = await client.wait_for_notification("account/updated")
        assert logout_update.params["authMode"] is None

        account_after_logout = await client.read_account()
        assert account_after_logout.is_authenticated is False


@pytest.mark.asyncio
async def test_codex_process_uses_explicit_stream_limit(tmp_path: Path) -> None:
    launch_config = CodexProcessLaunchConfig(
        executable_path=sys.executable,
        codex_home=str(tmp_path / "codex-home"),
        cwd=str(tmp_path),
    )
    process = CodexAppServerProcess(
        launch_config,
        command=(sys.executable, "-u", str(FAKE_SERVER)),
    )

    fake_process = AsyncMock()
    fake_process.stdin = None
    fake_process.stdout = None
    fake_process.stderr = None
    fake_process.returncode = None

    with patch(
        "agentrules.core.agents.codex.process.asyncio.create_subprocess_exec",
        new_callable=AsyncMock,
    ) as mock_exec:
        mock_exec.return_value = fake_process
        await process.start()

    assert mock_exec.await_args.kwargs["limit"] == DEFAULT_CODEX_SUBPROCESS_STREAM_LIMIT


@pytest.mark.asyncio
async def test_wait_for_buffered_message_ignores_unmatched_buffer_without_spinning(
    tmp_path: Path,
) -> None:
    client = _build_client(tmp_path)
    reader_task = asyncio.create_task(asyncio.sleep(1))
    stderr_task = asyncio.create_task(asyncio.sleep(1))
    client._reader_task = reader_task
    client._stderr_task = stderr_task

    event = _RecordingEvent()
    event.set()
    buffer = deque(
        [CodexNotification(method="server/heartbeat", params={"count": 1})]
    )

    async def deliver_match() -> None:
        await asyncio.sleep(0.01)
        buffer.append(CodexNotification(method="account/updated", params={"count": 2}))
        event.set()

    producer = asyncio.create_task(deliver_match())
    try:
        matched = await asyncio.wait_for(
            client._wait_for_buffered_message(
                buffer,
                event,
                matcher=lambda item: item.method == "account/updated",
            ),
            timeout=1.0,
        )
        await producer

        assert matched.method == "account/updated"
        assert event.wait_calls == 1
        assert [item.method for item in buffer] == ["server/heartbeat"]
    finally:
        for task in (producer, reader_task, stderr_task):
            task.cancel()
        await asyncio.gather(producer, reader_task, stderr_task, return_exceptions=True)
