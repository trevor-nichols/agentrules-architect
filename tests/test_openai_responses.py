import os
import unittest

os.environ.setdefault("OPENAI_API_KEY", "test")

from agentrules.core.agents.base import ReasoningMode
from agentrules.core.agents.openai import OpenAIArchitect
from agentrules.core.agents.openai.response_parser import parse_response


class OpenAIResponsesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.architect = OpenAIArchitect(
            model_name="gpt-5",
            reasoning=ReasoningMode.MINIMAL,
            text_verbosity="low"
        )

    def test_prepare_request_uses_responses_api(self) -> None:
        prepared = self.architect._prepare_request("Hello world")
        params = prepared.payload

        self.assertEqual(prepared.api, "responses")
        self.assertEqual(params["model"], "gpt-5")
        self.assertIn("instructions", params)
        self.assertEqual(params.get("reasoning"), {"effort": "minimal"})
        self.assertEqual(params.get("text"), {"verbosity": "low"})

    def test_prepare_request_uses_responses_api_for_gpt51(self) -> None:
        architect = OpenAIArchitect(
            model_name="gpt-5.1",
            reasoning=ReasoningMode.MEDIUM,
            text_verbosity="medium"
        )
        prepared = architect._prepare_request("Hola")
        params = prepared.payload

        self.assertEqual(prepared.api, "responses")
        self.assertEqual(params["model"], "gpt-5.1")
        self.assertEqual(params.get("reasoning"), {"effort": "medium"})
        self.assertEqual(params.get("text"), {"verbosity": "medium"})

    def test_prepare_request_uses_responses_api_for_gpt52(self) -> None:
        architect = OpenAIArchitect(
            model_name="gpt-5.2",
            reasoning=ReasoningMode.HIGH,
            text_verbosity="high"
        )
        prepared = architect._prepare_request("Bonjour")
        params = prepared.payload

        self.assertEqual(prepared.api, "responses")
        self.assertEqual(params["model"], "gpt-5.2")
        self.assertEqual(params.get("reasoning"), {"effort": "high"})
        self.assertEqual(params.get("text"), {"verbosity": "high"})

    def test_prepare_request_uses_responses_api_for_gpt52_codex(self) -> None:
        architect = OpenAIArchitect(
            model_name="gpt-5.2-codex",
            reasoning=ReasoningMode.MEDIUM,
            text_verbosity="medium"
        )
        prepared = architect._prepare_request("Salut")
        params = prepared.payload

        self.assertEqual(prepared.api, "responses")
        self.assertEqual(params["model"], "gpt-5.2-codex")
        self.assertEqual(params.get("reasoning"), {"effort": "medium"})
        self.assertEqual(params.get("text"), {"verbosity": "medium"})

    def test_prepare_request_uses_responses_api_for_gpt55(self) -> None:
        architect = OpenAIArchitect(
            model_name="gpt-5.5",
            reasoning=ReasoningMode.XHIGH,
            text_verbosity="high"
        )
        prepared = architect._prepare_request("Hej")
        params = prepared.payload

        self.assertEqual(prepared.api, "responses")
        self.assertEqual(params["model"], "gpt-5.5")
        self.assertEqual(params.get("reasoning"), {"effort": "xhigh"})
        self.assertEqual(params.get("text"), {"verbosity": "high"})

    def test_prepare_request_uses_responses_api_for_gpt54_snapshot(self) -> None:
        architect = OpenAIArchitect(
            model_name="gpt-5.4-2026-03-05",
            reasoning=ReasoningMode.MEDIUM,
            text_verbosity="medium"
        )
        prepared = architect._prepare_request("Ciao")
        params = prepared.payload

        self.assertEqual(prepared.api, "responses")
        self.assertEqual(params["model"], "gpt-5.4-2026-03-05")
        self.assertEqual(params.get("reasoning"), {"effort": "medium"})
        self.assertEqual(params.get("text"), {"verbosity": "medium"})

    def test_prepare_request_uses_responses_api_for_gpt54_mini(self) -> None:
        architect = OpenAIArchitect(
            model_name="gpt-5.4-mini",
            reasoning=ReasoningMode.DISABLED,
            text_verbosity="low"
        )
        prepared = architect._prepare_request("Ciao mini")
        params = prepared.payload

        self.assertEqual(prepared.api, "responses")
        self.assertEqual(params["model"], "gpt-5.4-mini")
        self.assertEqual(params.get("reasoning"), {"effort": "none"})
        self.assertEqual(params.get("text"), {"verbosity": "low"})

    def test_prepare_request_uses_responses_api_for_gpt54_nano(self) -> None:
        architect = OpenAIArchitect(
            model_name="gpt-5.4-nano",
            reasoning=ReasoningMode.XHIGH,
            text_verbosity="high"
        )
        prepared = architect._prepare_request("Ciao nano")
        params = prepared.payload

        self.assertEqual(prepared.api, "responses")
        self.assertEqual(params["model"], "gpt-5.4-nano")
        self.assertEqual(params.get("reasoning"), {"effort": "xhigh"})
        self.assertEqual(params.get("text"), {"verbosity": "high"})

    def test_parse_responses_output_normalizes_tool_calls(self) -> None:
        payload = {
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": "Result body"}],
                },
                {
                    "type": "function_call",
                    "id": "call_123",
                    "name": "summarize",
                    "arguments": '{"topic": "ai"}'
                },
            ]
        }

        parsed = parse_response(payload, "responses")

        self.assertEqual(parsed.findings, "Result body")
        tool_calls = parsed.tool_calls or []
        self.assertEqual(len(tool_calls), 1)
        call = tool_calls[0]
        self.assertEqual(call["type"], "function")
        self.assertEqual(call["function"]["name"], "summarize")
        self.assertEqual(call["function"]["arguments"], '{"topic": "ai"}')


if __name__ == "__main__":
    unittest.main()
