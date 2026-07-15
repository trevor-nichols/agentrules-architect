from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from agentrules.core.agents.anthropic.architect import AnthropicArchitect
from agentrules.core.agents.anthropic.client import execute_message_request, execute_message_stream, set_client
from agentrules.core.agents.anthropic.request_builder import PreparedRequest
from agentrules.core.agents.anthropic.response_parser import AnthropicRefusalError
from agentrules.core.agents.base import ReasoningMode


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

    class FakeStream:
        def __enter__(self):  # type: ignore[no-untyped-def]
            return self

        def __exit__(self, exc_type, exc, tb):  # type: ignore[no-untyped-def]
            return None

        def __iter__(self):  # type: ignore[no-untyped-def]
            return iter((refusal_event,))

        def get_final_message(self):  # pragma: no cover
            raise AssertionError("not used in this test")

    class FakeMessages:
        def stream(self, **_kwargs):  # type: ignore[no-untyped-def]
            return FakeStream()

    class FakeClient:
        messages = FakeMessages()

    set_client(FakeClient())
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
