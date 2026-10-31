"""Shared OpenAI client instance and helpers for issuing requests."""
from __future__ import annotations

from typing import Any

from openai import OpenAI

from .request_builder import PreparedRequest

_client: OpenAI | None = None


def set_client(client: OpenAI | None) -> None:
    """Inject a client for offline provider contract tests."""
    global _client
    _client = client


def get_client() -> OpenAI:
    """Return a cached OpenAI SDK client."""
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def execute_request(prepared: PreparedRequest) -> Any:
    """Dispatch the prepared request to the appropriate OpenAI endpoint."""
    client = get_client()

    if prepared.api == "responses":
        return client.responses.create(**prepared.payload)

    return client.chat.completions.create(**prepared.payload)
