"""
core/agent_tools/tool_manager.py

Central manager for tool definitions and provider-specific conversions.
"""

from typing import Any, Optional, Sequence

from core.agents.base import ModelProvider
from core.types.tool_config import Tool


class ToolManager:
    """
    Manages tool definitions and conversions between different model providers.
    """

    @staticmethod
    def get_provider_tools(
        tools: Optional[Sequence[Tool]],
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
            # OpenAI's format is very similar to our standard format
            return list(normalized)

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
            # Convert to Google GenAI SDK Tool format (google-genai)
            # The new SDK accepts pydantic types or plain dicts via config parsing.
            # We return list of dict tools using function_declarations with JSON schema parameters.
            converted = []
            for tool in normalized:
                fn = tool.get("function", {})
                converted.append({
                    "function_declarations": [
                        {
                            "name": fn.get("name"),
                            "description": fn.get("description", ""),
                            # Pass JSON Schema directly; SDK will parse into types.Schema
                            "parameters": fn.get("parameters", {"type": "object", "properties": {}}),
                        }
                    ]
                })
            return converted

        elif provider == ModelProvider.DEEPSEEK:
            # DeepSeek shares OpenAI's tool schema.
            return list(normalized)

        return []

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
