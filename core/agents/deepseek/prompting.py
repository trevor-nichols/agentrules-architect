"""Prompt templates and formatting helpers for DeepSeek agents."""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any


def default_prompt_template() -> str:
    """Default analysis prompt applied when callers do not provide one."""
    return """You are {agent_name}, a code architecture analyst with expertise in {agent_role}.

Your responsibilities:
{agent_responsibilities}

Please analyze the following context and provide a detailed analysis:

Context:
{context}

Provide your analysis in a structured format with clear sections and actionable insights."""


def _format_responsibilities(responsibilities: Iterable[str] | None) -> str:
    if not responsibilities:
        return "Analyzing code architecture and patterns"
    return "\n".join(f"- {resp}" for resp in responsibilities)


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
    context: dict[str, Any] | Any,
) -> str:
    """Build the final prompt string injected into DeepSeek requests."""
    return template.format(
        agent_name=agent_name,
        agent_role=agent_role,
        agent_responsibilities=_format_responsibilities(responsibilities),
        context=_format_context(context),
    )
