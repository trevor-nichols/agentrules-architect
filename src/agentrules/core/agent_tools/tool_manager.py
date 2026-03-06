"""
core/agent_tools/tool_manager.py

Central manager for tool definitions and provider-specific conversions.
"""

from collections.abc import Mapping, Sequence
from typing import Any, cast

from agentrules.core.agents.base import ModelProvider
from agentrules.core.types.tool_config import Tool


class ToolManager:
    """
    Manages tool definitions and conversions between different model providers.
    """

    @staticmethod
    def get_provider_tools(
        tools: Sequence[Tool] | None,
        provider: ModelProvider
    ) -> list[Any]:
        """
        Convert the standard tool format to provider-specific format.

        Args:
            tools: List of tools in standard format
            provider: The model provider to convert tools for

        Returns:
            List of tools in provider-specific format
        """
        if not tools:
            return []

        normalized = list(tools)

        if provider == ModelProvider.OPENAI:
            # OpenAI Responses API expects function tools to expose top-level
            # `name`/`description`/`parameters` fields.
            converted: list[dict[str, Any]] = []
            for tool in normalized:
                converted_tool = ToolManager._to_openai_responses_tool(tool)
                if converted_tool:
                    converted.append(converted_tool)
            return converted

        elif provider == ModelProvider.ANTHROPIC:
            # Convert to Anthropic's tools format
            return [
                {
                    "name": tool["function"]["name"],
                    "description": tool["function"]["description"],
                    "input_schema": {
                        "type": "object",
                        "properties": tool["function"]["parameters"]["properties"],
                        "required": tool["function"]["parameters"].get("required", [])
                    }
                }
                for tool in normalized
            ]

        elif provider == ModelProvider.GEMINI:
            # Convert to Google GenAI SDK Tool objects.
            try:
                from google.genai import types as genai_types  # type: ignore
            except Exception:  # pragma: no cover - fallback when SDK unavailable
                converted = []
                for tool in normalized:
                    fn = tool.get("function", {})
                    converted.append(
                        {
                            "function_declarations": [
                                {
                                    "name": fn.get("name"),
                                    "description": fn.get("description", ""),
                                    "parameters": fn.get("parameters", {"type": "object", "properties": {}}),
                                }
                            ]
                        }
                    )
                return converted

            function_declaration_cls = cast(
                Any, getattr(genai_types, "FunctionDeclaration", None)
            )
            tool_cls = cast(Any, getattr(genai_types, "Tool", None))
            if function_declaration_cls is None or tool_cls is None:
                # Fallback to plain dicts if the SDK structure is unavailable (unlikely).
                converted = []
                for tool in normalized:
                    fn = tool.get("function", {})
                    converted.append(
                        {
                            "function_declarations": [
                                {
                                    "name": fn.get("name"),
                                    "description": fn.get("description", ""),
                                    "parameters": fn.get("parameters", {"type": "object", "properties": {}}),
                                }
                            ]
                        }
                    )
                return converted

            converted = []
            for tool in normalized:
                fn = tool.get("function", {})
                fn_decl = function_declaration_cls(
                    name=fn.get("name"),
                    description=fn.get("description", ""),
                    parameters_json_schema=fn.get("parameters", {"type": "object", "properties": {}}),
                )
                converted.append(tool_cls(function_declarations=[fn_decl]))
            return converted

        elif provider in {ModelProvider.DEEPSEEK, ModelProvider.XAI}:
            # DeepSeek shares OpenAI's tool schema.
            return list(normalized)

        return []

    @staticmethod
    def _to_openai_responses_tool(tool: Tool) -> dict[str, Any] | None:
        """
        Convert an internal `Tool` entry to OpenAI Responses function-tool shape.

        Accepts either the legacy Chat Completions shape:
        {"type":"function","function":{"name":...,"parameters":...}}
        or an already-converted Responses shape.
        """
        if not isinstance(tool, Mapping):
            return None

        tool_type = tool.get("type")
        if tool_type != "function":
            return None

        # Already in Responses shape (top-level name/parameters)
        if isinstance(tool.get("name"), str):
            normalized: dict[str, Any] = {
                "type": "function",
                "name": tool.get("name"),
                "description": tool.get("description", ""),
                "parameters": tool.get("parameters", {"type": "object", "properties": {}}),
            }
            if "strict" in tool:
                normalized["strict"] = tool.get("strict")
            return normalized

        function_payload = tool.get("function")
        if not isinstance(function_payload, Mapping):
            return None

        name = function_payload.get("name")
        if not isinstance(name, str) or not name.strip():
            return None

        converted: dict[str, Any] = {
            "type": "function",
            "name": name,
            "description": function_payload.get("description", ""),
            "parameters": function_payload.get("parameters", {"type": "object", "properties": {}}),
        }
        if "strict" in function_payload:
            converted["strict"] = function_payload.get("strict")
        return converted

    @staticmethod
    def get_tools_for_phase(phase: str, tools_config: dict) -> list[Tool]:
        """
        Get the tools for a specific phase.

        Args:
            phase: The phase to get tools for (e.g., "phase1", "phase5")
            tools_config: Dictionary containing tool configurations

        Returns:
            List of tools for the specified phase
        """
        phase_key = f"{phase.upper()}_TOOLS"
        tools = tools_config.get(phase_key, [])
        return list(tools) if tools else []
