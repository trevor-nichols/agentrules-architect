"""Thin lazy-import client boundary for the Claude Agent SDK."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator, Iterable, Mapping
from contextlib import asynccontextmanager, suppress
from inspect import isawaitable
from typing import Any, cast

from .errors import ClaudeCodeExecutionError, ClaudeCodeSDKImportError

_ENV_SANITIZATION_LOCK = asyncio.Lock()


class _MissingEnvironmentValue:
    pass


_MISSING_ENV = _MissingEnvironmentValue()


async def execute_query(
    prompt: str,
    options: Mapping[str, Any],
    timeout_seconds: float | None = None,
    sanitized_env_vars: Iterable[str] = (),
) -> tuple[Any, ...]:
    """Execute a Claude Agent SDK query and collect all emitted messages."""

    try:
        from claude_agent_sdk import ClaudeAgentOptions, query
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised by packaging/import smoke
        raise ClaudeCodeSDKImportError(
            "The Claude Agent SDK is not installed. Install the 'claude-agent-sdk' package "
            "to use the Claude Code runtime provider."
        ) from exc

    try:
        sdk_options = ClaudeAgentOptions(**dict(options))
        collection = _collect_query_messages(
            query,
            prompt=prompt,
            options=sdk_options,
            sanitized_env_vars=sanitized_env_vars,
        )
        if timeout_seconds is None:
            return await collection
        return await asyncio.wait_for(collection, timeout=timeout_seconds)
    except ClaudeCodeSDKImportError:
        raise
    except TimeoutError as exc:
        raise _build_timeout_error(timeout_seconds) from exc
    except Exception as exc:
        raise ClaudeCodeExecutionError(f"Claude Code SDK query failed: {exc}") from exc


async def _collect_query_messages(
    query_fn: Any,
    *,
    prompt: str,
    options: Any,
    sanitized_env_vars: Iterable[str] = (),
) -> tuple[Any, ...]:
    iterator = query_fn(prompt=prompt, options=options).__aiter__()
    messages: list[Any] = []
    first_message = True
    try:
        while True:
            try:
                message = await _next_query_message(
                    iterator,
                    sanitized_env_vars=sanitized_env_vars if first_message else (),
                )
            except StopAsyncIteration:
                return tuple(messages)
            first_message = False
            messages.append(message)
    except BaseException:
        await _close_async_iterator(iterator)
        raise


async def stream_query(
    prompt: str,
    options: Mapping[str, Any],
    timeout_seconds: float | None = None,
    sanitized_env_vars: Iterable[str] = (),
) -> AsyncIterator[Any]:
    """Execute a Claude Agent SDK query and yield messages as they arrive."""

    try:
        from claude_agent_sdk import ClaudeAgentOptions, query
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised by packaging/import smoke
        raise ClaudeCodeSDKImportError(
            "The Claude Agent SDK is not installed. Install the 'claude-agent-sdk' package "
            "to use the Claude Code runtime provider."
        ) from exc

    try:
        sdk_options = ClaudeAgentOptions(**dict(options))
        async for message in _stream_query_messages(
            query,
            prompt=prompt,
            options=sdk_options,
            timeout_seconds=timeout_seconds,
            sanitized_env_vars=sanitized_env_vars,
        ):
            yield message
    except TimeoutError as exc:
        raise _build_timeout_error(timeout_seconds) from exc
    except Exception as exc:
        raise ClaudeCodeExecutionError(f"Claude Code SDK query failed: {exc}") from exc


async def _stream_query_messages(
    query_fn: Any,
    *,
    prompt: str,
    options: Any,
    timeout_seconds: float | None,
    sanitized_env_vars: Iterable[str] = (),
) -> AsyncIterator[Any]:
    iterator = query_fn(prompt=prompt, options=options).__aiter__()
    loop = asyncio.get_running_loop()
    deadline = None if timeout_seconds is None else loop.time() + timeout_seconds
    first_message = True
    try:
        while True:
            remaining_seconds = None
            if deadline is not None:
                remaining_seconds = deadline - loop.time()
                if remaining_seconds <= 0:
                    raise TimeoutError
            try:
                message = await _next_query_message(
                    iterator,
                    timeout_seconds=remaining_seconds,
                    sanitized_env_vars=sanitized_env_vars if first_message else (),
                )
            except StopAsyncIteration:
                return
            first_message = False
            yield message
    except TimeoutError:
        raise
    finally:
        await _close_async_iterator(iterator)


async def _next_query_message(
    iterator: AsyncIterator[Any],
    *,
    timeout_seconds: float | None = None,
    sanitized_env_vars: Iterable[str] = (),
) -> Any:
    async with _temporary_sdk_environment(sanitized_env_vars):
        if timeout_seconds is None:
            return await anext(iterator)
        return await asyncio.wait_for(anext(iterator), timeout=timeout_seconds)


@asynccontextmanager
async def _temporary_sdk_environment(sanitized_env_vars: Iterable[str]) -> AsyncIterator[None]:
    env_vars = _normalize_env_vars(sanitized_env_vars)
    if not env_vars:
        yield
        return

    # The Claude Agent SDK merges options.env on top of inherited os.environ and
    # does not expose an unset sentinel. Scrub while advancing the SDK through
    # startup so inherited API-key auth cannot override Claude Code OAuth.
    async with _ENV_SANITIZATION_LOCK:
        snapshot = _unset_process_env(env_vars)
        try:
            yield
        finally:
            _restore_process_env(snapshot)


def _normalize_env_vars(env_vars: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(env_var for env_var in env_vars if env_var))


def _unset_process_env(env_vars: tuple[str, ...]) -> dict[str, str | _MissingEnvironmentValue]:
    snapshot: dict[str, str | _MissingEnvironmentValue] = {}
    for env_var in env_vars:
        snapshot[env_var] = os.environ.get(env_var, _MISSING_ENV)
        os.environ.pop(env_var, None)
    return snapshot


def _restore_process_env(snapshot: Mapping[str, str | _MissingEnvironmentValue]) -> None:
    for env_var, previous_value in snapshot.items():
        if previous_value is _MISSING_ENV:
            os.environ.pop(env_var, None)
        else:
            os.environ[env_var] = cast("str", previous_value)


async def _close_async_iterator(iterator: AsyncIterator[Any]) -> None:
    close = getattr(iterator, "aclose", None)
    if callable(close):
        with suppress(Exception):
            result = close()
            if isawaitable(result):
                await result


def _build_timeout_error(timeout_seconds: float | None) -> ClaudeCodeExecutionError:
    timeout_label = "unknown" if timeout_seconds is None else f"{timeout_seconds:g}"
    return ClaudeCodeExecutionError(f"Claude Code SDK query timed out after {timeout_label} seconds.")


__all__ = ["execute_query", "stream_query"]
