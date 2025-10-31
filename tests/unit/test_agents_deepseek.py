import types

from core.agents.deepseek import DeepSeekArchitect


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
        class Chat:
            class Comps:
                def create(self, **kwargs):  # accepts params
                    return _FakeResponse(_FakeMessage(content="hi"))

            def __init__(self):
                self.completions = _FakeDeepseekClient.Chat.Comps()

        self.chat = Chat()


import pytest


@pytest.mark.asyncio
async def test_deepseek_chat_returns_findings(monkeypatch):
    arch = DeepSeekArchitect(model_name="deepseek-chat")
    arch.client = _FakeDeepseekClient()
    res = await arch.analyze({"formatted_prompt": "x"})
    assert res["findings"] == "hi"
    assert res["tool_calls"] is None


@pytest.mark.asyncio
async def test_deepseek_reasoner_includes_reasoning(monkeypatch):
    arch = DeepSeekArchitect(model_name="deepseek-reasoner")

    class Client(_FakeDeepseekClient):
        def __init__(self):
            class Chat:
                class Comps:
                    def create(self, **kwargs):
                        msg = _FakeMessage(content=None, reasoning_content="think", tool_calls=[])
                        return _FakeResponse(msg)

                def __init__(self):
                    self.completions = Chat.Comps()

            self.chat = Chat()

    arch.client = Client()
    res = await arch.analyze({"formatted_prompt": "x"})
    assert res["reasoning"] == "think"
    assert res["findings"] is None or res["findings"] == None or res["findings"] == ""


@pytest.mark.asyncio
async def test_deepseek_tool_calls_clear_findings(monkeypatch):
    arch = DeepSeekArchitect(model_name="deepseek-chat")

    class Client(_FakeDeepseekClient):
        def __init__(self):
            class Chat:
                class Comps:
                    def create(self, **kwargs):
                        msg = _FakeMessage(
                            content=None,
                            tool_calls=[_FakeToolCall("id1", "t", "{}")],
                        )
                        return _FakeResponse(msg)

                def __init__(self):
                    self.completions = Chat.Comps()

            self.chat = Chat()

    arch.client = Client()
    res = await arch.analyze({"formatted_prompt": "x"})
    assert isinstance(res["tool_calls"], list) and res["tool_calls"][0]["function"]["name"] == "t"
    assert res["findings"] is None
