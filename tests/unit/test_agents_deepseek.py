import types
from typing import Any, cast

import pytest

from agentrules.core.agents.base import ReasoningMode
from agentrules.core.agents.deepseek import DeepSeekArchitect
from agentrules.core.agents.deepseek.tooling import DEEPSEEK_TOOL_HISTORY_KEY


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


@pytest.mark.asyncio
async def test_deepseek_chat_returns_findings():
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
    assert arch.model_name == "deepseek-flash"
    assert captured["model"] == "deepseek-flash"
    assert captured["extra_body"] == {"thinking": {"type": "disabled"}}


@pytest.mark.asyncio
async def test_deepseek_default_uses_current_flash_thinking_contract():
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
    assert arch.model_name == "deepseek-flash"
    assert captured["model"] == "deepseek-flash"
    assert captured["extra_body"] == {"thinking": {"type": "enabled"}}
    assert captured["reasoning_effort"] == "high"


@pytest.mark.asyncio
async def test_deepseek_v4_flash_direct_constructor_uses_current_wire_id():
    captured: dict[str, Any] = {}
    arch = DeepSeekArchitect(model_name="deepseek-v4-flash", reasoning=ReasoningMode.LOW)

    def create(**kwargs):
        captured.update(kwargs)
        return _FakeResponse(_FakeMessage(content="hi"))

    arch.client = cast(
        Any,
        types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=create))),
    )
    result = await arch.analyze({"formatted_prompt": "x"})

    assert result["findings"] == "hi"
    assert captured["model"] == "deepseek-flash"
    assert captured["reasoning_effort"] == "low"
    assert captured["max_tokens"] == 32_000


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
async def test_deepseek_reasoner_includes_reasoning():
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
    assert res["findings"] in (None, "")
    assert arch.model_name == "deepseek-flash"
    assert captured["model"] == "deepseek-flash"
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
    assert DEEPSEEK_TOOL_HISTORY_KEY not in res


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("wire_calls", "reasoning", "error"),
    [
        ((("", "lookup", "{}"),), "Plan before using the tool.", "DeepSeek tool call is missing its ID"),
        ((("same", "lookup", "{}"),) * 2, "Plan to use tools.", "DeepSeek tool turn has duplicate call IDs"),
        ((("call-1", "lookup", "{}"),), None, "DeepSeek thinking tool turn is missing reasoning_content"),
        (
            (("call-1", "lookup", "{}"), ("call-2", "", "{}")),
            "Plan to use tools.",
            "DeepSeek tool call is missing its function name",
        ),
        (
            (("call-1", "lookup", "{}"), ("call-2", "lookup", None)),
            "Plan to use tools.",
            "DeepSeek tool call arguments must be a string",
        ),
    ],
)
async def test_deepseek_rejects_invalid_native_tool_turns(
    wire_calls: tuple[tuple[str, str, str | None], ...], reasoning: str | None, error: str,
) -> None:
    architect = DeepSeekArchitect(model_name="deepseek-flash", reasoning=ReasoningMode.HIGH)
    calls = [
        {"id": call_id, "type": "function", "function": {"name": name, "arguments": arguments}}
        for call_id, name, arguments in wire_calls
    ]
    message = _FakeMessage(content=None, reasoning_content=reasoning, tool_calls=calls)
    architect.client = types.SimpleNamespace(
        chat=types.SimpleNamespace(
            completions=types.SimpleNamespace(create=lambda **_: _FakeResponse(message)),
        ),
    )

    result = await architect.analyze(
        {"formatted_prompt": "Check dependency versions.", DEEPSEEK_TOOL_HISTORY_KEY: []},
        tools=[{"type": "function", "function": {"name": "lookup", "parameters": {"type": "object"}}}],
    )

    assert result["error"] == error
    assert "tool_calls" not in result
    assert DEEPSEEK_TOOL_HISTORY_KEY not in result
