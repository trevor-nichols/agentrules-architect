from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Any

from agentrules.core.agents.base import ReasoningMode
from agentrules.core.agents.openai.config import resolve_model_defaults
from agentrules.core.agents.openai.request_builder import prepare_request
from agentrules.core.agents.openai.response_parser import parse_response


class OpenAIConfigTests(unittest.TestCase):
    def test_resolve_defaults_for_gpt5_prefix(self) -> None:
        defaults = resolve_model_defaults("gpt-5-large")
        self.assertEqual(defaults.default_reasoning, ReasoningMode.MEDIUM)
        self.assertTrue(defaults.use_responses_api)
        self.assertIsNone(defaults.default_temperature)

    def test_resolve_defaults_for_gpt55_prefix(self) -> None:
        defaults = resolve_model_defaults("gpt-5.5")
        self.assertEqual(defaults.default_reasoning, ReasoningMode.MEDIUM)
        self.assertTrue(defaults.use_responses_api)
        self.assertIsNone(defaults.default_temperature)

    def test_resolve_defaults_for_gpt51_prefix(self) -> None:
        defaults = resolve_model_defaults("gpt-5.1-large")
        self.assertEqual(defaults.default_reasoning, ReasoningMode.DISABLED)
        self.assertTrue(defaults.use_responses_api)
        self.assertIsNone(defaults.default_temperature)

    def test_resolve_defaults_for_gpt52_prefix(self) -> None:
        defaults = resolve_model_defaults("gpt-5.2-large")
        self.assertEqual(defaults.default_reasoning, ReasoningMode.DISABLED)
        self.assertTrue(defaults.use_responses_api)
        self.assertIsNone(defaults.default_temperature)

    def test_resolve_defaults_for_gpt53_codex_prefix(self) -> None:
        defaults = resolve_model_defaults("gpt-5.3-codex")
        self.assertEqual(defaults.default_reasoning, ReasoningMode.MEDIUM)
        self.assertTrue(defaults.use_responses_api)
        self.assertIsNone(defaults.default_temperature)

    def test_resolve_defaults_for_gpt54_snapshot(self) -> None:
        defaults = resolve_model_defaults("gpt-5.4-2026-03-05")
        self.assertEqual(defaults.default_reasoning, ReasoningMode.DISABLED)
        self.assertTrue(defaults.use_responses_api)
        self.assertIsNone(defaults.default_temperature)

    def test_resolve_defaults_for_gpt54_pro(self) -> None:
        defaults = resolve_model_defaults("gpt-5.4-pro")
        self.assertEqual(defaults.default_reasoning, ReasoningMode.MEDIUM)
        self.assertTrue(defaults.use_responses_api)
        self.assertIsNone(defaults.default_temperature)

    def test_resolve_defaults_for_gpt54_mini(self) -> None:
        defaults = resolve_model_defaults("gpt-5.4-mini")
        self.assertEqual(defaults.default_reasoning, ReasoningMode.DISABLED)
        self.assertTrue(defaults.use_responses_api)
        self.assertIsNone(defaults.default_temperature)

    def test_resolve_defaults_for_gpt54_nano(self) -> None:
        defaults = resolve_model_defaults("gpt-5.4-nano")
        self.assertEqual(defaults.default_reasoning, ReasoningMode.DISABLED)
        self.assertTrue(defaults.use_responses_api)
        self.assertIsNone(defaults.default_temperature)

    def test_resolve_defaults_for_gpt52_pro(self) -> None:
        defaults = resolve_model_defaults("gpt-5.2-pro")
        self.assertEqual(defaults.default_reasoning, ReasoningMode.MEDIUM)
        self.assertTrue(defaults.use_responses_api)
        self.assertIsNone(defaults.default_temperature)

    def test_resolve_defaults_for_gpt5_pro(self) -> None:
        defaults = resolve_model_defaults("gpt-5-pro")
        self.assertEqual(defaults.default_reasoning, ReasoningMode.HIGH)
        self.assertTrue(defaults.use_responses_api)
        self.assertIsNone(defaults.default_temperature)

    def test_resolve_defaults_for_known_model(self) -> None:
        defaults = resolve_model_defaults("gpt-4.1")
        self.assertEqual(defaults.default_reasoning, ReasoningMode.TEMPERATURE)
        self.assertEqual(defaults.default_temperature, 0.7)
        self.assertTrue(defaults.use_responses_api)

    def test_resolve_defaults_for_unknown_model(self) -> None:
        defaults = resolve_model_defaults("custom-model")
        self.assertEqual(defaults.default_reasoning, ReasoningMode.DISABLED)
        self.assertIsNone(defaults.default_temperature)
        self.assertTrue(defaults.use_responses_api)


class OpenAIRequestBuilderTests(unittest.TestCase):
    def test_prepare_request_for_responses_api_includes_instructions(self) -> None:
        prepared = prepare_request(
            model_name="gpt-5-turbo",
            content="Hello world",
            system_prompt="You are a strict analyzer.",
            reasoning=ReasoningMode.LOW,
            temperature=None,
            tools=None,
            text_verbosity=None,
            use_responses_api=True,
        )

        self.assertEqual(prepared.api, "responses")
        payload = prepared.payload
        self.assertEqual(payload["instructions"], "You are a strict analyzer.")

    def test_prepare_request_for_chat_api_prepends_developer_message(self) -> None:
        prepared = prepare_request(
            model_name="gpt-4o-mini",
            content="Analyze this",
            system_prompt="Use concise bullet points.",
            reasoning=ReasoningMode.DISABLED,
            temperature=None,
            tools=None,
            text_verbosity=None,
            use_responses_api=False,
        )

        self.assertEqual(prepared.api, "chat")
        payload = prepared.payload
        self.assertEqual(payload["messages"][0], {"role": "developer", "content": "Use concise bullet points."})
        self.assertEqual(payload["messages"][1], {"role": "user", "content": "Analyze this"})

    def test_prepare_request_for_responses_api_gpt5(self) -> None:
        prepared = prepare_request(
            model_name="gpt-5-turbo",
            content="Hello world",
            reasoning=ReasoningMode.LOW,
            temperature=None,
            tools=[{"type": "function", "function": {"name": "ping", "parameters": {"type": "object"}}}],
            text_verbosity="concise",
            use_responses_api=True,
        )

        self.assertEqual(prepared.api, "responses")
        payload = prepared.payload
        self.assertEqual(payload["model"], "gpt-5-turbo")
        self.assertEqual(payload["input"], "Hello world")
        self.assertEqual(payload["reasoning"], {"effort": "low"})
        self.assertEqual(payload["text"], {"verbosity": "concise"})
        self.assertIn("tools", payload)
        self.assertEqual(payload["tool_choice"], "auto")

    def test_prepare_request_for_responses_api_gpt51(self) -> None:
        prepared = prepare_request(
            model_name="gpt-5.1-turbo",
            content="Hello gpt-5.1",
            reasoning=ReasoningMode.MINIMAL,
            temperature=None,
            tools=None,
            text_verbosity="low",
            use_responses_api=True,
        )

        self.assertEqual(prepared.api, "responses")
        payload = prepared.payload
        self.assertEqual(payload["model"], "gpt-5.1-turbo")
        self.assertEqual(payload["input"], "Hello gpt-5.1")
        self.assertEqual(payload["reasoning"], {"effort": "none"})
        self.assertEqual(payload["text"], {"verbosity": "low"})
        self.assertNotIn("tools", payload)

    def test_prepare_request_for_responses_api_gpt53_codex(self) -> None:
        prepared = prepare_request(
            model_name="gpt-5.3-codex",
            content="Hello gpt-5.3-codex",
            reasoning=ReasoningMode.MEDIUM,
            temperature=None,
            tools=None,
            text_verbosity="medium",
            use_responses_api=True,
        )

        self.assertEqual(prepared.api, "responses")
        payload = prepared.payload
        self.assertEqual(payload["model"], "gpt-5.3-codex")
        self.assertEqual(payload["input"], "Hello gpt-5.3-codex")
        self.assertEqual(payload["reasoning"], {"effort": "medium"})
        self.assertEqual(payload["text"], {"verbosity": "medium"})

    def test_prepare_request_for_responses_api_gpt55_xhigh(self) -> None:
        prepared = prepare_request(
            model_name="gpt-5.5",
            content="Hello gpt-5.5",
            reasoning=ReasoningMode.XHIGH,
            temperature=None,
            tools=None,
            text_verbosity="high",
            use_responses_api=True,
        )

        self.assertEqual(prepared.api, "responses")
        payload = prepared.payload
        self.assertEqual(payload["model"], "gpt-5.5")
        self.assertEqual(payload["input"], "Hello gpt-5.5")
        self.assertEqual(payload["reasoning"], {"effort": "xhigh"})
        self.assertEqual(payload["text"], {"verbosity": "high"})

    def test_prepare_request_for_responses_api_gpt55_minimal_downgrades_to_none(self) -> None:
        prepared = prepare_request(
            model_name="gpt-5.5",
            content="Hello gpt-5.5",
            reasoning=ReasoningMode.MINIMAL,
            temperature=None,
            tools=None,
            text_verbosity="low",
            use_responses_api=True,
        )

        self.assertEqual(prepared.api, "responses")
        payload = prepared.payload
        self.assertEqual(payload["model"], "gpt-5.5")
        self.assertEqual(payload["reasoning"], {"effort": "none"})
        self.assertEqual(payload["text"], {"verbosity": "low"})

    def test_prepare_request_for_responses_api_gpt54_mini_none(self) -> None:
        prepared = prepare_request(
            model_name="gpt-5.4-mini",
            content="Hello gpt-5.4-mini",
            reasoning=ReasoningMode.DISABLED,
            temperature=None,
            tools=None,
            text_verbosity="low",
            use_responses_api=True,
        )

        self.assertEqual(prepared.api, "responses")
        payload = prepared.payload
        self.assertEqual(payload["model"], "gpt-5.4-mini")
        self.assertEqual(payload["reasoning"], {"effort": "none"})
        self.assertEqual(payload["text"], {"verbosity": "low"})

    def test_prepare_request_for_responses_api_gpt54_nano_xhigh(self) -> None:
        prepared = prepare_request(
            model_name="gpt-5.4-nano",
            content="Hello gpt-5.4-nano",
            reasoning=ReasoningMode.XHIGH,
            temperature=None,
            tools=None,
            text_verbosity="high",
            use_responses_api=True,
        )

        self.assertEqual(prepared.api, "responses")
        payload = prepared.payload
        self.assertEqual(payload["model"], "gpt-5.4-nano")
        self.assertEqual(payload["reasoning"], {"effort": "xhigh"})
        self.assertEqual(payload["text"], {"verbosity": "high"})

    def test_prepare_request_for_responses_api_gpt54_pro_disabled_omits_reasoning(self) -> None:
        prepared = prepare_request(
            model_name="gpt-5.4-pro",
            content="Hello gpt-5.4-pro",
            reasoning=ReasoningMode.DISABLED,
            temperature=None,
            tools=None,
            text_verbosity="medium",
            use_responses_api=True,
        )

        self.assertEqual(prepared.api, "responses")
        payload = prepared.payload
        self.assertEqual(payload["model"], "gpt-5.4-pro")
        self.assertNotIn("reasoning", payload)
        self.assertEqual(payload["text"], {"verbosity": "medium"})

    def test_prepare_request_for_responses_api_gpt54_pro_xhigh(self) -> None:
        prepared = prepare_request(
            model_name="gpt-5.4-pro",
            content="Hello gpt-5.4-pro",
            reasoning=ReasoningMode.XHIGH,
            temperature=None,
            tools=None,
            text_verbosity="high",
            use_responses_api=True,
        )

        self.assertEqual(prepared.api, "responses")
        payload = prepared.payload
        self.assertEqual(payload["model"], "gpt-5.4-pro")
        self.assertEqual(payload["reasoning"], {"effort": "xhigh"})
        self.assertEqual(payload["text"], {"verbosity": "high"})

    def test_prepare_request_for_responses_api_gpt52_pro_disabled_omits_reasoning(self) -> None:
        prepared = prepare_request(
            model_name="gpt-5.2-pro",
            content="Hello gpt-5.2-pro",
            reasoning=ReasoningMode.DISABLED,
            temperature=None,
            tools=None,
            text_verbosity="medium",
            use_responses_api=True,
        )

        self.assertEqual(prepared.api, "responses")
        payload = prepared.payload
        self.assertEqual(payload["model"], "gpt-5.2-pro")
        self.assertNotIn("reasoning", payload)
        self.assertEqual(payload["text"], {"verbosity": "medium"})

    def test_prepare_request_for_responses_api_gpt5_pro_xhigh_downgrades_to_high(self) -> None:
        prepared = prepare_request(
            model_name="gpt-5-pro",
            content="Hello gpt-5-pro",
            reasoning=ReasoningMode.XHIGH,
            temperature=None,
            tools=None,
            text_verbosity="high",
            use_responses_api=True,
        )

        self.assertEqual(prepared.api, "responses")
        payload = prepared.payload
        self.assertEqual(payload["model"], "gpt-5-pro")
        self.assertEqual(payload["reasoning"], {"effort": "high"})
        self.assertEqual(payload["text"], {"verbosity": "high"})

    def test_prepare_request_for_responses_api_gpt52_codex_xhigh(self) -> None:
        prepared = prepare_request(
            model_name="gpt-5.2-codex",
            content="Hello gpt-5.2-codex",
            reasoning=ReasoningMode.XHIGH,
            temperature=None,
            tools=None,
            text_verbosity="high",
            use_responses_api=True,
        )

        self.assertEqual(prepared.api, "responses")
        payload = prepared.payload
        self.assertEqual(payload["model"], "gpt-5.2-codex")
        self.assertEqual(payload["reasoning"], {"effort": "xhigh"})
        self.assertEqual(payload["text"], {"verbosity": "high"})

    def test_prepare_request_for_responses_api_gpt51_codex_disabled_omits_reasoning(self) -> None:
        prepared = prepare_request(
            model_name="gpt-5.1-codex",
            content="Hello gpt-5.1-codex",
            reasoning=ReasoningMode.DISABLED,
            temperature=None,
            tools=None,
            text_verbosity="medium",
            use_responses_api=True,
        )

        self.assertEqual(prepared.api, "responses")
        payload = prepared.payload
        self.assertEqual(payload["model"], "gpt-5.1-codex")
        self.assertNotIn("reasoning", payload)
        self.assertEqual(payload["text"], {"verbosity": "medium"})

    def test_prepare_request_for_responses_api_gpt41_temperature(self) -> None:
        prepared = prepare_request(
            model_name="gpt-4.1",
            content="Plan",
            reasoning=ReasoningMode.TEMPERATURE,
            temperature=0.42,
            tools=None,
            text_verbosity=None,
            use_responses_api=True,
        )

        self.assertEqual(prepared.api, "responses")
        payload = prepared.payload
        self.assertEqual(payload["model"], "gpt-4.1")
        self.assertEqual(payload["input"], "Plan")
        self.assertEqual(payload["temperature"], 0.42)
        self.assertNotIn("reasoning", payload)

    def test_prepare_request_for_responses_api_merges_structured_text(self) -> None:
        text_format = {
            "format": {
                "type": "json_schema",
                "name": "phase2_response",
                "schema": {"type": "object"},
                "strict": True,
            }
        }
        prepared = prepare_request(
            model_name="gpt-5-turbo",
            content="Hello world",
            reasoning=ReasoningMode.LOW,
            temperature=None,
            tools=None,
            text_verbosity="concise",
            use_responses_api=True,
            structured_text=text_format,
        )

        payload = prepared.payload
        self.assertEqual(payload["text"]["verbosity"], "concise")
        self.assertEqual(payload["text"]["format"], text_format["format"])

    def test_prepare_request_for_responses_api_ignores_chat_response_format(self) -> None:
        prepared = prepare_request(
            model_name="gpt-4.1",
            content="Plan",
            reasoning=ReasoningMode.DISABLED,
            temperature=None,
            tools=None,
            text_verbosity=None,
            use_responses_api=True,
            chat_response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "phase2_response",
                    "schema": {"type": "object"},
                    "strict": True,
                },
            },
        )

        payload = prepared.payload
        self.assertNotIn("response_format", payload)

    def test_prepare_request_includes_reasoning_effort_for_o3(self) -> None:
        prepared = prepare_request(
            model_name="o3",
            content="Investigate",
            reasoning=ReasoningMode.HIGH,
            temperature=None,
            tools=None,
            text_verbosity=None,
            use_responses_api=True,
        )

        payload = prepared.payload
        self.assertEqual(prepared.api, "responses")
        self.assertEqual(payload["reasoning"], {"effort": "high"})


@dataclass
class _FakeFunction:
    name: str
    arguments: str


@dataclass
class _FakeToolCall:
    id: str
    type: str
    function: _FakeFunction


@dataclass
class _FakeMessage:
    content: str | None
    tool_calls: list[_FakeToolCall] | None


@dataclass
class _FakeChoice:
    message: _FakeMessage


class _FakeChatResponse:
    def __init__(self, content: str | None, tool_calls: list[_FakeToolCall] | None):
        self.choices = [_FakeChoice(_FakeMessage(content=content, tool_calls=tool_calls))]


class OpenAIResponseParserTests(unittest.TestCase):
    def test_parse_chat_response_with_tool_call(self) -> None:
        tool_call = _FakeToolCall(
            id="call_1",
            type="function",
            function=_FakeFunction(name="lookup", arguments='{"query": "foo"}'),
        )
        response = _FakeChatResponse(content=None, tool_calls=[tool_call])

        parsed = parse_response(response, "chat")

        self.assertIsNone(parsed.findings)
        self.assertIsNotNone(parsed.tool_calls)
        calls = parsed.tool_calls or []
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["function"]["name"], "lookup")
        self.assertEqual(calls[0]["function"]["arguments"], '{"query": "foo"}')

    def test_parse_responses_output_with_aggregated_text(self) -> None:
        payload: dict[str, Any] = {
            "output": [],
            "output_text": "Aggregated text",
        }

        parsed = parse_response(payload, "responses")

        self.assertEqual(parsed.findings, "Aggregated text")
        self.assertIsNone(parsed.tool_calls)

    def test_parse_responses_output_tool_call(self) -> None:
        payload: dict[str, Any] = {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "custom_tool_call",
                            "id": "call_2",
                            "name": "webhook",
                            "input": {"url": "https://example.com"},
                        }
                    ],
                }
            ]
        }

        parsed = parse_response(payload, "responses")

        tool_calls = parsed.tool_calls or []
        self.assertEqual(len(tool_calls), 1)
        self.assertEqual(tool_calls[0]["type"], "custom")
        self.assertEqual(tool_calls[0]["name"], "webhook")
        self.assertEqual(tool_calls[0]["input"], {"url": "https://example.com"})


if __name__ == "__main__":
    unittest.main()
