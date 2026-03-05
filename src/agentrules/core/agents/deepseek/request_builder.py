"""Helpers for preparing DeepSeek chat completion payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agentrules.core.agents.base import ReasoningMode

from .config import ModelDefaults


@dataclass(frozen=True)
class PreparedRequest:
    """Represents a DeepSeek chat completion payload ready for dispatch."""

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
    Construct the request payload sent to the DeepSeek Chat Completions API.

    DeepSeek exposes an OpenAI-compatible interface. Reasoning behaviour is
    driven by the selected model, so the ``reasoning`` argument is currently
    advisory but retained for future parity with other providers.
    """
    del reasoning  # Reasoning mode is inferred by the model; retained for parity.

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

    if defaults.max_output_tokens:
        payload["max_tokens"] = defaults.max_output_tokens

    if defaults.tools_allowed and tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    if temperature is not None and defaults.tools_allowed:
        payload["temperature"] = temperature

    if response_format is not None:
        payload["response_format"] = response_format

    return PreparedRequest(payload=payload)
