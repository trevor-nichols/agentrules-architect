from __future__ import annotations

import os
import unittest
from dataclasses import dataclass
from unittest import mock

from agentrules.core.agents.base import ReasoningMode
from agentrules.core.agents.deepseek.config import (
    API_BASE_ENV_VAR,
    DEFAULT_BASE_URL,
    resolve_base_url,
    resolve_model_alias,
    resolve_model_defaults,
)
from agentrules.core.agents.deepseek.request_builder import prepare_request
from agentrules.core.agents.deepseek.response_parser import parse_response
from agentrules.core.agents.deepseek.tooling import resolve_tool_config


class DeepSeekConfigTests(unittest.TestCase):
    def test_resolve_legacy_model_aliases(self) -> None:
        self.assertEqual(
            resolve_model_alias("deepseek-chat"),
            ("deepseek-v4-flash", ReasoningMode.DISABLED),
        )
        self.assertEqual(
            resolve_model_alias("deepseek-reasoner"),
            ("deepseek-v4-flash", ReasoningMode.HIGH),
        )

    def test_resolve_defaults_for_v4_flash(self) -> None:
        defaults = resolve_model_defaults("deepseek-v4-flash")
        self.assertEqual(defaults.default_reasoning, ReasoningMode.HIGH)
        self.assertTrue(defaults.tools_allowed)
        self.assertTrue(defaults.supports_sampling)
        self.assertTrue(defaults.supports_thinking_toggle)
        self.assertEqual(defaults.accepted_reasoning_efforts, frozenset({"high", "max"}))
        self.assertEqual(defaults.max_output_tokens, 32_000)

    def test_resolve_defaults_for_v4_pro(self) -> None:
        defaults = resolve_model_defaults("deepseek-v4-pro")
        self.assertEqual(defaults.default_reasoning, ReasoningMode.HIGH)
        self.assertTrue(defaults.tools_allowed)
        self.assertTrue(defaults.supports_thinking_toggle)
        self.assertEqual(defaults.accepted_reasoning_efforts, frozenset({"high", "max"}))

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
    def test_prepare_v4_thinking_request_includes_high_effort_and_tools(self) -> None:
        defaults = resolve_model_defaults("deepseek-v4-flash")
        tools = [
            {
                "type": "function",
                "function": {"name": "lookup", "description": "", "parameters": {"type": "object"}},
            }
        ]

        prepared = prepare_request(
            model_name="deepseek-v4-flash",
            content="Analyze this project",
            reasoning=ReasoningMode.HIGH,
            defaults=defaults,
            tools=tools,
            temperature=0.6,
        )

        self.assertEqual(prepared.payload["extra_body"], {"thinking": {"type": "enabled"}})
        self.assertEqual(prepared.payload["reasoning_effort"], "high")
        self.assertEqual(prepared.payload["max_tokens"], 32_000)
        self.assertEqual(prepared.payload["tools"], tools)
        self.assertEqual(prepared.payload["tool_choice"], "auto")
        self.assertNotIn("temperature", prepared.payload)

    def test_prepare_v4_xhigh_request_maps_to_max_effort(self) -> None:
        defaults = resolve_model_defaults("deepseek-v4-pro")

        prepared = prepare_request(
            model_name="deepseek-v4-pro",
            content="Analyze this project",
            reasoning=ReasoningMode.XHIGH,
            defaults=defaults,
            tools=None,
        )

        self.assertEqual(prepared.payload["extra_body"], {"thinking": {"type": "enabled"}})
        self.assertEqual(prepared.payload["reasoning_effort"], "max")

    def test_prepare_v4_max_request_maps_to_max_effort(self) -> None:
        defaults = resolve_model_defaults("deepseek-v4-pro")

        prepared = prepare_request(
            model_name="deepseek-v4-pro",
            content="Analyze this project",
            reasoning=ReasoningMode.MAX,
            defaults=defaults,
            tools=None,
        )

        self.assertEqual(prepared.payload["reasoning_effort"], "max")

    def test_prepare_v4_non_thinking_request_explicitly_disables_thinking(self) -> None:
        defaults = resolve_model_defaults("deepseek-v4-flash")

        prepared = prepare_request(
            model_name="deepseek-v4-flash",
            content="Analyze this project",
            reasoning=ReasoningMode.DISABLED,
            defaults=defaults,
            tools=None,
            temperature=0.6,
        )

        self.assertEqual(prepared.payload["extra_body"], {"thinking": {"type": "disabled"}})
        self.assertNotIn("reasoning_effort", prepared.payload)
        self.assertEqual(prepared.payload["temperature"], 0.6)

    def test_prepare_v4_low_and_medium_efforts_normalize_to_high(self) -> None:
        defaults = resolve_model_defaults("deepseek-v4-flash")

        for reasoning in (ReasoningMode.MINIMAL, ReasoningMode.LOW, ReasoningMode.MEDIUM):
            with self.subTest(reasoning=reasoning):
                prepared = prepare_request(
                    model_name="deepseek-v4-flash",
                    content="Analyze this project",
                    reasoning=reasoning,
                    defaults=defaults,
                    tools=None,
                )
                self.assertEqual(prepared.payload["reasoning_effort"], "high")

    def test_prepare_request_prepends_system_message(self) -> None:
        defaults = resolve_model_defaults("deepseek-chat")
        prepared = prepare_request(
            model_name="deepseek-chat",
            content="Analyze this project",
            system_prompt="You are a strict reviewer.",
            reasoning=ReasoningMode.DISABLED,
            defaults=defaults,
            tools=None,
        )

        payload = prepared.payload
        self.assertEqual(payload["messages"][0], {"role": "system", "content": "You are a strict reviewer."})
        self.assertEqual(payload["messages"][1], {"role": "user", "content": "Analyze this project"})

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

    def test_prepare_request_rejects_effort_missing_from_model_capabilities(self) -> None:
        defaults = resolve_model_defaults("deepseek-v4-pro")
        restricted_defaults = defaults.__class__(
            default_reasoning=defaults.default_reasoning,
            max_output_tokens=defaults.max_output_tokens,
            tools_allowed=defaults.tools_allowed,
            supports_sampling=defaults.supports_sampling,
            supports_thinking_toggle=True,
            accepted_reasoning_efforts=frozenset({"high"}),
        )

        with self.assertRaisesRegex(ValueError, "not supported"):
            prepare_request(
                model_name="deepseek-v4-pro",
                content="Analyze this project",
                reasoning=ReasoningMode.XHIGH,
                defaults=restricted_defaults,
                tools=None,
            )

    def test_prepare_request_adds_response_format(self) -> None:
        defaults = resolve_model_defaults("deepseek-chat")
        prepared = prepare_request(
            model_name="deepseek-chat",
            content="Return JSON",
            reasoning=ReasoningMode.DISABLED,
            defaults=defaults,
            tools=None,
            response_format={"type": "json_object"},
        )

        payload = prepared.payload
        self.assertEqual(payload["response_format"], {"type": "json_object"})


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
