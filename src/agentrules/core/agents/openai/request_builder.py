"""Helpers for preparing OpenAI API request payloads."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from agentrules.core.agents.base import ReasoningMode

ApiType = Literal["responses", "chat"]


@dataclass(frozen=True)
class PreparedRequest:
    """Represents a fully constructed request ready for dispatch."""

    api: ApiType
    payload: dict[str, Any]


def prepare_request(
    *,
    model_name: str,
    content: str,
    reasoning: ReasoningMode,
    temperature: float | None,
    tools: list[Any] | None,
    text_verbosity: str | None,
    use_responses_api: bool,
    system_prompt: str | None = None,
    structured_text: dict[str, Any] | None = None,
    chat_response_format: dict[str, Any] | None = None,
) -> PreparedRequest:
    """Build an OpenAI SDK request payload based on the active model pathway."""
    if use_responses_api:
        payload: dict[str, Any] = {
            "model": model_name,
            "input": content,
        }
        if system_prompt:
            payload["instructions"] = system_prompt

        reasoning_payload = _build_responses_reasoning_payload(reasoning)
        if reasoning_payload:
            payload["reasoning"] = reasoning_payload

        text_config = _build_text_config(text_verbosity, structured_text)
        if text_config:
            payload["text"] = text_config

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        if _should_attach_temperature(model_name, reasoning, temperature):
            payload["temperature"] = temperature

        return PreparedRequest(api="responses", payload=payload)

    messages: list[dict[str, Any]] = []
    if system_prompt:
        messages.append(
            {
                "role": "developer",
                "content": system_prompt,
            }
        )
    messages.append(
        {
            "role": "user",
            "content": content,
        }
    )

    payload = {
        "model": model_name,
        "messages": messages,
    }

    reasoning_params = _build_chat_reasoning_params(model_name, reasoning)
    if reasoning_params:
        payload.update(reasoning_params)

    if _should_attach_temperature(model_name, reasoning, temperature):
        payload["temperature"] = temperature

    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    if chat_response_format:
        payload["response_format"] = chat_response_format

    return PreparedRequest(api="chat", payload=payload)


def _build_responses_reasoning_payload(reasoning: ReasoningMode) -> dict[str, str] | None:
    if reasoning == ReasoningMode.XHIGH:
        return {"effort": ReasoningMode.HIGH.value}

    if reasoning in {
        ReasoningMode.MINIMAL,
        ReasoningMode.LOW,
        ReasoningMode.MEDIUM,
        ReasoningMode.HIGH,
    }:
        return {"effort": reasoning.value}

    if reasoning == ReasoningMode.ENABLED:
        return {"effort": ReasoningMode.MEDIUM.value}

    return None


def _build_text_config(
    text_verbosity: str | None,
    structured_text: dict[str, Any] | None,
) -> dict[str, Any] | None:
    text_config: dict[str, Any] = {}

    if text_verbosity:
        text_config["verbosity"] = text_verbosity

    if structured_text:
        text_config.update(structured_text)

    if not text_config:
        return None
    return text_config


def _build_chat_reasoning_params(
    model_name: str,
    reasoning: ReasoningMode,
) -> dict[str, Any] | None:
    normalized = model_name.lower()
    if normalized not in {"o3", "o4-mini"}:
        return None

    if reasoning == ReasoningMode.ENABLED:
        effort = "high"
    elif reasoning == ReasoningMode.MINIMAL:
        effort = ReasoningMode.LOW.value
    elif reasoning in {ReasoningMode.LOW, ReasoningMode.MEDIUM, ReasoningMode.HIGH, ReasoningMode.XHIGH}:
        if reasoning == ReasoningMode.XHIGH:
            effort = ReasoningMode.HIGH.value
        else:
            effort = reasoning.value
    else:
        effort = ReasoningMode.MEDIUM.value

    return {"reasoning_effort": effort}


def _should_attach_temperature(
    model_name: str,
    reasoning: ReasoningMode,
    temperature: float | None,
) -> bool:
    if temperature is None:
        return False

    return reasoning == ReasoningMode.TEMPERATURE or model_name.lower() == "gpt-4.1"
