"""Helpers for constructing and resolving provider system prompts."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

_SYSTEM_PROMPT_KEYS: tuple[str, ...] = (
    "system_prompt",
    "developer_instructions",
    "instructions",
)


def build_agent_system_prompt(
    *,
    agent_name: str,
    agent_role: str,
    responsibilities: Iterable[str] | None,
) -> str:
    """
    Build a default system prompt for an architect request.

    The prompt intentionally carries stable persona and responsibility guidance.
    Phase-specific task payloads should stay in the user prompt.
    """
    lines: list[str] = [
        f"You are {agent_name}, responsible for {agent_role}.",
    ]

    cleaned_responsibilities = [item.strip() for item in (responsibilities or []) if item and item.strip()]
    if cleaned_responsibilities:
        lines.append("")
        lines.append("Responsibilities:")
        lines.extend(f"- {item}" for item in cleaned_responsibilities)

    lines.append("")
    lines.append("Prioritize accurate, actionable, and structured analysis.")
    return "\n".join(lines)


def resolve_system_prompt(
    *,
    context: Mapping[str, Any] | None,
    default_prompt: str | None,
) -> str | None:
    """
    Resolve system prompt text from request context, then fallback to default.

    Context-level overrides are useful for phase-specific experiments without
    changing architect defaults.
    """
    if context:
        for key in _SYSTEM_PROMPT_KEYS:
            value = context.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return default_prompt
