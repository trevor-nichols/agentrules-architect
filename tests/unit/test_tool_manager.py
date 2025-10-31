import pytest

from core.agent_tools.tool_manager import ToolManager
from core.agents.base import ModelProvider


def _sample_tool():
    return {
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


def test_get_provider_tools_no_tools_returns_empty():
    assert ToolManager.get_provider_tools([], ModelProvider.OPENAI) == []
    assert ToolManager.get_provider_tools(None, ModelProvider.OPENAI) == []


def test_get_provider_tools_openai_identity():
    tools = [_sample_tool()]
    converted = ToolManager.get_provider_tools(tools, ModelProvider.OPENAI)
    # OpenAI path keeps the same schema
    assert converted == tools


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
    assert "function_declarations" in tool
    fns = tool["function_declarations"]
    assert isinstance(fns, list) and len(fns) == 1
    fn = fns[0]
    assert fn["name"] == "tavily_web_search"
    assert fn["parameters"]["type"] == "object"


def test_get_provider_tools_deepseek_returns_empty():
    tools = [_sample_tool()]
    converted = ToolManager.get_provider_tools(tools, ModelProvider.DEEPSEEK)
    # DeepSeek path returns empty (no tool support in manager)
    assert converted == []

