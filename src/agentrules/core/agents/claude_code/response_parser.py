"""Utilities for parsing Claude Agent SDK message streams."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any


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

    for message in messages:
        message_type = message.__class__.__name__

        if message_type == "AssistantMessage":
            assistant_error = getattr(message, "error", None)
            if assistant_error:
                errors.append(str(assistant_error))
            assistant_usage = _to_dict(getattr(message, "usage", None))
            if assistant_usage is not None:
                usage = assistant_usage
            for block in getattr(message, "content", []) or []:
                _collect_content_block(block, text_parts=text_parts, tool_calls=tool_calls)
            continue

        if message_type == "ResultMessage":
            result_usage = _to_dict(getattr(message, "usage", None))
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
        tool_calls.append(
            {
                "id": getattr(block, "id", None),
                "name": getattr(block, "name", None),
                "input": _to_dict(getattr(block, "input", None)) or getattr(block, "input", None),
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


def _to_dict(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        if isinstance(dumped, dict):
            return dumped
    if hasattr(value, "to_dict"):
        dumped = value.to_dict()
        if isinstance(dumped, dict):
            return dumped
    if hasattr(value, "__dict__"):
        return {
            key: item
            for key, item in value.__dict__.items()
            if not key.startswith("_")
        }
    return None


__all__ = ["ParsedResponse", "parse_response"]
