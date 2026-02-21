from __future__ import annotations

import unittest
from typing import Any, cast
from unittest.mock import patch

from google.genai import types as genai_types
from google.protobuf.struct_pb2 import Struct

from agentrules.core.agents.base import ReasoningMode
from agentrules.core.agents.gemini import GeminiArchitect
from tests.fakes.vendor_responses import GeminiGenerateContentResponseFake, _FunctionCallFake


class _GeminiFakeModelsService:
    def __init__(self) -> None:
        self.last_call: dict[str, Any] | None = None

    def generate_content(self, model, contents, config=None):
        self.last_call = {"model": model, "contents": contents, "config": config}
        s = Struct(); s.update({"query": "flask"})
        fc = _FunctionCallFake("tavily_search", s)
        return GeminiGenerateContentResponseFake(text="hello", function_call=fc)


class _GeminiFakeClient:
    def __init__(self):
        self.models = _GeminiFakeModelsService()


class _GeminiToolSensitiveModelsService:
    def __init__(self) -> None:
        self.last_call: dict[str, Any] | None = None

    def generate_content(self, model, contents, config=None):
        self.last_call = {"model": model, "contents": contents, "config": config}
        has_tools = bool(getattr(config, "tools", None)) if config is not None else False

        if has_tools:
            args = Struct()
            args.update({"query": "should-not-be-used-in-phase5"})
            return GeminiGenerateContentResponseFake(text=None, function_call=_FunctionCallFake("lookup", args))

        return GeminiGenerateContentResponseFake(
            text='{"phase":"Consolidation","report":"Merged findings"}'
        )


class _GeminiToolSensitiveClient:
    def __init__(self) -> None:
        self.models = _GeminiToolSensitiveModelsService()


class GeminiArchitectParsingTests(unittest.IsolatedAsyncioTestCase):
    async def test_extracts_text_and_function_calls(self):
        arch = GeminiArchitect()
        # Inject fake client
        arch.client = _GeminiFakeClient()  # type: ignore
        res = await arch.analyze({"x": 1})
        self.assertEqual(res.get("findings"), "hello")
        self.assertIn("function_calls", res)
        fc = res["function_calls"][0]
        self.assertEqual(fc["name"], "tavily_search")
        self.assertEqual(fc["args"].get("query"), "flask")

    async def test_reasoning_disabled_disables_thinking_budget(self):
        arch = GeminiArchitect(reasoning=ReasoningMode.DISABLED)
        arch.client = _GeminiFakeClient()  # type: ignore
        await arch.analyze({})
        config = arch.client.models.last_call["config"]  # type: ignore[index]
        self.assertIsNotNone(config)
        self.assertEqual(config.thinking_config.thinking_budget, 0)

    async def test_reasoning_dynamic_sets_dynamic_budget(self):
        arch = GeminiArchitect(reasoning=ReasoningMode.DYNAMIC)
        arch.client = _GeminiFakeClient()  # type: ignore
        await arch.analyze({})
        config = arch.client.models.last_call["config"]  # type: ignore[index]
        self.assertEqual(config.thinking_config.thinking_budget, -1)

    async def test_pro_model_disable_falls_back_to_dynamic(self):
        arch = GeminiArchitect(model_name="gemini-2.5-pro", reasoning=ReasoningMode.DISABLED)
        arch.client = _GeminiFakeClient()  # type: ignore
        await arch.analyze({})
        config = arch.client.models.last_call["config"]  # type: ignore[index]
        self.assertEqual(config.thinking_config.thinking_budget, -1)

    async def test_gemini3_dynamic_maps_to_thinking_level_high(self):
        arch = GeminiArchitect(model_name="gemini-3-pro-preview", reasoning=ReasoningMode.DYNAMIC)
        arch.client = _GeminiFakeClient()  # type: ignore
        await arch.analyze({})
        config = arch.client.models.last_call["config"]  # type: ignore[index]
        thinking_level = cast(Any, getattr(genai_types, "ThinkingLevel", None))
        self.assertIsNotNone(thinking_level)
        self.assertEqual(config.thinking_config.thinking_level, thinking_level.HIGH)
        self.assertIsNone(config.thinking_config.thinking_budget)

    async def test_gemini3_disabled_maps_to_thinking_level_low(self):
        arch = GeminiArchitect(model_name="gemini-3-pro-preview", reasoning=ReasoningMode.DISABLED)
        arch.client = _GeminiFakeClient()  # type: ignore
        await arch.analyze({})
        config = arch.client.models.last_call["config"]  # type: ignore[index]
        thinking_level = cast(Any, getattr(genai_types, "ThinkingLevel", None))
        self.assertIsNotNone(thinking_level)
        self.assertEqual(config.thinking_config.thinking_level, thinking_level.LOW)
        self.assertIsNone(config.thinking_config.thinking_budget)

    async def test_consolidation_disables_tools_even_when_configured(self):
        arch = GeminiArchitect(
            model_name="gemini-2.5-flash",
            tools_config={
                "enabled": True,
                "tools": [{"type": "function", "function": {"name": "lookup", "parameters": {"type": "object"}}}],
            },
        )
        arch.client = _GeminiToolSensitiveClient()  # type: ignore

        with patch(
            "agentrules.core.agents.gemini.architect.resolve_tool_config",
            return_value=[{"function_declarations": [{"name": "lookup"}]}],
        ):
            result = await arch.consolidate_results({"phase1": {}, "phase2": {}, "phase3": {}, "phase4": {}})

        self.assertEqual(result.get("phase"), "Consolidation")
        self.assertEqual(result.get("report"), "Merged findings")

        config = arch.client.models.last_call["config"]  # type: ignore[index]
        self.assertIsNotNone(config)
        self.assertFalse(bool(getattr(config, "tools", None)))

    async def test_phase_schema_request_disables_tools_for_non_gemini3_models(self):
        arch = GeminiArchitect(
            model_name="gemini-2.5-flash",
            tools_config={
                "enabled": True,
                "tools": [{"type": "function", "function": {"name": "lookup", "parameters": {"type": "object"}}}],
            },
        )
        arch.client = _GeminiToolSensitiveClient()  # type: ignore

        with patch(
            "agentrules.core.agents.gemini.architect.resolve_tool_config",
            return_value=[{"function_declarations": [{"name": "lookup"}]}],
        ):
            result = await arch.create_analysis_plan({"phase": "Initial Discovery"}, prompt="Return a plan")

        self.assertIn("plan", result)
        config = arch.client.models.last_call["config"]  # type: ignore[index]
        self.assertIsNotNone(config)
        self.assertFalse(bool(getattr(config, "tools", None)))
        self.assertIsNotNone(getattr(config, "response_json_schema", None))

    async def test_phase_schema_request_keeps_tools_for_gemini3_models(self):
        arch = GeminiArchitect(
            model_name="gemini-3-pro-preview",
            tools_config={
                "enabled": True,
                "tools": [{"type": "function", "function": {"name": "lookup", "parameters": {"type": "object"}}}],
            },
        )
        arch.client = _GeminiToolSensitiveClient()  # type: ignore

        with patch(
            "agentrules.core.agents.gemini.architect.resolve_tool_config",
            return_value=[{"function_declarations": [{"name": "lookup"}]}],
        ):
            _ = await arch.create_analysis_plan({"phase": "Initial Discovery"}, prompt="Return a plan")

        config = arch.client.models.last_call["config"]  # type: ignore[index]
        self.assertIsNotNone(config)
        self.assertTrue(bool(getattr(config, "tools", None)))
        self.assertIsNotNone(getattr(config, "response_json_schema", None))
