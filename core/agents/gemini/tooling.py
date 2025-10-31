"""Tool configuration helpers for Gemini."""

from __future__ import annotations

from typing import Any

from core.agents.base import ModelProvider


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

    from core.agent_tools.tool_manager import ToolManager  # Lazy import to avoid cycles

    return ToolManager.get_provider_tools(tool_list, ModelProvider.GEMINI)

