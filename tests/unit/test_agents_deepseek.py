import types
from typing import Any, cast

from agentrules.core.agents.deepseek import DeepSeekArchitect


class _FakeMessage:
    def __init__(self, content=None, reasoning_content=None, tool_calls=None):
        self.content = content
        self.reasoning_content = reasoning_content
        self.tool_calls = tool_calls or []


class _FakeToolCall:
    def __init__(self, id, name, arguments):
        self.id = id
        self.type = "function"
        self.function = types.SimpleNamespace(name=name, arguments=arguments)


class _FakeResponse:
    def __init__(self, message):
        self.choices = [types.SimpleNamespace(message=message)]


class _FakeDeepseekClient:
    def __init__(self):
        def create(**kwargs):
            return _FakeResponse(_FakeMessage(content="hi"))

        completions = types.SimpleNamespace(create=create)
        self.chat = types.SimpleNamespace(completions=completions)


import pytest


@pytest.mark.asyncio
async def test_deepseek_chat_returns_findings(monkeypatch):
    captured: dict[str, Any] = {}
    arch = DeepSeekArchitect(model_name="deepseek-chat")

    class Client(_FakeDeepseekClient):
        def __init__(self):
            def create(**kwargs):
                captured.update(kwargs)
                return _FakeResponse(_FakeMessage(content="hi"))

            completions = types.SimpleNamespace(create=create)
            self.chat = types.SimpleNamespace(completions=completions)

    arch.client = cast(Any, Client())
    res = await arch.analyze({"formatted_prompt": "x"})
    assert res["findings"] == "hi"
    assert res["tool_calls"] is None
    assert arch.model_name == "deepseek-v4-flash"
    assert captured["model"] == "deepseek-v4-flash"
    assert captured["extra_body"] == {"thinking": {"type": "disabled"}}


@pytest.mark.asyncio
async def test_deepseek_default_uses_v4_flash_thinking_contract():
    captured: dict[str, Any] = {}
    arch = DeepSeekArchitect()

    class Client(_FakeDeepseekClient):
        def __init__(self):
            def create(**kwargs):
                captured.update(kwargs)
                return _FakeResponse(_FakeMessage(content="hi"))

            completions = types.SimpleNamespace(create=create)
            self.chat = types.SimpleNamespace(completions=completions)

    arch.client = cast(Any, Client())
    res = await arch.analyze({"formatted_prompt": "x"})

    assert res["findings"] == "hi"
    assert arch.model_name == "deepseek-v4-flash"
    assert captured["extra_body"] == {"thinking": {"type": "enabled"}}
    assert captured["reasoning_effort"] == "high"


@pytest.mark.asyncio
async def test_deepseek_v4_thinking_keeps_tools_enabled():
    captured: dict[str, Any] = {}
    arch = DeepSeekArchitect(model_name="deepseek-v4-pro", reasoning=None)

    class Client(_FakeDeepseekClient):
        def __init__(self):
            def create(**kwargs):
                captured.update(kwargs)
                return _FakeResponse(_FakeMessage(content="hi"))

            completions = types.SimpleNamespace(create=create)
            self.chat = types.SimpleNamespace(completions=completions)

    arch.client = cast(Any, Client())
    await arch.analyze(
        {"formatted_prompt": "x"},
        tools=[
            {
                "type": "function",
                "function": {"name": "lookup", "description": "", "parameters": {"type": "object"}},
            }
        ],
    )

    assert captured["extra_body"] == {"thinking": {"type": "enabled"}}
    assert captured["tool_choice"] == "auto"
    assert captured["tools"][0]["function"]["name"] == "lookup"


@pytest.mark.asyncio
async def test_deepseek_reasoner_includes_reasoning(monkeypatch):
    captured: dict[str, Any] = {}
    arch = DeepSeekArchitect(model_name="deepseek-reasoner")

    class Client(_FakeDeepseekClient):
        def __init__(self):
            def create(**kwargs):
                captured.update(kwargs)
                msg = _FakeMessage(content=None, reasoning_content="think", tool_calls=[])
                return _FakeResponse(msg)

            completions = types.SimpleNamespace(create=create)
            self.chat = types.SimpleNamespace(completions=completions)

    arch.client = cast(Any, Client())
    res = await arch.analyze({"formatted_prompt": "x"})
    assert res["reasoning"] == "think"
    assert res["findings"] is None or res["findings"] is None or res["findings"] == ""
    assert arch.model_name == "deepseek-v4-flash"
    assert captured["model"] == "deepseek-v4-flash"
    assert captured["extra_body"] == {"thinking": {"type": "enabled"}}
    assert captured["reasoning_effort"] == "high"


@pytest.mark.asyncio
async def test_deepseek_tool_calls_clear_findings(monkeypatch):
    arch = DeepSeekArchitect(model_name="deepseek-chat")

    class Client(_FakeDeepseekClient):
        def __init__(self):
            def create(**kwargs):
                msg = _FakeMessage(
                    content=None,
                    tool_calls=[_FakeToolCall("id1", "t", "{}")],
                )
                return _FakeResponse(msg)

            completions = types.SimpleNamespace(create=create)
            self.chat = types.SimpleNamespace(completions=completions)

    arch.client = cast(Any, Client())
    res = await arch.analyze({"formatted_prompt": "x"})
    assert isinstance(res["tool_calls"], list) and res["tool_calls"][0]["function"]["name"] == "t"
    assert res["findings"] is None
