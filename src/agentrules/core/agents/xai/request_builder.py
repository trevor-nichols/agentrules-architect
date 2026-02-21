"""Helpers for preparing xAI chat completion payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agentrules.core.agents.base import ReasoningMode

from .config import ModelDefaults


@dataclass(frozen=True)
class PreparedRequest:
    """Represents an xAI chat completion payload ready for dispatch."""

    payload: dict[str, Any]


def prepare_request(
    *,
    model_name: str,
    content: str,
    reasoning: ReasoningMode,
    defaults: ModelDefaults,
    tools: list[Any] | None,
    temperature: float | None = None,
    response_format: dict[str, Any] | None = None,
) -> PreparedRequest:
    """
    Construct the request payload sent to the xAI Chat Completions API.
    """
    payload: dict[str, Any] = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": content,
            }
        ],
    }

    if defaults.tools_allowed and tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    effort = _map_reasoning_effort(reasoning, defaults)
    if effort is not None:
        payload["reasoning_effort"] = effort

    if temperature is not None:
        payload["temperature"] = temperature

    if response_format is not None:
        payload["response_format"] = response_format

    return PreparedRequest(payload=payload)


def _map_reasoning_effort(reasoning: ReasoningMode, defaults: ModelDefaults) -> str | None:
    if not defaults.reasoning_effort_supported:
        return None
    if reasoning in {
        ReasoningMode.MINIMAL,
        ReasoningMode.LOW,
        ReasoningMode.MEDIUM,
        ReasoningMode.HIGH,
    }:
        return reasoning.value

    if reasoning == ReasoningMode.ENABLED:
        return ReasoningMode.MEDIUM.value

    return None
