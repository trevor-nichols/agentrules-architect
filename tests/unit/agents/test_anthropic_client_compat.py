from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from agentrules.core.agents.anthropic.architect import AnthropicArchitect
from agentrules.core.agents.anthropic.client import execute_message_request, execute_message_stream, set_client
from agentrules.core.agents.anthropic.request_builder import PreparedRequest
from agentrules.core.agents.anthropic.response_parser import AnthropicRefusalError
from agentrules.core.agents.base import ReasoningMode
from agentrules.core.streaming import StreamEventType


class _EventStream:
    def __init__(self, events: tuple[Any, ...]) -> None:
        self._events = events

    def __enter__(self) -> _EventStream:
        return self

    def __exit__(self, exc_type, exc, tb):  # type: ignore[no-untyped-def]
        return None

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self._events)

    def get_final_message(self):  # pragma: no cover
        raise AssertionError("not used by event-stream tests")


class _EventMessages:
    def __init__(self, events: tuple[Any, ...]) -> None:
        self._events = events

    def stream(self, **_kwargs):  # type: ignore[no-untyped-def]
        return _EventStream(self._events)


class _EventClient:
    def __init__(self, *events: Any) -> None:
        self.messages = _EventMessages(events)


def test_execute_message_request_moves_output_config_to_extra_body() -> None:
    captured: dict[str, Any] = {}

    class FakeMessages:
        def create(self, **kwargs):  # type: ignore[no-untyped-def]
            captured["kwargs"] = kwargs
            return {"ok": True}

    class FakeClient:
        messages = FakeMessages()

    set_client(FakeClient())
    try:
        payload = {
            "model": "claude-opus-4-6",
            "max_tokens": 1,
            "messages": [{"role": "user", "content": "hi"}],
            "output_config": {"effort": "low"},
        }
        execute_message_request(payload)

        kwargs = captured.get("kwargs")
        assert isinstance(kwargs, dict)
        assert "output_config" not in kwargs
        assert kwargs.get("extra_body") == {"output_config": {"effort": "low"}}
    finally:
        set_client(None)


def test_execute_message_stream_moves_output_config_to_extra_body() -> None:
    captured: dict[str, Any] = {}

    class FakeStream:
        def __enter__(self):  # type: ignore[no-untyped-def]
            return self

        def __exit__(self, exc_type, exc, tb):  # type: ignore[no-untyped-def]
            return None

        def __iter__(self):  # type: ignore[no-untyped-def]
            return iter(())

        def get_final_message(self):  # pragma: no cover
            raise AssertionError("not used in this test")

    class FakeMessages:
        def stream(self, **kwargs):  # type: ignore[no-untyped-def]
            captured["kwargs"] = kwargs
            return FakeStream()

    class FakeClient:
        messages = FakeMessages()

    set_client(FakeClient())
    try:
        payload = {
            "model": "claude-opus-4-6",
            "max_tokens": 1,
            "messages": [{"role": "user", "content": "hi"}],
            "output_config": {"effort": "medium"},
        }
        with execute_message_stream(payload):
            pass

        kwargs = captured.get("kwargs")
        assert isinstance(kwargs, dict)
        assert "output_config" not in kwargs
        assert kwargs.get("extra_body") == {"output_config": {"effort": "medium"}}
        assert "stream" not in kwargs  # `.stream()` does not accept stream=True
    finally:
        set_client(None)


def test_anthropic_architect_stream_does_not_pass_output_config_kwarg() -> None:
    captured: dict[str, Any] = {}

    class FakeStream:
        def __enter__(self):  # type: ignore[no-untyped-def]
            return self

        def __exit__(self, exc_type, exc, tb):  # type: ignore[no-untyped-def]
            return None

        def __iter__(self):  # type: ignore[no-untyped-def]
            return iter(())

        def get_final_message(self):  # pragma: no cover
            raise AssertionError("not used in this test")

    class FakeMessages:
        def stream(self, **kwargs):  # type: ignore[no-untyped-def]
            captured["kwargs"] = kwargs
            return FakeStream()

    class FakeClient:
        messages = FakeMessages()

    set_client(FakeClient())
    try:
        arch = AnthropicArchitect(
            model_name="claude-opus-4-6",
            reasoning=ReasoningMode.DYNAMIC,
            model_config=None,
        )
        prepared = PreparedRequest(
            payload={
                "model": "claude-opus-4-6",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "hi"}],
                "output_config": {"effort": "low"},
            }
        )
        list(arch._stream_messages(prepared))

        kwargs = captured.get("kwargs")
        assert isinstance(kwargs, dict)
        assert "output_config" not in kwargs
        assert kwargs.get("extra_body") == {"output_config": {"effort": "low"}}
        assert "stream" not in kwargs
    finally:
        set_client(None)


def test_anthropic_stream_raises_for_refusal_message_delta() -> None:
    refusal_event = SimpleNamespace(
        type="message_delta",
        delta=SimpleNamespace(
            stop_reason="refusal",
            stop_details=SimpleNamespace(
                category="cyber",
                explanation="Request declined.",
            ),
            usage=None,
        ),
    )

    set_client(_EventClient(refusal_event))
    try:
        arch = AnthropicArchitect(model_name="claude-fable-5", reasoning=ReasoningMode.DYNAMIC)
        prepared = PreparedRequest(
            payload={
                "model": "claude-fable-5",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "hi"}],
            }
        )

        with pytest.raises(AnthropicRefusalError, match="category: cyber"):
            list(arch._stream_messages(prepared))
    finally:
        set_client(None)


def test_anthropic_stream_does_not_expose_partial_refusal_content() -> None:
    text_event = SimpleNamespace(
        type="content_block_delta",
        index=0,
        delta=SimpleNamespace(type="text_delta", text="partial refused output"),
    )
    refusal_event = SimpleNamespace(
        type="message_delta",
        delta=SimpleNamespace(
            stop_reason="refusal",
            stop_details=SimpleNamespace(category="cyber", explanation="Request declined."),
            usage=None,
        ),
    )

    set_client(_EventClient(text_event, refusal_event))
    try:
        arch = AnthropicArchitect(model_name="claude-fable-5", reasoning=ReasoningMode.DYNAMIC)
        prepared = PreparedRequest(
            payload={
                "model": "claude-fable-5",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "hi"}],
            }
        )

        stream = arch._stream_messages(prepared)
        with pytest.raises(AnthropicRefusalError, match="category: cyber"):
            next(stream)
    finally:
        set_client(None)


def test_anthropic_stream_yields_immediately_without_partial_refusal_capability() -> None:
    text_event = SimpleNamespace(
        type="content_block_delta",
        index=0,
        delta=SimpleNamespace(type="text_delta", text="incremental output"),
    )
    error_event = SimpleNamespace(
        type="error",
        error=SimpleNamespace(message="later stream error"),
    )

    set_client(_EventClient(text_event, error_event))
    try:
        arch = AnthropicArchitect(model_name="claude-sonnet-5", reasoning=ReasoningMode.DYNAMIC)
        prepared = PreparedRequest(
            payload={
                "model": "claude-sonnet-5",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "hi"}],
            }
        )

        stream = arch._stream_messages(prepared)
        first_chunk = next(stream)

        assert first_chunk.event_type == StreamEventType.TEXT_DELTA
        assert first_chunk.text == "incremental output"
    finally:
        set_client(None)


def test_anthropic_stream_releases_content_after_terminal_stop_reason() -> None:
    text_event = SimpleNamespace(
        type="content_block_delta",
        index=0,
        delta=SimpleNamespace(type="text_delta", text="accepted output"),
    )
    message_delta_event = SimpleNamespace(
        type="message_delta",
        delta=SimpleNamespace(
            stop_reason="end_turn",
            stop_details=None,
            usage=SimpleNamespace(output_tokens=2),
        ),
    )
    final_message = SimpleNamespace(
        stop_reason="end_turn",
        stop_details=None,
        usage=SimpleNamespace(output_tokens=2),
    )
    message_stop_event = SimpleNamespace(type="message_stop", message=final_message)

    set_client(_EventClient(text_event, message_delta_event, message_stop_event))
    try:
        arch = AnthropicArchitect(model_name="claude-fable-5", reasoning=ReasoningMode.DYNAMIC)
        prepared = PreparedRequest(
            payload={
                "model": "claude-fable-5",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "hi"}],
            }
        )

        chunks = list(arch._stream_messages(prepared))

        assert [chunk.event_type for chunk in chunks] == [
            StreamEventType.TEXT_DELTA,
            StreamEventType.MESSAGE_DELTA,
            StreamEventType.MESSAGE_END,
        ]
        assert chunks[0].text == "accepted output"
    finally:
        set_client(None)
