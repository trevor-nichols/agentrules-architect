"""Helper utilities for preparing DeepSeek tool configurations."""

from __future__ import annotations

from typing import Any

from agentrules.core.agent_tools.tool_manager import ToolManager
from agentrules.core.agents.base import ModelProvider


def resolve_tool_config(
    tools: list[Any] | None,
    tools_config: dict[str, Any] | None,
    *,
    allow_tools: bool,
) -> list[Any] | None:
    """
    Convert generic tool declarations into DeepSeek-compatible payloads.

    Legacy ``deepseek-reasoner`` does not support function calling. DeepSeek V4
    supports tools in both thinking and non-thinking modes, so callers should
    derive ``allow_tools`` from the model capability defaults.
    """
    if not allow_tools:
        return None

    config_enabled = tools_config and tools_config.get("enabled", False)
    if not tools and not config_enabled:
        return None

    tool_list = tools or (tools_config.get("tools") if tools_config else None)
    if not tool_list:
        return None

    return ToolManager.get_provider_tools(tool_list, ModelProvider.DEEPSEEK)
