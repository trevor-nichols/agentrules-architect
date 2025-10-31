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


def parse_response(response: Any) -> ParsedResponse:
    """Extract findings, reasoning, and tool calls from the SDK response."""
    message = response.choices[0].message

    content = getattr(message, "content", None)
    if isinstance(content, list):
        # Join multi-part content segments if the SDK returns them as lists.
        content = "\n".join(str(part) for part in content if part)
    findings = content or None

    reasoning = getattr(message, "reasoning_content", None) or None
    tool_calls = _normalise_tool_calls(getattr(message, "tool_calls", None))

    if tool_calls and not findings:
        findings = None

    return ParsedResponse(findings=findings, reasoning=reasoning, tool_calls=tool_calls)


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

