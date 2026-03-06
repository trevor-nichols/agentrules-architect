"""Prompt template helpers for Gemini architects."""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any


def default_prompt_template() -> str:
    """Return the default persona-aware prompt template."""
    return (
        "Project context:\n"
        "{context}\n\n"
        "Complete the current analysis task using this context."
    )


def format_prompt(
    *,
    template: str,
    agent_name: str,
    agent_role: str,
    responsibilities: Iterable[str],
    context: dict[str, Any],
) -> str:
    """Render the analysis prompt with persona information and JSON context."""
    responsibilities_str = "\n".join(f"- {item}" for item in responsibilities)
    context_str = json.dumps(context, indent=2)

    return template.format(
        agent_name=agent_name,
        agent_role=agent_role,
        agent_responsibilities=responsibilities_str,
        context=context_str,
    )
