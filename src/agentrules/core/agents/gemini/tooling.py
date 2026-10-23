"""Tool configuration helpers for Gemini."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from google.genai import types as genai_types

from agentrules.core.agents.base import ModelProvider


def resolve_tool_config(
    explicit_tools: list[Any] | None,
    tools_config: dict[str, Any] | None,
) -> list[Any] | None:
    """Translate CursorRules tool definitions into Gemini-compatible schemas."""
    tool_list: list[Any] | None = None

    if explicit_tools:
        tool_list = explicit_tools
    elif tools_config and tools_config.get("enabled", False):
        tool_list = tools_config.get("tools") or []

    if not tool_list:
        return None

    from agentrules.core.agent_tools.tool_manager import ToolManager  # Lazy import to avoid cycles

    return ToolManager.get_provider_tools(tool_list, ModelProvider.GEMINI)


def build_function_response_contents(
    request_contents: str | list[Any],
    model_content: dict[str, Any] | None,
    function_calls: Sequence[dict[str, Any]],
    tool_results: Sequence[dict[str, Any]],
    *,
    require_call_id: bool,
) -> list[Any]:
    """Append a Gemini model turn and matching tool responses without altering signed parts."""
    if model_content is None or len(function_calls) != len(tool_results):
        raise ValueError("Gemini tool turn is missing model content or matching tool results.")

    history: list[Any] = (
        [genai_types.Content(role="user", parts=[genai_types.Part(text=request_contents)])]
        if isinstance(request_contents, str)
        else list(request_contents)
    )
    response_parts: list[Any] = []
    for call, result in zip(function_calls, tool_results, strict=True):
        name = call.get("name")
        call_id = call.get("id")
        if not isinstance(name, str) or not name or result.get("name") != name:
            raise ValueError("Gemini tool result does not match its function call name.")
        if require_call_id and (not isinstance(call_id, str) or not call_id):
            raise ValueError(f"Gemini function call '{name}' is missing its required ID.")
        if result.get("call_id") != call_id:
            raise ValueError(f"Gemini tool result for '{name}' has a mismatched call ID.")

        raw_response = result.get("result")
        if isinstance(raw_response, str):
            try:
                response = json.loads(raw_response)
            except json.JSONDecodeError:
                response = {"text": raw_response}
        else:
            response = raw_response
        if not isinstance(response, dict):
            response = {"result": response}

        response_parts.append(
            genai_types.Part(
                function_response=genai_types.FunctionResponse(
                    id=call_id,
                    name=name,
                    response=response,
                )
            )
        )

    history.extend(
        (
            genai_types.Content.model_validate(model_content),
            genai_types.Content(role="user", parts=response_parts),
        )
    )
    return history

