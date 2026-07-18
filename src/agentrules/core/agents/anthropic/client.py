"""Anthropic SDK client helpers."""
from __future__ import annotations

from typing import Any

from anthropic import Anthropic

from .request_builder import DEFAULT_NONSTREAMING_MAX_TOKENS

_client: Anthropic | Any | None = None


def get_client() -> Any:
    """Return a cached Anthropic SDK client instance."""
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


def set_client(client: Any | None) -> None:
    """Override the cached client, primarily for tests."""
    global _client
    _client = client


def _coerce_sdk_kwargs(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Translate our provider payload into kwargs accepted by the installed SDK.

    Anthropic's Python SDKs often add new request fields via `extra_body` before
    promoting them to first-class kwargs. Keep our payload shape provider-native
    (e.g., `output_config` at top-level), but send via extra_body for compatibility.
    """
    kwargs: dict[str, Any] = dict(payload)

    output_config = kwargs.pop("output_config", None)
    if output_config is not None:
        extra_body = kwargs.get("extra_body")
        if extra_body is None:
            extra_body_dict: dict[str, Any] = {}
        elif isinstance(extra_body, dict):
            extra_body_dict = dict(extra_body)
        else:  # pragma: no cover - defensive
            raise TypeError(f"extra_body must be a dict when provided, got {type(extra_body)!r}")
        extra_body_dict["output_config"] = output_config
        kwargs["extra_body"] = extra_body_dict

    return kwargs


def execute_message_request(payload: dict[str, Any]) -> Any:
    """Execute a Claude Messages API call with the provided payload."""
    client = get_client()
    kwargs = _coerce_sdk_kwargs(payload)
    if kwargs["max_tokens"] > DEFAULT_NONSTREAMING_MAX_TOKENS:
        # Anthropic rejects long non-streaming requests under the SDK's default
        # timeout. Accumulate the stream so callers still receive one Message.
        with client.messages.stream(**kwargs) as stream:
            return stream.get_final_message()
    return client.messages.create(**kwargs)


def execute_message_stream(payload: dict[str, Any]) -> Any:
    """Execute a Claude Messages API streaming call with the provided payload."""
    client = get_client()
    return client.messages.stream(**_coerce_sdk_kwargs(payload))
