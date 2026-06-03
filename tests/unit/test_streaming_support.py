"""Unit tests covering streaming infrastructure and provider adapters."""

from __future__ import annotations

import asyncio
import unittest
from collections.abc import Iterator
from typing import Any, cast
from unittest.mock import patch

from agentrules.core.agents.anthropic import AnthropicArchitect
from agentrules.core.agents.base import BaseArchitect, ModelProvider, ReasoningMode
from agentrules.core.agents.deepseek import DeepSeekArchitect
from agentrules.core.agents.gemini import GeminiArchitect
from agentrules.core.agents.openai import OpenAIArchitect
from agentrules.core.agents.xai import XaiArchitect
from agentrules.core.streaming import StreamChunk, StreamEventType
from agentrules.core.utils.async_stream import iterate_in_thread


async def _collect_async(iterator) -> list[StreamChunk]:
    """Helper to gather all chunks from an async iterator."""
    events: list[StreamChunk] = []
    async for item in iterator:
        events.append(item)
    return events


class AsyncStreamAdapterTests(unittest.TestCase):
    def test_iterate_in_thread_yields_values(self) -> None:
        async def consume() -> list[int]:
            iterator = iterate_in_thread(lambda: iter([1, 2, 3]))
            values: list[int] = []
            async for value in iterator:
                values.append(value)
            return values

        result = asyncio.run(consume())
        self.assertEqual(result, [1, 2, 3])

    def test_iterate_in_thread_propagates_errors(self) -> None:
        def factory() -> Iterator[int]:
            yield 1
            raise RuntimeError("boom")

        async def consume() -> None:
            iterator = iterate_in_thread(factory)
            async for _ in iterator:  # pragma: no cover - consumption stops at error
                pass

        with self.assertRaises(RuntimeError):
            asyncio.run(consume())


class BaseArchitectStreamingTests(unittest.TestCase):
    def test_stream_analyze_missing_override_raises(self) -> None:
        class DummyArchitect(BaseArchitect):
            async def analyze(self, context, tools=None):
                return {}

            async def create_analysis_plan(self, phase1_results, prompt=None):
                return {}

            async def synthesize_findings(self, phase3_results, prompt=None):
                return {}

            async def final_analysis(self, consolidated_report, prompt=None):
                return {}

            async def consolidate_results(self, all_results, prompt=None):
                return {}

        architect = DummyArchitect(
            provider=ModelProvider.OPENAI,
            model_name="dummy",
            reasoning=ReasoningMode.DISABLED,
        )

        async def consume() -> None:
            async for _ in architect.stream_analyze({}):
                pass

        with self.assertRaises(NotImplementedError):
            asyncio.run(consume())


class ProviderStreamingTests(unittest.TestCase):
    def _assert_stream_chunks(self, chunks: list[StreamChunk]) -> None:
        self.assertEqual(
            [chunk.event_type for chunk in chunks],
            [
                StreamEventType.TEXT_DELTA,
                StreamEventType.TOOL_CALL_DELTA,
                StreamEventType.MESSAGE_END,
            ],
        )
        self.assertEqual(chunks[0].text, "hello")
        self.assertEqual(chunks[1].tool_call, {"id": "call-1"})
        self.assertEqual(chunks[2].finish_reason, "stop")

    def test_openai_stream_analyze_normalizes_events(self) -> None:
        architect = OpenAIArchitect(model_name="o3")
        mock_chunks = iter(
            [
                StreamChunk(StreamEventType.TEXT_DELTA, text="hello"),
                StreamChunk(StreamEventType.TOOL_CALL_DELTA, tool_call={"id": "call-1"}),
                StreamChunk(StreamEventType.MESSAGE_END, finish_reason="stop"),
            ]
        )
        with patch.object(architect, "_stream_dispatch", return_value=mock_chunks):
            events = asyncio.run(
                _collect_async(
                    architect.stream_analyze({"formatted_prompt": "hi"})
                )
            )
        self._assert_stream_chunks(events)

    def test_anthropic_stream_analyze_normalizes_events(self) -> None:
        architect = AnthropicArchitect(model_name="claude-sonnet-4-5")
        mock_chunks = iter(
            [
                StreamChunk(StreamEventType.TEXT_DELTA, text="hello"),
                StreamChunk(StreamEventType.TOOL_CALL_DELTA, tool_call={"id": "call-1"}),
                StreamChunk(StreamEventType.MESSAGE_END, finish_reason="stop"),
            ]
        )
        with patch.object(architect, "_stream_messages", return_value=mock_chunks):
            events = asyncio.run(
                _collect_async(
                    architect.stream_analyze({"formatted_prompt": "hi"})
                )
            )
        self._assert_stream_chunks(events)

    def test_deepseek_stream_analyze_normalizes_events(self) -> None:
        architect = DeepSeekArchitect(model_name="deepseek-chat")
        mock_chunks = iter(
            [
                StreamChunk(StreamEventType.TEXT_DELTA, text="hello"),
                StreamChunk(StreamEventType.TOOL_CALL_DELTA, tool_call={"id": "call-1"}),
                StreamChunk(StreamEventType.MESSAGE_END, finish_reason="stop"),
            ]
        )
        with patch.object(architect, "_stream_dispatch", return_value=mock_chunks):
            events = asyncio.run(
                _collect_async(
                    architect.stream_analyze({"formatted_prompt": "hi"})
                )
            )
        self._assert_stream_chunks(events)

    def test_gemini_stream_analyze_normalizes_events(self) -> None:
        architect = GeminiArchitect(model_name="gemini-2.5-flash")
        architect.client = cast(Any, object())
        mock_chunks = iter(
            [
                StreamChunk(StreamEventType.TEXT_DELTA, text="hello"),
                StreamChunk(StreamEventType.TOOL_CALL_DELTA, tool_call={"id": "call-1"}),
                StreamChunk(StreamEventType.MESSAGE_END, finish_reason="stop"),
            ]
        )
        with patch.object(architect, "_stream_content", return_value=mock_chunks):
            events = asyncio.run(
                _collect_async(
                    architect.stream_analyze({"formatted_prompt": "hi"})
                )
            )
        self._assert_stream_chunks(events)

    def test_xai_stream_analyze_normalizes_events(self) -> None:
        architect = XaiArchitect(model_name="grok-4.3")
        mock_chunks = iter(
            [
                StreamChunk(StreamEventType.TEXT_DELTA, text="hello"),
                StreamChunk(StreamEventType.TOOL_CALL_DELTA, tool_call={"id": "call-1"}),
                StreamChunk(StreamEventType.MESSAGE_END, finish_reason="stop"),
            ]
        )
        with patch.object(architect, "_stream_dispatch", return_value=mock_chunks):
            events = asyncio.run(
                _collect_async(
                    architect.stream_analyze({"formatted_prompt": "hi"})
                )
            )
        self._assert_stream_chunks(events)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
