"""Thin lazy-import client boundary for the Claude Agent SDK."""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from typing import Any

from .errors import ClaudeCodeExecutionError, ClaudeCodeSDKImportError


async def execute_query(prompt: str, options: Mapping[str, Any]) -> tuple[Any, ...]:
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
        return tuple([message async for message in query(prompt=prompt, options=sdk_options)])
    except ClaudeCodeSDKImportError:
        raise
    except Exception as exc:
        raise ClaudeCodeExecutionError(f"Claude Code SDK query failed: {exc}") from exc


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
