from __future__ import annotations

import json
import unittest
from typing import Any, cast
from unittest.mock import patch

import httpx2
import pytest
from google.genai import types as genai_types
from google.protobuf.struct_pb2 import Struct

from agentrules.core.agents.base import ReasoningMode
from agentrules.core.agents.gemini import GeminiAgent, GeminiArchitect
from agentrules.core.agents.gemini.client import build_gemini_client, generate_content_async
from tests.fakes.vendor_responses import GeminiGenerateContentResponseFake, _FunctionCallFake


@pytest.fixture
def gemini_wire_requests(monkeypatch: pytest.MonkeyPatch) -> list[httpx2.Request]:
    requests: list[httpx2.Request] = []

    def handle_request(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return httpx2.Response(
            200,
            json={
                "candidates": [
                    {"content": {"role": "model", "parts": [{"text": "Wire response"}]}, "finishReason": "STOP"},
                ],
            },
        )

    init_client = httpx2.Client.__init__

    def init_with_mock_transport(client: httpx2.Client, **kwargs: Any) -> None:
        init_client(client, **(kwargs | {"transport": httpx2.MockTransport(handle_request)}))

    monkeypatch.setattr(httpx2.Client, "__init__", init_with_mock_transport)
    for variable in (
        "GEMINI_API_KEY",
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_CLOUD_LOCATION",
        "GOOGLE_GENAI_API_VERSION",
        "GOOGLE_GENAI_USE_ENTERPRISE",
        "GOOGLE_GENAI_USE_VERTEXAI",
    ):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "sdk-key")
    monkeypatch.setenv("GOOGLE_API_USE_MTLS_ENDPOINT", "never")
    monkeypatch.setenv("GOOGLE_GENAI_HTTP_CLIENT", "httpx2")
    return requests


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("api_key", "managed_flag", "host", "path_prefix", "sent_key"),
    [
        ("direct-key", None, "generativelanguage.googleapis.com", "/v1beta/models", "direct-key"),
        (None, None, "generativelanguage.googleapis.com", "/v1beta/models", "sdk-key"),
        ("direct-key", "GOOGLE_GENAI_USE_VERTEXAI", "aiplatform.googleapis.com",
         "/v1beta1/publishers/google/models", "direct-key"),
        ("direct-key", "GOOGLE_GENAI_USE_ENTERPRISE", "aiplatform.googleapis.com",
         "/v1beta1/publishers/google/models", "direct-key"),
    ],
    ids=["developer-configured-key", "developer-sdk-key", "vertex", "enterprise"],
)
async def test_preview_request_keeps_gemini_client_endpoint(
    monkeypatch: pytest.MonkeyPatch,
    gemini_wire_requests: list[httpx2.Request],
    api_key: str | None,
    managed_flag: str | None,
    host: str,
    path_prefix: str,
    sent_key: str,
) -> None:
    if managed_flag:
        monkeypatch.setenv(managed_flag, "true")

    client, error = build_gemini_client(api_key)
    assert client is not None, error
    try:
        response = await generate_content_async(
            client, model="gemini-3.1-pro-preview", contents="Analyze the project", config=None
        )
    finally:
        client.close()

    assert response.text == "Wire response"
    request, = gemini_wire_requests
    assert request.url.host == host
    assert request.url.path == f"{path_prefix}/gemini-3.1-pro-preview:generateContent"
    assert request.headers["x-goog-api-key"] == sent_key


@pytest.mark.asyncio
@pytest.mark.parametrize(("api_version", "expected_version"), [(None, "v1beta"), ("v1", "v1")])
async def test_gemini_sdk_applies_request_timeout_without_changing_api_version(
    monkeypatch: pytest.MonkeyPatch,
    gemini_wire_requests: list[httpx2.Request],
    api_version: str | None,
    expected_version: str,
) -> None:
    if api_version:
        monkeypatch.setenv("GOOGLE_GENAI_API_VERSION", api_version)
    client, error = build_gemini_client(None)
    assert client is not None, error
    config = genai_types.GenerateContentConfig(http_options=genai_types.HttpOptions(timeout=1_200_000))
    try:
        response = await generate_content_async(
            client, model="gemini-4-argon", contents="Analyze the project", config=config
        )
    finally:
        client.close()

    assert response.text == "Wire response"
    request, = gemini_wire_requests
    assert request.url.path == f"/{expected_version}/models/gemini-4-argon:generateContent"
    assert request.extensions["timeout"]["read"] == 1200


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
    async def test_system_instruction_includes_role_and_responsibilities(self):
        arch = GeminiArchitect(
            name="Gemini Planner",
            role="security-focused architecture analysis",
            responsibilities=["Identify high-risk code paths"],
        )
        arch.client = _GeminiFakeClient()  # type: ignore

        await arch.analyze({})

        config = arch.client.models.last_call["config"]  # type: ignore[index]
        self.assertIsNotNone(config)
        instruction = getattr(config, "system_instruction", "")
        self.assertIn("Gemini Planner", instruction)
        self.assertIn("security-focused architecture analysis", instruction)
        self.assertIn("Identify high-risk code paths", instruction)

    async def test_system_instruction_can_be_overridden_from_context(self):
        arch = GeminiArchitect(
            name="Gemini Planner",
            role="architecture analysis",
        )
        arch.client = _GeminiFakeClient()  # type: ignore

        await arch.analyze({"system_prompt": "Use strict JSON output and concise findings."})

        config = arch.client.models.last_call["config"]  # type: ignore[index]
        self.assertIsNotNone(config)
        self.assertEqual(
            getattr(config, "system_instruction", None),
            "Use strict JSON output and concise findings.",
        )

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
        self.assertIsInstance(json.dumps(res), str)

    async def test_default_entry_points_send_flash_lite_with_minimal_thinking(self):
        for entry_point, build_agent in (
            ("architect", lambda: GeminiArchitect(api_key="test-key")),
            ("legacy", lambda: GeminiAgent("Legacy", "Analyze", [], api_key="test-key")),
        ):
            with self.subTest(entry_point=entry_point):
                client = _GeminiFakeClient()
                with patch("agentrules.core.agents.gemini.client.genai.Client", return_value=client):
                    agent = build_agent()

                await agent.analyze({"formatted_prompt": "Analyze the project"})

                request = client.models.last_call
                assert request is not None
                self.assertEqual(request["model"], "gemini-3.5-flash-lite")
                self.assertEqual(request["config"].thinking_config.thinking_level, genai_types.ThinkingLevel.MINIMAL)
                self.assertIsNone(request["config"].thinking_config.thinking_budget)

    async def test_default_model_rejects_explicit_disabled_reasoning(self):
        arch = GeminiArchitect(reasoning=ReasoningMode.DISABLED)
        client = _GeminiFakeClient()
        arch.client = client  # type: ignore

        with self.assertRaisesRegex(ValueError, "gemini-3.5-flash-lite"):
            await arch.analyze({})

        self.assertIsNone(client.models.last_call)

    async def test_explicit_gemini25_flash_with_no_reasoning_keeps_zero_budget(self):
        arch = GeminiArchitect(model_name="gemini-2.5-flash")
        arch.client = _GeminiFakeClient()  # type: ignore
        await arch.analyze({})
        request = arch.client.models.last_call  # type: ignore[union-attr]
        self.assertEqual(request["model"], "gemini-2.5-flash")
        self.assertEqual(request["config"].thinking_config.thinking_budget, 0)
        self.assertIsNone(request["config"].thinking_config.thinking_level)

    async def test_flash_models_requiring_an_exact_level_default_to_medium(self):
        for model_name in ("gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.8-flash"):
            with self.subTest(model=model_name):
                client = _GeminiFakeClient()
                with patch("agentrules.core.agents.gemini.client.genai.Client", return_value=client):
                    arch = GeminiArchitect(model_name=model_name, api_key="test-key")

                await arch.analyze({"formatted_prompt": "Analyze the project"})

                request = client.models.last_call
                assert request is not None
                self.assertEqual(request["model"], model_name)
                self.assertEqual(request["config"].thinking_config.thinking_level, genai_types.ThinkingLevel.MEDIUM)
                self.assertIsNone(request["config"].thinking_config.thinking_budget)

    async def test_reasoning_dynamic_sets_dynamic_budget(self):
        arch = GeminiArchitect(model_name="gemini-2.5-flash", reasoning=ReasoningMode.DYNAMIC)
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

    async def test_gemini31_pro_dynamic_maps_to_thinking_level_high(self):
        arch = GeminiArchitect(model_name="gemini-3.1-pro-preview", reasoning=ReasoningMode.DYNAMIC)
        arch.client = _GeminiFakeClient()  # type: ignore
        await arch.analyze({})
        config = arch.client.models.last_call["config"]  # type: ignore[index]
        thinking_level = cast(Any, getattr(genai_types, "ThinkingLevel", None))
        self.assertIsNotNone(thinking_level)
        self.assertEqual(config.thinking_config.thinking_level, thinking_level.HIGH)
        self.assertIsNone(config.thinking_config.thinking_budget)

    async def test_gemini31_pro_disabled_maps_to_thinking_level_low(self):
        arch = GeminiArchitect(model_name="gemini-3.1-pro-preview", reasoning=ReasoningMode.DISABLED)
        arch.client = _GeminiFakeClient()  # type: ignore
        await arch.analyze({})
        config = arch.client.models.last_call["config"]  # type: ignore[index]
        thinking_level = cast(Any, getattr(genai_types, "ThinkingLevel", None))
        self.assertIsNotNone(thinking_level)
        self.assertEqual(config.thinking_config.thinking_level, thinking_level.LOW)
        self.assertIsNone(config.thinking_config.thinking_budget)

    async def test_gemini31_flash_lite_disabled_maps_to_thinking_level_minimal(self):
        arch = GeminiArchitect(model_name="gemini-3.1-flash-lite", reasoning=ReasoningMode.DISABLED)
        arch.client = _GeminiFakeClient()  # type: ignore
        await arch.analyze({})
        config = arch.client.models.last_call["config"]  # type: ignore[index]
        thinking_level = cast(Any, getattr(genai_types, "ThinkingLevel", None))
        self.assertIsNotNone(thinking_level)
        expected_level = getattr(thinking_level, "MINIMAL", thinking_level.LOW)
        self.assertEqual(config.thinking_config.thinking_level, expected_level)
        self.assertIsNone(config.thinking_config.thinking_budget)

    async def test_gemini35_flash_medium_maps_to_thinking_level_medium(self):
        arch = GeminiArchitect(model_name="gemini-3.5-flash", reasoning=ReasoningMode.MEDIUM)
        arch.client = _GeminiFakeClient()  # type: ignore
        await arch.analyze({})
        config = arch.client.models.last_call["config"]  # type: ignore[index]
        thinking_level = cast(Any, getattr(genai_types, "ThinkingLevel", None))
        self.assertIsNotNone(thinking_level)
        expected_level = getattr(thinking_level, "MEDIUM", thinking_level.HIGH)
        self.assertEqual(config.thinking_config.thinking_level, expected_level)
        self.assertIsNone(config.thinking_config.thinking_budget)

    async def test_gemini37_invalid_reasoning_fails_before_dispatch(self):
        arch = GeminiArchitect(model_name="gemini-3.7-flash", reasoning=ReasoningMode.DISABLED)
        arch.client = _GeminiFakeClient()  # type: ignore

        with self.assertRaisesRegex(ValueError, "gemini-3.7-flash"):
            await arch.analyze({})

        self.assertIsNone(arch.client.models.last_call)  # type: ignore[union-attr]

    async def test_gemini38_disabled_thinking_fails_before_dispatch(self):
        arch = GeminiArchitect(model_name="gemini-3.8-flash", reasoning=ReasoningMode.DISABLED)
        arch.client = _GeminiFakeClient()  # type: ignore

        with self.assertRaisesRegex(ValueError, "gemini-3.8-flash"):
            await arch.analyze({})

        self.assertIsNone(arch.client.models.last_call)  # type: ignore[union-attr]

    async def test_argon_request_uses_sdk_continuation_and_shared_budget(self):
        arch = GeminiArchitect(model_name="gemini-4-argon", reasoning=ReasoningMode.HIGH)
        arch.client = _GeminiFakeClient()  # type: ignore

        await arch.analyze({"formatted_prompt": "Analyze the project"})

        request = arch.client.models.last_call  # type: ignore[union-attr]
        self.assertEqual(request["model"], "gemini-4-argon")
        config = request["config"]
        self.assertEqual(config.thinking_config.thinking_level, genai_types.ThinkingLevel.HIGH)
        self.assertEqual(config.max_output_tokens, 65_536)
        self.assertTrue(config.automatic_continuation)
        self.assertGreaterEqual(config.http_options.timeout, 1_200_000)

    async def test_gemini31_pro_medium_maps_to_thinking_level_high(self):
        arch = GeminiArchitect(model_name="gemini-3.1-pro-preview", reasoning=ReasoningMode.MEDIUM)
        arch.client = _GeminiFakeClient()  # type: ignore
        await arch.analyze({})
        config = arch.client.models.last_call["config"]  # type: ignore[index]
        thinking_level = cast(Any, getattr(genai_types, "ThinkingLevel", None))
        self.assertIsNotNone(thinking_level)
        self.assertEqual(config.thinking_config.thinking_level, thinking_level.HIGH)
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
            model_name="gemini-3.5-flash",
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

    async def test_phase_schema_request_keeps_tools_for_gemini31_flash_lite_models(self):
        arch = GeminiArchitect(
            model_name="gemini-3.1-flash-lite",
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
