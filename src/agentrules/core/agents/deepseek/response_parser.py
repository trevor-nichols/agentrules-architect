"""Utilities for normalising DeepSeek chat completion responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ParsedResponse:
    """Canonical representation of a DeepSeek response."""

    findings: str | None
    reasoning: str | None
    tool_calls: list[dict[str, Any]] | None
    assistant_tool_turn: dict[str, Any] | None = None


def parse_response(
    response: Any,
    *,
    native_tool_history: bool = False,
    thinking_enabled: bool = False,
) -> ParsedResponse:
    """Extract findings and retain the original assistant turn for native tool continuation."""
    message = response.choices[0].message
    content = getattr(message, "content", None)
    reasoning = getattr(message, "reasoning_content", None)
    raw_tool_calls = getattr(message, "tool_calls", None)
    tool_calls = _normalise_tool_calls(raw_tool_calls)

    assistant_tool_turn = None
    if native_tool_history and raw_tool_calls:
        if tool_calls is None or len(tool_calls) != len(raw_tool_calls):
            raise ValueError("DeepSeek tool turn contains an unsupported call type")
        assistant_tool_turn = _build_assistant_tool_turn(
            content, reasoning, tool_calls, thinking_enabled=thinking_enabled
        )

    if isinstance(content, list):
        # Join multi-part content segments for the public findings field.
        content = "\n".join(str(part) for part in content if part)

    return ParsedResponse(
        findings=content or None,
        reasoning=reasoning or None,
        tool_calls=tool_calls,
        assistant_tool_turn=assistant_tool_turn,
    )


def _build_assistant_tool_turn(
    content: Any,
    reasoning: Any,
    tool_calls: list[dict[str, Any]],
    *,
    thinking_enabled: bool,
) -> dict[str, Any]:
    if thinking_enabled and not isinstance(reasoning, str):
        raise ValueError("DeepSeek thinking tool turn is missing reasoning_content")

    ids: set[str] = set()
    for call in tool_calls:
        call_id = call["id"]
        if not isinstance(call_id, str) or not call_id.strip():
            raise ValueError("DeepSeek tool call is missing its ID")
        if call_id in ids:
            raise ValueError("DeepSeek tool turn has duplicate call IDs")
        ids.add(call_id)

        function = call["function"]
        name = function["name"]
        if not isinstance(name, str) or not name.strip():
            raise ValueError("DeepSeek tool call is missing its function name")
        if not isinstance(function["arguments"], str):
            raise ValueError("DeepSeek tool call arguments must be a string")

    turn = {"role": "assistant", "content": content, "tool_calls": tool_calls}
    if isinstance(reasoning, str):
        turn["reasoning_content"] = reasoning
    return turn


def _normalise_tool_calls(tool_calls: Any) -> list[dict[str, Any]] | None:
    if not tool_calls:
        return None

    normalised: list[dict[str, Any]] = []
    for call in tool_calls:
        call_type = _get_attr(call, "type")
        if call_type != "function":
            continue

        function = _get_attr(call, "function") or {}
        normalised.append(
            {
                "id": _get_attr(call, "id"),
                "type": call_type,
                "function": {
                    "name": _get_attr(function, "name"),
                    "arguments": _get_attr(function, "arguments"),
                },
            }
        )

    return normalised or None


def _get_attr(obj: Any, attr: str) -> Any:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(attr)
    return getattr(obj, attr, None)

