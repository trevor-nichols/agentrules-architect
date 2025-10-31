"""Typed exceptions for the Gemini provider adapter."""


class GeminiClientInitializationError(RuntimeError):
    """Raised when the Gemini client cannot be constructed."""


class GeminiClientNotAvailableError(RuntimeError):
    """Raised when the client is accessed before successful initialization."""

