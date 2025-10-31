import os
import unittest

os.environ.setdefault("OPENAI_API_KEY", "test")

from core.agents.base import ReasoningMode
from core.agents.openai import OpenAIArchitect


class OpenAIResponsesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.architect = OpenAIArchitect(
            model_name="gpt-5",
            reasoning=ReasoningMode.MINIMAL,
            text_verbosity="low"
        )

    def test_prepare_request_uses_responses_api(self) -> None:
        api_type, params = self.architect._prepare_request("Hello world")

        self.assertEqual(api_type, "responses")
        self.assertEqual(params["model"], "gpt-5")
        self.assertEqual(params.get("reasoning"), {"effort": "minimal"})
        self.assertEqual(params.get("text"), {"verbosity": "low"})

    def test_parse_responses_output_normalizes_tool_calls(self) -> None:
        payload = {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {"type": "output_text", "text": "Result body"},
                        {
                            "type": "function_call",
                            "id": "call_123",
                            "name": "summarize",
                            "arguments": '{"topic": "ai"}'
                        }
                    ]
                }
            ]
        }

        findings, tool_calls = self.architect._parse_responses_output(payload)

        self.assertEqual(findings, "Result body")
        self.assertIsNotNone(tool_calls)
        self.assertEqual(len(tool_calls or []), 1)
        self.assertEqual(tool_calls[0]["type"], "function")
        self.assertEqual(tool_calls[0]["function"]["name"], "summarize")
        self.assertEqual(tool_calls[0]["function"]["arguments"], '{"topic": "ai"}')


if __name__ == "__main__":
    unittest.main()
