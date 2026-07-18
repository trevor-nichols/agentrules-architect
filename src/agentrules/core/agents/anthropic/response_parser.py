"""Helpers for normalising Anthropic responses."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class AnthropicRefusalError(RuntimeError):
    """Raised when Anthropic returns a successful transport response that refused the request."""

    def __init__(self, *, category: str | None = None, explanation: str | None = None) -> None:
        self.category = category
        self.explanation = explanation

        message = "Anthropic refused the request"
        if category:
            message += f" (category: {category})"
        if explanation:
            message += f": {explanation}"
        super().__init__(message)


@dataclass(frozen=True)
class ParsedResponse:
    """Represents the extracted findings and optional tool calls."""

    findings: str | None
    tool_calls: list[dict[str, Any]] | None


def parse_response(response: Any) -> ParsedResponse:
    """Extract human-readable findings and tool metadata from the response."""
    raise_for_refusal(response)

    findings_parts: list[str] = []
    tool_calls: list[dict[str, Any]] = []

    content = getattr(response, "content", None)
    if content is None and isinstance(response, dict):
        content = response.get("content")

    for block in content or []:
        text = _extract_text(block)
        if text:
            findings_parts.append(text)

        tool_call = _extract_tool_use(block)
        if tool_call:
            tool_calls.append(tool_call)

    findings = "\n".join(findings_parts).strip() or None
    return ParsedResponse(findings=findings, tool_calls=tool_calls or None)


def raise_for_refusal(response: Any) -> None:
    """Raise a typed error when a Messages response reports a refusal stop reason."""

    if _get_field(response, "stop_reason") != "refusal":
        return

    stop_details = _get_field(response, "stop_details")
    category = _safe_detail(_get_field(stop_details, "category"), max_length=80)
    explanation = _safe_detail(_get_field(stop_details, "explanation"), max_length=500)
    raise AnthropicRefusalError(category=category, explanation=explanation)


def _get_field(value: Any, field: str) -> Any:
    if isinstance(value, dict):
        return value.get(field)
    return getattr(value, field, None)


def _safe_detail(value: Any, *, max_length: int) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.split())[:max_length]
    return normalized or None


def _extract_text(block: Any) -> str | None:
    if isinstance(block, dict):
        text = block.get("text")
        if isinstance(text, str):
            return text
        return None

    return getattr(block, "text", None)


def _extract_tool_use(block: Any) -> dict[str, Any] | None:
    if isinstance(block, dict):
        if block.get("type") == "tool_use":
            return {
                "id": block.get("id"),
                "name": block.get("name"),
                "input": block.get("input"),
            }
        tool_use = block.get("tool_use")
    else:
        if getattr(block, "type", None) == "tool_use":
            return {
                "id": getattr(block, "id", None),
                "name": getattr(block, "name", None),
                "input": getattr(block, "input", None),
            }
        tool_use = getattr(block, "tool_use", None)

    if not tool_use:
        return None

    tool_id = getattr(tool_use, "id", None) if not isinstance(tool_use, dict) else tool_use.get("id")
    tool_name = getattr(tool_use, "name", None) if not isinstance(tool_use, dict) else tool_use.get("name")
    tool_input = getattr(tool_use, "input", None) if not isinstance(tool_use, dict) else tool_use.get("input")

    return {
        "id": tool_id,
        "name": tool_name,
        "input": tool_input,
    }
