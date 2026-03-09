"""Synchronous helpers for inspecting and managing the Codex app-server runtime."""

from __future__ import annotations

import asyncio
import webbrowser
from collections.abc import Callable, Coroutine, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from dataclasses import dataclass
from typing import Any, TypeVar, cast

from agentrules.core.agents.codex import (
    CodexAccountSummary,
    CodexAppServerClient,
    CodexAppServerProcess,
    CodexError,
    CodexLoginCompleted,
    CodexLoginStartResult,
    CodexModelInfo,
)
from agentrules.core.configuration import ConfigManager, get_config_manager

BrowserOpener = Callable[[str], bool]
T = TypeVar("T")


@dataclass(frozen=True)
class CodexRuntimeDiagnostics:
    executable_path: str | None
    codex_home: str | None
    command: tuple[str, ...]
    user_agent: str | None = None
    account: CodexAccountSummary | None = None
    models: tuple[CodexModelInfo, ...] = ()
    runtime_error: str | None = None
    account_error: str | None = None
    models_error: str | None = None
    recent_stderr: tuple[str, ...] = ()

    @property
    def can_connect(self) -> bool:
        return self.runtime_error is None and self.user_agent is not None


@dataclass(frozen=True)
class CodexLoginFlowResult:
    login: CodexLoginStartResult
    completion: CodexLoginCompleted | None
    account: CodexAccountSummary | None
    opened_browser: bool
    browser_error: str | None = None
    waiting_timed_out: bool = False


def _run_sync(awaitable: Coroutine[Any, Any, T]) -> T:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)

    # CLI helpers may be invoked from environments that already own the current
    # thread's event loop. Execute the coroutine in a worker thread so runtime
    # failures propagate unchanged instead of retrying an already-awaited coroutine.
    context = copy_context()
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="codex-runtime-sync") as executor:
        future = executor.submit(context.run, asyncio.run, awaitable)
        return cast(T, future.result())


async def _collect_runtime_diagnostics(
    config_manager: ConfigManager,
    *,
    include_models: bool,
    refresh_account: bool,
    include_hidden_models: bool,
    model_page_size: int,
    cwd: str | None,
    config_overrides: Mapping[str, Any] | None,
    command: Sequence[str] | None,
) -> CodexRuntimeDiagnostics:
    executable_path = config_manager.resolve_codex_executable()
    codex_home = config_manager.get_effective_codex_home()

    if executable_path is None:
        return CodexRuntimeDiagnostics(
            executable_path=None,
            codex_home=codex_home,
            command=(),
            runtime_error="Codex executable could not be resolved from the current settings.",
        )

    try:
        launch_config = config_manager.build_codex_launch_config(
            cwd=cwd,
            config_overrides=config_overrides,
        )
    except CodexError as exc:
        return CodexRuntimeDiagnostics(
            executable_path=executable_path,
            codex_home=codex_home,
            command=tuple(command or ()),
            runtime_error=str(exc),
        )

    process = CodexAppServerProcess(launch_config, command=command)
    try:
        async with CodexAppServerClient(process) as client:
            account: CodexAccountSummary | None = None
            account_error: str | None = None
            try:
                account = await client.read_account(refresh_token=refresh_account)
            except CodexError as exc:
                account_error = str(exc)

            models: tuple[CodexModelInfo, ...] = ()
            models_error: str | None = None
            if include_models:
                try:
                    models = await client.list_all_models(
                        limit=model_page_size,
                        include_hidden=include_hidden_models,
                    )
                except CodexError as exc:
                    models_error = str(exc)

            return CodexRuntimeDiagnostics(
                executable_path=launch_config.executable_path,
                codex_home=launch_config.codex_home,
                command=process.command,
                user_agent=client.initialize_result.user_agent if client.initialize_result else None,
                account=account,
                models=models,
                account_error=account_error,
                models_error=models_error,
                recent_stderr=process.recent_stderr,
            )
    except CodexError as exc:
        return CodexRuntimeDiagnostics(
            executable_path=launch_config.executable_path,
            codex_home=launch_config.codex_home,
            command=process.command,
            runtime_error=str(exc),
            recent_stderr=process.recent_stderr,
        )


async def _run_chatgpt_login(
    config_manager: ConfigManager,
    *,
    timeout_seconds: float,
    browser_opener: BrowserOpener,
    open_browser: bool,
    cwd: str | None,
    config_overrides: Mapping[str, Any] | None,
    command: Sequence[str] | None,
) -> CodexLoginFlowResult:
    launch_config = config_manager.build_codex_launch_config(
        cwd=cwd,
        config_overrides=config_overrides,
    )
    process = CodexAppServerProcess(launch_config, command=command)

    async with CodexAppServerClient(process) as client:
        login = await client.start_chatgpt_login()

        opened_browser = False
        browser_error: str | None = None
        if open_browser and login.auth_url:
            try:
                opened_browser = bool(browser_opener(login.auth_url))
            except Exception as exc:  # pragma: no cover - stdlib browser failures are platform-specific
                browser_error = str(exc)

        if open_browser and login.auth_url and not opened_browser:
            return CodexLoginFlowResult(
                login=login,
                completion=None,
                account=None,
                opened_browser=False,
                browser_error=browser_error or "Failed to open the ChatGPT login URL automatically.",
            )

        try:
            completion = await client.wait_for_login_completion(
                login.login_id,
                timeout_seconds=timeout_seconds,
            )
        except TimeoutError:
            return CodexLoginFlowResult(
                login=login,
                completion=None,
                account=None,
                opened_browser=opened_browser,
                browser_error=browser_error,
                waiting_timed_out=True,
            )

        account = await client.read_account(refresh_token=completion.success)
        return CodexLoginFlowResult(
            login=login,
            completion=completion,
            account=account,
            opened_browser=opened_browser,
            browser_error=browser_error,
        )


async def _logout_codex_runtime(
    config_manager: ConfigManager,
    *,
    cwd: str | None,
    config_overrides: Mapping[str, Any] | None,
    command: Sequence[str] | None,
) -> CodexAccountSummary:
    launch_config = config_manager.build_codex_launch_config(
        cwd=cwd,
        config_overrides=config_overrides,
    )
    process = CodexAppServerProcess(launch_config, command=command)

    async with CodexAppServerClient(process) as client:
        await client.logout()
        return await client.read_account(refresh_token=False)


def get_codex_runtime_diagnostics(
    *,
    config_manager: ConfigManager | None = None,
    include_models: bool = True,
    refresh_account: bool = False,
    include_hidden_models: bool = False,
    model_page_size: int = 50,
    cwd: str | None = None,
    config_overrides: Mapping[str, Any] | None = None,
    command: Sequence[str] | None = None,
) -> CodexRuntimeDiagnostics:
    manager = config_manager or get_config_manager()
    return _run_sync(
        _collect_runtime_diagnostics(
            manager,
            include_models=include_models,
            refresh_account=refresh_account,
            include_hidden_models=include_hidden_models,
            model_page_size=model_page_size,
            cwd=cwd,
            config_overrides=config_overrides,
            command=command,
        )
    )


def start_codex_chatgpt_login(
    *,
    config_manager: ConfigManager | None = None,
    timeout_seconds: float = 180.0,
    browser_opener: BrowserOpener = webbrowser.open,
    open_browser: bool = True,
    cwd: str | None = None,
    config_overrides: Mapping[str, Any] | None = None,
    command: Sequence[str] | None = None,
) -> CodexLoginFlowResult:
    manager = config_manager or get_config_manager()
    return _run_sync(
        _run_chatgpt_login(
            manager,
            timeout_seconds=timeout_seconds,
            browser_opener=browser_opener,
            open_browser=open_browser,
            cwd=cwd,
            config_overrides=config_overrides,
            command=command,
        )
    )


def logout_codex_runtime(
    *,
    config_manager: ConfigManager | None = None,
    cwd: str | None = None,
    config_overrides: Mapping[str, Any] | None = None,
    command: Sequence[str] | None = None,
) -> CodexAccountSummary:
    manager = config_manager or get_config_manager()
    return _run_sync(
        _logout_codex_runtime(
            manager,
            cwd=cwd,
            config_overrides=config_overrides,
            command=command,
        )
    )
