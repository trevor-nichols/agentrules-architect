"""Thin lazy-import client boundary for the Claude Agent SDK."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping
from typing import Any

from .errors import ClaudeCodeExecutionError, ClaudeCodeSDKImportError


async def execute_query(
    prompt: str,
    options: Mapping[str, Any],
    timeout_seconds: float | None = None,
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
        collection = _collect_query_messages(query, prompt=prompt, options=sdk_options)
        if timeout_seconds is None:
            return await collection
        return await asyncio.wait_for(collection, timeout=timeout_seconds)
    except ClaudeCodeSDKImportError:
        raise
    except TimeoutError as exc:
        timeout_label = "unknown" if timeout_seconds is None else f"{timeout_seconds:g}"
        raise ClaudeCodeExecutionError(
            f"Claude Code SDK query timed out after {timeout_label} seconds."
        ) from exc
    except Exception as exc:
        raise ClaudeCodeExecutionError(f"Claude Code SDK query failed: {exc}") from exc


async def _collect_query_messages(query_fn: Any, *, prompt: str, options: Any) -> tuple[Any, ...]:
    return tuple([message async for message in query_fn(prompt=prompt, options=options)])


async def stream_query(prompt: str, options: Mapping[str, Any]) -> AsyncIterator[Any]:
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
        async for message in query(prompt=prompt, options=sdk_options):
            yield message
    except Exception as exc:
        raise ClaudeCodeExecutionError(f"Claude Code SDK query failed: {exc}") from exc


__all__ = ["execute_query", "stream_query"]
