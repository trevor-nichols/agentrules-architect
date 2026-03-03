"""Utilities for normalising OpenAI SDK responses."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .request_builder import ApiType


@dataclass
class ParsedResponse:
    """The canonical representation of an OpenAI model response."""

    findings: str | None
    tool_calls: list[dict[str, Any]] | None


def parse_response(response: Any, api_type: ApiType) -> ParsedResponse:
    """Route to the correct parser based on the executed API."""
    if api_type == "responses":
        return _parse_responses_output(response)
    return _parse_chat_output(response)


def _parse_chat_output(response: Any) -> ParsedResponse:
    message = response.choices[0].message
    findings = message.content or None
    tool_calls = None

    if message.tool_calls:
        tool_calls = [
            {
                "id": call.id,
                "type": call.type,
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                },
            }
            for call in message.tool_calls
            if getattr(call, "type", None) == "function"
        ] or None

    return ParsedResponse(findings=findings, tool_calls=tool_calls)


def _parse_responses_output(response: Any) -> ParsedResponse:
    response_dict = _as_dict(response)
    output_items = response_dict.get("output", []) or []
    text_segments: list[str] = []
    tool_calls: list[dict[str, Any]] = []

    for item in output_items:
        item_dict = _as_dict(item)
        item_type = item_dict.get("type")

        # Responses API function/custom tool calls are top-level output items.
        if item_type in {"function_call", "custom_tool_call"}:
            normalized = _normalize_tool_call(item_dict)
            if normalized:
                tool_calls.append(normalized)
            continue

        if item_type != "message":
            continue

        for part in item_dict.get("content", []) or []:
            part_dict = _as_dict(part)
            part_type = part_dict.get("type")
            if part_type == "output_text":
                text_value = part_dict.get("text")
                if text_value:
                    text_segments.append(str(text_value))
                continue

            # Keep compatibility for synthetic fixtures that place tool calls in message parts.
            if part_type in {"function_call", "custom_tool_call"}:
                normalized = _normalize_tool_call(part_dict)
                if normalized:
                    tool_calls.append(normalized)

    if not text_segments:
        aggregated = response_dict.get("output_text") or getattr(response, "output_text", None)
        if aggregated:
            text_segments.append(str(aggregated))

    findings = "\n".join(text_segments).strip() if text_segments else None
    normalized_tool_calls = tool_calls or None
    return ParsedResponse(findings=findings, tool_calls=normalized_tool_calls)


def _normalize_tool_call(part_dict: Mapping[str, Any]) -> dict[str, Any] | None:
    part_type = part_dict.get("type")
    call_id = part_dict.get("id") or part_dict.get("call_id")
    if part_type == "function_call":
        return {
            "id": call_id,
            "type": "function",
            "function": {
                "name": part_dict.get("name"),
                "arguments": part_dict.get("arguments", ""),
            },
        }
    if part_type == "custom_tool_call":
        return {
            "id": call_id,
            "type": "custom",
            "name": part_dict.get("name"),
            "input": part_dict.get("input"),
        }
    return None


def _as_dict(obj: Any) -> dict[str, Any]:
    if isinstance(obj, dict):
        return obj

    for attr in ("model_dump", "to_dict", "dict"):
        method = getattr(obj, attr, None)
        if not callable(method):
            continue

        try:
            result = method()
        except TypeError:
            try:
                result = method(mode="python")  # type: ignore[arg-type]
            except Exception:
                continue
        except Exception:
            continue

        if isinstance(result, Mapping):
            return dict(result)
        if hasattr(result, "__dict__"):
            return {
                key: value
                for key, value in vars(result).items()
                if not key.startswith("_")
            }

    if hasattr(obj, "__dict__"):
        return {
            key: value
            for key, value in obj.__dict__.items()
            if not key.startswith("_")
        }

    return {}
