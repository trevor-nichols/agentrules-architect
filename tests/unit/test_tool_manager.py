
from typing import Any

from google.genai import types as genai_types

from agentrules.core.agent_tools.tool_manager import ToolManager
from agentrules.core.agents.base import ModelProvider
from agentrules.core.types.tool_config import Tool


def _sample_tool() -> Tool:
    tool: Tool = {
        "type": "function",
        "function": {
            "name": "tavily_web_search",
            "description": "Search the web",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer"},
                },
                "required": ["query"],
            },
        },
    }
    return tool


def test_get_provider_tools_no_tools_returns_empty():
    assert ToolManager.get_provider_tools([], ModelProvider.OPENAI) == []
    assert ToolManager.get_provider_tools(None, ModelProvider.OPENAI) == []


def test_get_provider_tools_openai_identity():
    tools = [_sample_tool()]
    converted = ToolManager.get_provider_tools(tools, ModelProvider.OPENAI)
    # OpenAI Responses API expects top-level function metadata fields.
    assert converted == [
        {
            "type": "function",
            "name": "tavily_web_search",
            "description": "Search the web",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer"},
                },
                "required": ["query"],
            },
        }
    ]


def test_get_provider_tools_anthropic_conversion():
    tools = [_sample_tool()]
    converted = ToolManager.get_provider_tools(tools, ModelProvider.ANTHROPIC)
    assert isinstance(converted, list) and len(converted) == 1
    tool = converted[0]
    assert tool["name"] == "tavily_web_search"
    assert tool["description"] == "Search the web"
    assert "input_schema" in tool
    assert tool["input_schema"]["type"] == "object"
    assert "query" in tool["input_schema"]["properties"]
    assert "required" in tool["input_schema"] and tool["input_schema"]["required"] == ["query"]


def test_get_provider_tools_gemini_conversion():
    tools = [_sample_tool()]
    converted = ToolManager.get_provider_tools(tools, ModelProvider.GEMINI)
    assert isinstance(converted, list) and len(converted) == 1
    tool = converted[0]
    tool_cls: Any = getattr(genai_types, "Tool")  # noqa: B009 - dynamic import for stub-less SDK
    fn_decl_cls: Any = getattr(genai_types, "FunctionDeclaration")  # noqa: B009 - dynamic import for stub-less SDK
    assert isinstance(tool, tool_cls)
    function_decls = getattr(tool, "function_declarations")  # noqa: B009
    assert function_decls is not None
    assert len(function_decls) == 1
    fn_decl = function_decls[0]
    assert isinstance(fn_decl, fn_decl_cls)
    assert getattr(fn_decl, "name") == "tavily_web_search"  # noqa: B009
    params_schema = getattr(fn_decl, "parameters_json_schema")  # noqa: B009
    assert params_schema["type"] == "object"


def test_get_provider_tools_deepseek_returns_empty():
    tools = [_sample_tool()]
    converted = ToolManager.get_provider_tools(tools, ModelProvider.DEEPSEEK)
    # DeepSeek shares OpenAI schema, so the tool is passed through unchanged.
    assert converted == tools
