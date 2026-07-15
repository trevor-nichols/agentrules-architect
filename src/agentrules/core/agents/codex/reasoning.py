"""Validation policy for runtime-advertised Codex reasoning efforts."""

from __future__ import annotations

import re

KNOWN_RUNTIME_REASONING_EFFORT_ORDER: tuple[str, ...] = (
    "none",
    "minimal",
    "low",
    "medium",
    "high",
    "xhigh",
    "max",
    "ultra",
)

_SAFE_RUNTIME_REASONING_EFFORT = re.compile(r"^[a-z][a-z0-9_-]{0,31}$", re.ASCII)
_INVALID_RUNTIME_REASONING_EFFORT_MESSAGE = (
    "Codex runtime reasoning effort must be a lowercase ASCII token containing at most "
    "32 letters, numbers, underscores, or hyphens."
)


def normalize_runtime_reasoning_effort(value: object) -> str | None:
    """Return a safe runtime effort token, or ``None`` when it is malformed."""

    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not _SAFE_RUNTIME_REASONING_EFFORT.fullmatch(normalized):
        return None
    return normalized


def require_runtime_reasoning_effort(value: object) -> str:
    """Return a safe runtime effort token or raise an actionable configuration error."""

    normalized = normalize_runtime_reasoning_effort(value)
    if normalized is None:
        raise ValueError(_INVALID_RUNTIME_REASONING_EFFORT_MESSAGE)
    return normalized


__all__ = [
    "KNOWN_RUNTIME_REASONING_EFFORT_ORDER",
    "normalize_runtime_reasoning_effort",
    "require_runtime_reasoning_effort",
]
