"""Response parsing utilities for Gemini."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from google.protobuf.struct_pb2 import Struct


@dataclass
class GeminiParsedResponse:
    """Normalized payload extracted from the Gemini SDK response."""

    findings: str | None = None
    function_calls: list[dict[str, Any]] = field(default_factory=list)


def _collect_candidate_parts(response: Any) -> list[Any]:
    """Safely collect all content parts from a Gemini response."""
    parts: list[Any] = []
    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        candidate_parts = getattr(content, "parts", None)
        if not candidate_parts:
            continue
        parts.extend(candidate_parts)
    return parts


def _extract_function_call_args(function_call: Any) -> dict[str, Any]:
    """Normalize Gemini function-call arguments into a dictionary."""
    if function_call is None:
        return {}

    args_obj = getattr(function_call, "args", None)
    if isinstance(args_obj, dict):
        return args_obj
    if isinstance(args_obj, Struct):
        return {key: value for key, value in args_obj.items()}

    arguments_obj = getattr(function_call, "arguments", None)
    if isinstance(arguments_obj, dict):
        return arguments_obj

    return {}


def parse_generate_response(response: Any) -> GeminiParsedResponse:
    """Extract text content and function calls from a Gemini response object."""
    payload = GeminiParsedResponse()

    # Try direct text attribute first (newer SDKs expose this).
    payload.findings = getattr(response, "text", None)

    if not payload.findings:
        for part in _collect_candidate_parts(response):
            part_text = getattr(part, "text", None)
            if part_text:
                payload.findings = part_text
                break

    for part in _collect_candidate_parts(response):
        function_call = getattr(part, "function_call", None)
        if function_call is None:
            continue
        payload.function_calls.append(
            {
                "name": getattr(function_call, "name", None),
                "args": _extract_function_call_args(function_call),
            }
        )

    return payload
