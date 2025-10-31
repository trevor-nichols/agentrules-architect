from __future__ import annotations

import os
import unittest
from dataclasses import dataclass
from unittest import mock

from core.agents.base import ReasoningMode
from core.agents.deepseek.config import (
    API_BASE_ENV_VAR,
    DEFAULT_BASE_URL,
    resolve_base_url,
    resolve_model_defaults,
)
from core.agents.deepseek.request_builder import prepare_request
from core.agents.deepseek.response_parser import parse_response
from core.agents.deepseek.tooling import resolve_tool_config


class DeepSeekConfigTests(unittest.TestCase):
    def test_resolve_defaults_for_chat(self) -> None:
        defaults = resolve_model_defaults("deepseek-chat")
        self.assertEqual(defaults.default_reasoning, ReasoningMode.DISABLED)
        self.assertTrue(defaults.tools_allowed)
        self.assertIsNone(defaults.max_output_tokens)

    def test_resolve_defaults_for_reasoner(self) -> None:
        defaults = resolve_model_defaults("deepseek-reasoner")
        self.assertEqual(defaults.default_reasoning, ReasoningMode.ENABLED)
        self.assertFalse(defaults.tools_allowed)
        self.assertEqual(defaults.max_output_tokens, 32_000)

    def test_resolve_base_url_priority(self) -> None:
        explicit = resolve_base_url("https://custom.deepseek.local")
        self.assertEqual(explicit, "https://custom.deepseek.local")

        with mock.patch.dict(os.environ, {API_BASE_ENV_VAR: "https://env.deepseek.local"}):
            env_value = resolve_base_url(None)
        self.assertEqual(env_value, "https://env.deepseek.local")

        with mock.patch.dict(os.environ, {API_BASE_ENV_VAR: ""}):
            default_value = resolve_base_url(None)
        self.assertEqual(default_value, DEFAULT_BASE_URL)


class DeepSeekRequestBuilderTests(unittest.TestCase):
    def test_prepare_request_includes_temperature_for_chat(self) -> None:
        defaults = resolve_model_defaults("deepseek-chat")
        prepared = prepare_request(
            model_name="deepseek-chat",
            content="Please analyze",
            reasoning=ReasoningMode.DISABLED,
            defaults=defaults,
            tools=None,
            temperature=0.6,
        )

        payload = prepared.payload
        self.assertEqual(payload["temperature"], 0.6)

    def test_prepare_request_allows_tools_for_chat(self) -> None:
        defaults = resolve_model_defaults("deepseek-chat")
        prepared = prepare_request(
            model_name="deepseek-chat",
            content="Analyze this project",
            reasoning=ReasoningMode.DISABLED,
            defaults=defaults,
            tools=[
                {
                    "type": "function",
                    "function": {"name": "lookup", "description": "", "parameters": {"type": "object"}},
                }
            ],
        )

        payload = prepared.payload
        self.assertEqual(payload["model"], "deepseek-chat")
        self.assertEqual(payload["messages"][0]["content"], "Analyze this project")
        self.assertIn("tools", payload)
        self.assertEqual(payload["tool_choice"], "auto")
        self.assertNotIn("max_tokens", payload)

    def test_prepare_request_disables_tools_for_reasoner(self) -> None:
        defaults = resolve_model_defaults("deepseek-reasoner")
        prepared = prepare_request(
            model_name="deepseek-reasoner",
            content="Reason about architecture",
            reasoning=ReasoningMode.ENABLED,
            defaults=defaults,
            tools=[
                {
                    "type": "function",
                    "function": {"name": "lookup", "description": "", "parameters": {"type": "object"}},
                }
            ],
            temperature=0.2,
        )

        payload = prepared.payload
        self.assertEqual(payload["model"], "deepseek-reasoner")
        self.assertEqual(payload["max_tokens"], 32_000)
        self.assertNotIn("tools", payload)
        self.assertNotIn("tool_choice", payload)
        self.assertNotIn("temperature", payload)


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
    content: str | list[str] | None
    reasoning_content: str | None
    tool_calls: list[_FakeToolCall] | None


@dataclass
class _FakeChoice:
    message: _FakeMessage


class _FakeChatResponse:
    def __init__(self, message: _FakeMessage):
        self.choices = [_FakeChoice(message)]


class DeepSeekResponseParserTests(unittest.TestCase):
    def test_parse_response_with_reasoning(self) -> None:
        message = _FakeMessage(
            content="Final answer",
            reasoning_content="Chain of thought",
            tool_calls=None,
        )
        parsed = parse_response(_FakeChatResponse(message))

        self.assertEqual(parsed.findings, "Final answer")
        self.assertEqual(parsed.reasoning, "Chain of thought")
        self.assertIsNone(parsed.tool_calls)

    def test_parse_response_collapses_list_content_and_tool_calls(self) -> None:
        tool_call = _FakeToolCall(
            id="call_1",
            type="function",
            function=_FakeFunction(name="lookup", arguments='{"query": "foo"}'),
        )
        message = _FakeMessage(
            content=["Part one", "Part two"],
            reasoning_content=None,
            tool_calls=[tool_call],
        )

        parsed = parse_response(_FakeChatResponse(message))

        self.assertEqual(parsed.findings, "Part one\nPart two")
        self.assertIsNone(parsed.reasoning)
        self.assertIsNotNone(parsed.tool_calls)
        calls = parsed.tool_calls or []
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["function"]["name"], "lookup")
        self.assertEqual(calls[0]["function"]["arguments"], '{"query": "foo"}')


class DeepSeekToolingTests(unittest.TestCase):
    def test_resolve_tool_config_returns_tools(self) -> None:
        tool = {
            "type": "function",
            "function": {
                "name": "lookup",
                "description": "",
                "parameters": {"type": "object", "properties": {}}
            },
        }

        resolved = resolve_tool_config(
            tools=None,
            tools_config={"enabled": True, "tools": [tool]},
            allow_tools=True,
        )

        self.assertIsNotNone(resolved)
        assert resolved is not None
        self.assertIsInstance(resolved, list)
        self.assertEqual(resolved[0]["function"]["name"], "lookup")



if __name__ == "__main__":
    unittest.main()
