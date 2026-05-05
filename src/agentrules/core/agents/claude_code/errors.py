"""Claude Code runtime exceptions."""

from __future__ import annotations


class ClaudeCodeError(Exception):
    """Base exception for Claude Code runtime failures."""


class ClaudeCodeSDKImportError(ClaudeCodeError):
    """Raised when the Claude Agent SDK cannot be imported."""


class ClaudeCodeExecutionError(ClaudeCodeError):
    """Raised when a Claude Code SDK request fails or returns an error."""


__all__ = [
    "ClaudeCodeError",
    "ClaudeCodeExecutionError",
    "ClaudeCodeSDKImportError",
]
