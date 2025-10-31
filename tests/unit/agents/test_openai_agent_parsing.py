import asyncio
import json
import unittest

from core.agents.openai import OpenAIArchitect
from tests.fakes.vendor_responses import OpenAIChatCompletionFake, _ToolCallFake


class _OpenAIFakeChatAPI:
    def __init__(self):
        self.last_params = None

    def create(self, **params):
        # Store params for assertion
        self.last_params = params
        # Return tool call if tools were supplied, else normal text
        if params.get("tools"):
            tc = _ToolCallFake("tool_1", "tavily_web_search", '{"query": "Flask", "max_results": 1}')
            return OpenAIChatCompletionFake(content=None, tool_calls=[tc])
        return OpenAIChatCompletionFake(content="hello")


class _OpenAIFakeClient:
    def __init__(self):
        # Keep a direct handle to completions for assertions
        self.completions_api = _OpenAIFakeChatAPI()
        self.chat = type("C", (), {"completions": self.completions_api})()


class OpenAIArchitectParsingTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Monkeypatch module-level client with our fake
        import core.agents.openai as openai_mod
        self.fake_client = _OpenAIFakeClient()
        openai_mod.openai_client = self.fake_client  # type: ignore

    async def test_reasoning_effort_param_for_o3(self):
        arch = OpenAIArchitect(model_name="o3")
        await arch.analyze({"foo": "bar"})
        p = self.fake_client.completions_api.last_params
        self.assertIsNotNone(p)
        # For o3 default reasoning HIGH -> reasoning_effort included
        self.assertEqual(p.get("model"), "o3")
        self.assertEqual(p.get("reasoning_effort"), "high")

    async def test_tool_call_parsing(self):
        arch = OpenAIArchitect(model_name="o4-mini")
        # Tools enabled
        res = await arch.analyze({"context": "x"}, tools=[{"type": "function", "function": {"name": "tavily_web_search", "description": "", "parameters": {"type": "object", "properties": {}}}}])
        self.assertIn("tool_calls", res)
        self.assertIsNone(res.get("findings"))
        calls = res["tool_calls"]
        self.assertEqual(calls[0]["function"]["name"], "tavily_web_search")
