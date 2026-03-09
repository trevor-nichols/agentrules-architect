"""Codex app-server runtime exceptions."""

from __future__ import annotations

from typing import Any


class CodexError(RuntimeError):
    """Base exception for Codex runtime failures."""


class CodexExecutableNotFoundError(CodexError):
    """Raised when the configured Codex executable cannot be resolved."""


class CodexProcessError(CodexError):
    """Raised when the Codex app-server process cannot be started or exits unexpectedly."""

    def __init__(self, message: str, *, stderr: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.stderr = stderr


class CodexProtocolError(CodexError):
    """Raised when stdout does not contain valid Codex JSON-RPC messages."""


class CodexJsonRpcError(CodexError):
    """Raised when app-server responds with a JSON-RPC error payload."""

    def __init__(self, code: int | None, message: str, data: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.data = data
