import unittest
from types import SimpleNamespace

from agentrules.core.agents.anthropic import AnthropicArchitect
from agentrules.core.agents.anthropic import client as anthropic_client
from agentrules.core.agents.anthropic.response_parser import (
    AnthropicRefusalError,
    parse_response,
)
from agentrules.core.agents.base import ReasoningMode
from tests.fakes.vendor_responses import AnthropicMessageCreateResponseFake, _AnthropicToolUseBlock


class _AnthropicFakeMessagesAPI:
    def __init__(self):
        self.last_params = None

    def create(self, **params):
        self.last_params = params
        # Return a text block and a tool_use block
        tool_block = _AnthropicToolUseBlock("call_1", "web_search", {"query": "Flask docs"})
        return AnthropicMessageCreateResponseFake(text="analysis", tool_call=tool_block)


class _AnthropicFakeClient:
    def __init__(self):
        self.messages = _AnthropicFakeMessagesAPI()


class AnthropicArchitectParsingTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.fake_client = _AnthropicFakeClient()
        anthropic_client.set_client(self.fake_client)

    async def asyncTearDown(self):  # noqa: D401 - cleanup helper
        anthropic_client.set_client(None)

    async def test_parses_text_and_tool_use(self):
        arch = AnthropicArchitect()
        res = await arch.analyze({"ctx": 1}, tools=[{"type": "function", "function": {"name": "web_search", "description": "", "parameters": {"type": "object", "properties": {}}}}])
        self.assertEqual(res.get("findings"), "analysis")
        self.assertIsNotNone(res.get("tool_calls"))
        tc = res["tool_calls"][0]
        self.assertEqual(tc["name"], "web_search")

    def test_parse_response_rejects_dict_refusal_with_safe_details(self):
        with self.assertRaises(AnthropicRefusalError) as raised:
            parse_response(
                {
                    "content": [],
                    "stop_reason": "refusal",
                    "stop_details": {
                        "category": "cyber",
                        "explanation": "This request was declined because it could enable cyber harm.",
                    },
                }
            )

        self.assertEqual(raised.exception.category, "cyber")
        self.assertIn("could enable cyber harm", str(raised.exception))

    def test_parse_response_rejects_object_refusal_without_details(self):
        response = SimpleNamespace(content=[], stop_reason="refusal", stop_details=None)

        with self.assertRaisesRegex(AnthropicRefusalError, "Anthropic refused the request"):
            parse_response(response)

    async def test_architect_surfaces_refusal_as_error_result(self):
        class RefusalMessages:
            def create(self, **_params):  # type: ignore[no-untyped-def]
                return {
                    "content": [],
                    "stop_reason": "refusal",
                    "stop_details": {
                        "category": "cyber",
                        "explanation": "Request declined.",
                    },
                }

        class RefusalClient:
            messages = RefusalMessages()

        anthropic_client.set_client(RefusalClient())
        arch = AnthropicArchitect(model_name="claude-fable-5", reasoning=ReasoningMode.DYNAMIC)

        result = await arch.analyze({"formatted_prompt": "hello"})

        self.assertIn("Anthropic refused the request", result["error"])
        self.assertNotIn("findings", result)

    async def test_fable_disabled_thinking_fails_before_client_dispatch(self):
        arch = AnthropicArchitect(model_name="claude-fable-5", reasoning=ReasoningMode.DISABLED)

        result = await arch.analyze({"formatted_prompt": "hello"})

        self.assertIn("always uses adaptive thinking", result["error"])
        self.assertIsNone(self.fake_client.messages.last_params)
