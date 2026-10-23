import asyncio
import threading
import unittest
from collections.abc import Callable
from typing import Any, cast

from openai import OpenAI

from agentrules.core.agents.openai import OpenAIArchitect
from agentrules.core.agents.openai.client import set_client


class _OpenAIFakeResponsesAPI:
    def __init__(self):
        self.last_params = None
        self.create_override: Callable[..., dict[str, Any]] | None = None

    def create(self, **params):
        if self.create_override is not None:
            return self.create_override(**params)
        # Store params for assertion
        self.last_params = params
        # Return tool call if tools were supplied, else normal text
        if params.get("tools"):
            return {
                "output": [
                    {
                        "type": "function_call",
                        "id": "tool_1",
                        "name": "tavily_web_search",
                        "arguments": '{"query": "Flask", "max_results": 1}',
                    }
                ]
            }
        return {
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": "hello"}],
                }
            ]
        }


class _OpenAIFakeClient:
    def __init__(self):
        self.responses_api = _OpenAIFakeResponsesAPI()
        self.responses = self.responses_api


class OpenAIArchitectParsingTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.fake_client = _OpenAIFakeClient()
        set_client(cast(OpenAI, self.fake_client))
        self.addCleanup(lambda: set_client(None))

    async def test_reasoning_effort_param_for_o3(self):
        arch = OpenAIArchitect(model_name="o3")
        await arch.analyze({"foo": "bar"})
        p = self.fake_client.responses_api.last_params
        if p is None:
            self.fail("Expected parameters to be captured on the fake responses API")
        p = cast(dict[str, Any], p)
        # For o3 default reasoning HIGH -> responses reasoning payload included.
        self.assertEqual(p.get("model"), "o3")
        self.assertEqual(p.get("reasoning"), {"effort": "high"})

    async def test_tool_call_parsing(self):
        arch = OpenAIArchitect(model_name="o4-mini")
        # Tools enabled
        res = await arch.analyze({"context": "x"}, tools=[{"type": "function", "function": {"name": "tavily_web_search", "description": "", "parameters": {"type": "object", "properties": {}}}}])
        self.assertIn("tool_calls", res)
        self.assertIsNone(res.get("findings"))
        calls = res["tool_calls"]
        self.assertEqual(calls[0]["function"]["name"], "tavily_web_search")

    async def test_blocking_sdk_call_does_not_block_event_loop(self):
        started = threading.Event()
        release = threading.Event()

        def slow_create(**params):
            started.set()
            release.wait(timeout=1)
            return {"output": [{"type": "message", "content": [{"type": "output_text", "text": "ok"}]}]}

        self.fake_client.responses_api.create_override = slow_create
        timer = threading.Timer(0.3, release.set)
        timer.start()
        try:
            task = asyncio.create_task(OpenAIArchitect().analyze({"formatted_prompt": "hello"}))
            assert await asyncio.to_thread(started.wait, 1)
            await asyncio.sleep(0.01)
            self.assertFalse(task.done(), "SDK dispatch blocked the asyncio event loop")
            release.set()
            self.assertEqual((await task)["findings"], "ok")
        finally:
            release.set()
            timer.cancel()

    async def test_sdk_failure_surfaces_as_agent_error(self):
        def failing_create(**params):
            raise RuntimeError("provider unavailable")

        self.fake_client.responses_api.create_override = failing_create
        result = await OpenAIArchitect().analyze({"formatted_prompt": "hello"})
        self.assertEqual(result["error"], "provider unavailable")
