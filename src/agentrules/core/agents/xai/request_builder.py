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
    system_prompt: str | None = None,
    temperature: float | None = None,
    response_format: dict[str, Any] | None = None,
) -> PreparedRequest:
    """
    Construct the request payload sent to the xAI Chat Completions API.
    """
    messages: list[dict[str, Any]] = []
    if system_prompt:
        messages.append(
            {
                "role": "system",
                "content": system_prompt,
            }
        )
    messages.append(
        {
            "role": "user",
            "content": content,
        }
    )

    payload: dict[str, Any] = {
        "model": model_name,
        "messages": messages,
    }

    if defaults.tools_allowed and tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    effort = _map_reasoning_effort(reasoning, defaults, model_name=model_name)
    if effort is not None:
        payload["reasoning_effort"] = effort

    if temperature is not None:
        payload["temperature"] = temperature

    if response_format is not None:
        payload["response_format"] = response_format

    return PreparedRequest(payload=payload)


def _map_reasoning_effort(
    reasoning: ReasoningMode,
    defaults: ModelDefaults,
    *,
    model_name: str,
) -> str | None:
    accepted_efforts = defaults.accepted_reasoning_efforts
    if not accepted_efforts:
        return None

    effort: str | None
    if reasoning == ReasoningMode.DISABLED:
        effort = "none"
    elif reasoning in {ReasoningMode.XHIGH, ReasoningMode.MAX}:
        effort = (
            ReasoningMode.HIGH.value
            if defaults.normalize_higher_efforts_to_high
            else reasoning.value
        )
    elif reasoning in {
        ReasoningMode.MINIMAL,
        ReasoningMode.LOW,
        ReasoningMode.MEDIUM,
        ReasoningMode.HIGH,
    }:
        effort = reasoning.value
    elif reasoning in {ReasoningMode.ENABLED, ReasoningMode.DYNAMIC}:
        effort = defaults.enabled_reasoning_effort
    else:
        effort = None

    if effort is None:
        return None
    if effort not in accepted_efforts:
        supported = ", ".join(sorted(accepted_efforts))
        raise ValueError(
            f"Reasoning mode '{reasoning.value}' is not supported for xAI model '{model_name}'. "
            f"Accepted reasoning efforts: {supported}."
        )
    return effort
