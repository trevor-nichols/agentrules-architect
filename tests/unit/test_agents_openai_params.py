from agentrules.core.agents.base import ReasoningMode
from agentrules.core.agents.openai import OpenAIArchitect


def test_openai_params_reasoning_effort_for_o3():
    arch = OpenAIArchitect(model_name="o3", reasoning=ReasoningMode.HIGH)
    prepared = arch._prepare_request("hello")
    params = prepared.payload
    assert prepared.api == "responses"
    assert params["model"] == "o3"
    assert params["reasoning"] == {"effort": "high"}


def test_openai_params_temperature_for_gpt41():
    arch = OpenAIArchitect(model_name="gpt-4.1", reasoning=ReasoningMode.TEMPERATURE, temperature=0.42)
    prepared = arch._prepare_request("hello")
    params = prepared.payload
    assert params["model"] == "gpt-4.1"
    assert params["temperature"] == 0.42


def test_openai_params_adds_tools_when_provided():
    arch = OpenAIArchitect(model_name="o4-mini", reasoning=ReasoningMode.MEDIUM)
    tools = [{"type": "function", "function": {"name": "t", "parameters": {"type": "object", "properties": {}}}}]
    prepared = arch._prepare_request("hello", tools=tools)
    params = prepared.payload
    assert params["tools"] == [
        {
            "type": "function",
            "name": "t",
            "description": "",
            "parameters": {"type": "object", "properties": {}},
        }
    ]
    assert params["tool_choice"] == "auto"
