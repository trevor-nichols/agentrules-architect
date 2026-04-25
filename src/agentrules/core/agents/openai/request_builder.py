"""Helpers for preparing OpenAI API request payloads."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from agentrules.core.agents.base import ReasoningMode

ApiType = Literal["responses", "chat"]

_GPT5_RESPONSES_REASONING_SUPPORT: tuple[tuple[str, frozenset[str]], ...] = (
    ("gpt-5.5-pro", frozenset()),
    ("gpt-5.5", frozenset({"none", "low", "medium", "high", "xhigh"})),
    ("gpt-5.4-pro", frozenset({"medium", "high", "xhigh"})),
    ("gpt-5.4", frozenset({"none", "low", "medium", "high", "xhigh"})),
    ("gpt-5.3-codex", frozenset({"low", "medium", "high", "xhigh"})),
    ("gpt-5.2-pro", frozenset({"medium", "high", "xhigh"})),
    ("gpt-5.2-codex", frozenset({"low", "medium", "high", "xhigh"})),
    ("gpt-5.2", frozenset({"none", "low", "medium", "high", "xhigh"})),
    ("gpt-5.1-codex", frozenset({"low", "medium", "high"})),
    ("gpt-5.1", frozenset({"none", "low", "medium", "high"})),
    ("gpt-5-pro", frozenset({"high"})),
    ("gpt-5", frozenset({"minimal", "low", "medium", "high"})),
)


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

        reasoning_payload = _build_responses_reasoning_payload(
            model_name=model_name,
            reasoning=reasoning,
        )
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


def _build_responses_reasoning_payload(
    *,
    model_name: str,
    reasoning: ReasoningMode,
) -> dict[str, str] | None:
    supported_efforts = _resolve_supported_responses_efforts(model_name)

    if not supported_efforts:
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

    effort = _select_supported_responses_effort(
        reasoning=reasoning,
        supported_efforts=supported_efforts,
    )
    if effort is None:
        return None
    return {"effort": effort}


def _resolve_supported_responses_efforts(model_name: str) -> frozenset[str]:
    normalized = model_name.lower()
    for prefix, supported_efforts in _GPT5_RESPONSES_REASONING_SUPPORT:
        if normalized.startswith(prefix):
            return supported_efforts
    return frozenset()


def _select_supported_responses_effort(
    *,
    reasoning: ReasoningMode,
    supported_efforts: frozenset[str],
) -> str | None:
    if reasoning == ReasoningMode.DISABLED:
        return "none" if "none" in supported_efforts else None

    if reasoning in {ReasoningMode.ENABLED, ReasoningMode.DYNAMIC}:
        return "medium" if "medium" in supported_efforts else None

    if reasoning == ReasoningMode.MINIMAL:
        for effort in ("minimal", "none", "low"):
            if effort in supported_efforts:
                return effort
        return None

    if reasoning == ReasoningMode.XHIGH:
        for effort in ("xhigh", "high"):
            if effort in supported_efforts:
                return effort
        return None

    if reasoning in {ReasoningMode.LOW, ReasoningMode.MEDIUM, ReasoningMode.HIGH}:
        return reasoning.value if reasoning.value in supported_efforts else None

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
