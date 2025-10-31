"""Helpers for preparing DeepSeek chat completion payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.agents.base import ReasoningMode

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
) -> PreparedRequest:
    """
    Construct the request payload sent to the DeepSeek Chat Completions API.

    DeepSeek exposes an OpenAI-compatible interface. Reasoning behaviour is
    driven by the selected model, so the ``reasoning`` argument is currently
    advisory but retained for future parity with other providers.
    """
    del reasoning  # Reasoning mode is inferred by the model; retained for parity.

    payload: dict[str, Any] = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": content,
            }
        ],
    }

    if defaults.max_output_tokens:
        payload["max_tokens"] = defaults.max_output_tokens

    if defaults.tools_allowed and tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    return PreparedRequest(payload=payload)

