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

    DeepSeek V4 exposes thinking and non-thinking modes on the same model ID.
    The OpenAI-compatible SDK carries the thinking toggle in ``extra_body``.
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

    thinking_enabled = False
    if defaults.supports_thinking_toggle:
        thinking_enabled, effort = _resolve_v4_reasoning(reasoning)
        payload["extra_body"] = {
            "thinking": {"type": "enabled" if thinking_enabled else "disabled"}
        }
        if effort is not None:
            if effort not in defaults.accepted_reasoning_efforts:
                accepted = ", ".join(sorted(defaults.accepted_reasoning_efforts))
                raise ValueError(
                    f"Reasoning effort '{effort}' is not supported by {model_name}. "
                    f"Supported efforts: {accepted}."
                )
            payload["reasoning_effort"] = effort

    if defaults.max_output_tokens:
        payload["max_tokens"] = defaults.max_output_tokens

    if defaults.tools_allowed and tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    if temperature is not None and defaults.supports_sampling and not thinking_enabled:
        payload["temperature"] = temperature

    if response_format is not None:
        payload["response_format"] = response_format

    return PreparedRequest(payload=payload)


def _resolve_v4_reasoning(reasoning: ReasoningMode) -> tuple[bool, str | None]:
    if reasoning in {ReasoningMode.DISABLED, ReasoningMode.TEMPERATURE}:
        return False, None
    if reasoning == ReasoningMode.XHIGH:
        return True, "max"
    return True, "high"
