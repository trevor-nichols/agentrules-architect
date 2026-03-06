"""Prompt templates and formatting helpers for xAI agents."""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any


def default_prompt_template() -> str:
    """Default analysis prompt when callers do not provide one."""
    return (
        "Project context:\n"
        "{context}\n\n"
        "Complete the current analysis task using this context."
    )


def _format_responsibilities(responsibilities: Iterable[str] | None) -> str:
    if not responsibilities:
        return "Analyzing software architecture quality and risks"
    return "\n".join(f"- {item}" for item in responsibilities)


def _format_context(context: Any) -> str:
    if isinstance(context, str):
        return context
    if isinstance(context, dict):
        return json.dumps(context, indent=2)
    return json.dumps(context, default=str, indent=2)


def format_prompt(
    *,
    template: str,
    agent_name: str,
    agent_role: str,
    responsibilities: Iterable[str] | None,
    context: Any,
) -> str:
    """Render the final prompt string injected into xAI requests."""
    return template.format(
        agent_name=agent_name,
        agent_role=agent_role,
        agent_responsibilities=_format_responsibilities(responsibilities),
        context=_format_context(context),
    )
