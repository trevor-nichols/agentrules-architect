import unittest

from core.agents.deepseek import DeepSeekArchitect
from tests.fakes.vendor_responses import DeepSeekChatCompletionFake, _ToolCallFake


class _DeepSeekFakeChatAPI:
    def __init__(self):
        self.last_params = None

    def create(self, **params):
        self.last_params = params
        # Return reasoning content for reasoner, and a tool call for chat
        model = params.get("model")
        if model == "deepseek-reasoner":
            return DeepSeekChatCompletionFake(content="final", reasoning="chain of thought")
        tc = _ToolCallFake("call1", "tavily_web_search", '{"query":"flask"}')
        return DeepSeekChatCompletionFake(content=None, tool_calls=[tc])


class _DeepSeekFakeClient:
    def __init__(self):
        self.chat = type("C", (), {"completions": _DeepSeekFakeChatAPI()})()


class DeepSeekArchitectParsingTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        import core.agents.deepseek as ds_mod
        self.ds_mod = ds_mod
        self.fake_client = _DeepSeekFakeClient()

    async def test_reasoner_includes_reasoning_content(self):
        arch = DeepSeekArchitect(model_name="deepseek-reasoner")
        # Inject fake client
        arch.client = self.fake_client  # type: ignore
        res = await arch.analyze({"ctx": 1})
        self.assertEqual(res.get("findings"), "final")
        self.assertEqual(res.get("reasoning"), "chain of thought")

    async def test_chat_tool_call(self):
        arch = DeepSeekArchitect(model_name="deepseek-chat")
        arch.client = self.fake_client  # type: ignore
        res = await arch.analyze({"ctx": 1}, tools=[{"type": "function", "function": {"name": "tavily_web_search", "description": "", "parameters": {"type": "object", "properties": {}}}}])
        self.assertIsNone(res.get("findings"))
        self.assertIn("tool_calls", res)
        self.assertEqual(res["tool_calls"][0]["function"]["name"], "tavily_web_search")

