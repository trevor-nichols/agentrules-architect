"""Utilities for parsing Claude Agent SDK message streams."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from agentrules.core.utils.provider_utils import sdk_object_to_dict


@dataclass(frozen=True)
class ParsedResponse:
    """The canonical representation of a Claude Code SDK response."""

    findings: str | None
    structured_output: Any | None
    tool_calls: list[dict[str, Any]] | None
    usage: dict[str, Any] | None
    error_message: str | None
    messages: tuple[Any, ...]


def parse_response(messages: Sequence[Any]) -> ParsedResponse:
    """Parse SDK messages into the AgentRules provider response shape."""

    text_parts: list[str] = []
    result_text: str | None = None
    structured_output: Any | None = None
    tool_calls: list[dict[str, Any]] = []
    usage: dict[str, Any] | None = None
    errors: list[str] = []
    refusal_seen = False

    for message in messages:
        message_type = message.__class__.__name__

        if getattr(message, "stop_reason", None) == "refusal" and not refusal_seen:
            errors.append("Claude Code returned a model refusal; no automatic fallback was assumed.")
            refusal_seen = True

        if message_type == "AssistantMessage":
            assistant_error = getattr(message, "error", None)
            if assistant_error:
                errors.append(str(assistant_error))
            assistant_usage = sdk_object_to_dict(getattr(message, "usage", None))
            if assistant_usage is not None:
                usage = assistant_usage
            for block in getattr(message, "content", []) or []:
                _collect_content_block(block, text_parts=text_parts, tool_calls=tool_calls)
            continue

        if message_type == "ResultMessage":
            result_usage = sdk_object_to_dict(getattr(message, "usage", None))
            if result_usage is not None:
                usage = result_usage
            result_value = getattr(message, "result", None)
            if isinstance(result_value, str) and result_value.strip():
                result_text = result_value
            structured_value = getattr(message, "structured_output", None)
            if structured_value is not None:
                structured_output = structured_value
            if getattr(message, "is_error", False):
                errors.append(_format_result_error(message))
            continue

    findings = result_text or "".join(text_parts).strip() or None
    return ParsedResponse(
        findings=findings,
        structured_output=structured_output,
        tool_calls=tool_calls or None,
        usage=usage,
        error_message="; ".join(error for error in errors if error) or None,
        messages=tuple(messages),
    )


def _collect_content_block(
    block: Any,
    *,
    text_parts: list[str],
    tool_calls: list[dict[str, Any]],
) -> None:
    block_type = block.__class__.__name__
    if block_type == "TextBlock":
        text = getattr(block, "text", None)
        if isinstance(text, str):
            text_parts.append(text)
        return

    if block_type == "ToolUseBlock":
        raw_input = getattr(block, "input", None)
        tool_input = sdk_object_to_dict(raw_input)
        tool_calls.append(
            {
                "id": getattr(block, "id", None),
                "name": getattr(block, "name", None),
                "input": tool_input if tool_input is not None else raw_input,
            }
        )
        return

    if isinstance(block, dict):
        block_kind = block.get("type")
        if block_kind == "text" and isinstance(block.get("text"), str):
            text_parts.append(block["text"])
        if block_kind == "tool_use":
            tool_calls.append(
                {
                    "id": block.get("id"),
                    "name": block.get("name"),
                    "input": block.get("input"),
                }
            )


def _format_result_error(message: Any) -> str:
    errors = getattr(message, "errors", None)
    if isinstance(errors, list) and errors:
        return ", ".join(str(error) for error in errors)
    subtype = getattr(message, "subtype", None)
    if subtype:
        return str(subtype)
    return "Claude Code SDK returned an error result."


__all__ = ["ParsedResponse", "parse_response"]
