from core.agents.openai import OpenAIArchitect
from core.agents.base import ReasoningMode


def test_openai_params_reasoning_effort_for_o3():
    arch = OpenAIArchitect(model_name="o3", reasoning=ReasoningMode.HIGH)
    params = arch._get_model_parameters("hello")
    assert params["model"] == "o3"
    assert params["reasoning_effort"] == "high"


def test_openai_params_temperature_for_gpt41():
    arch = OpenAIArchitect(model_name="gpt-4.1", reasoning=ReasoningMode.TEMPERATURE, temperature=0.42)
    params = arch._get_model_parameters("hello")
    assert params["model"] == "gpt-4.1"
    assert params["temperature"] == 0.42


def test_openai_params_adds_tools_when_provided():
    arch = OpenAIArchitect(model_name="o4-mini", reasoning=ReasoningMode.MEDIUM)
    tools = [{"type": "function", "function": {"name": "t", "parameters": {"type": "object", "properties": {}}}}]
    params = arch._get_model_parameters("hello", tools=tools)
    assert params["tools"] == tools
    assert params["tool_choice"] == "auto"

