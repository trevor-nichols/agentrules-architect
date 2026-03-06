"""Helpers for constructing and resolving provider system prompts."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

_SYSTEM_PROMPT_KEYS: tuple[str, ...] = (
    "system_prompt",
    "developer_instructions",
    "instructions",
)


def normalize_responsibilities(responsibilities: object) -> list[str]:
    """
    Normalize model- or config-provided responsibility lists for prompt use.

    Providers occasionally return mixed payloads in JSON fallback modes. Keep
    meaningful scalar items, trim whitespace, and drop container values that
    would only inject noisy representations into prompts.
    """

    if responsibilities is None:
        return []

    items: Iterable[object]
    if isinstance(responsibilities, str):
        items = [responsibilities]
    elif isinstance(responsibilities, Mapping):
        return []
    elif isinstance(responsibilities, Iterable):
        items = responsibilities
    else:
        items = [responsibilities]

    cleaned: list[str] = []
    for item in items:
        if isinstance(item, str):
            candidate = item.strip()
        elif isinstance(item, (bool, int, float)):
            candidate = str(item).strip()
        else:
            continue
        if candidate:
            cleaned.append(candidate)
    return cleaned


def build_agent_system_prompt(
    *,
    agent_name: str,
    agent_role: str,
    responsibilities: object,
) -> str:
    """
    Build a default system prompt for an architect request.

    The prompt intentionally carries stable persona and responsibility guidance.
    Phase-specific task payloads should stay in the user prompt.
    """
    lines: list[str] = [
        f"You are {agent_name}, responsible for {agent_role}.",
    ]

    cleaned_responsibilities = normalize_responsibilities(responsibilities)
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
