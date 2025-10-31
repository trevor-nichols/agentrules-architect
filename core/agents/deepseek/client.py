"""DeepSeek client helpers implemented on top of the OpenAI SDK."""

from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

from .config import resolve_base_url

_CLIENTS: dict[str, OpenAI | Any] = {}


def _normalise_base_url(base_url: str | None) -> str:
    """Return the canonical base URL key used for client caching."""
    return resolve_base_url(base_url)


def get_client(base_url: str | None = None) -> OpenAI | Any:
    """
    Return a cached OpenAI client configured for the DeepSeek endpoint.

    The DeepSeek API is OpenAI-compatible, so we reuse the OpenAI SDK.
    """
    resolved_base = _normalise_base_url(base_url)
    if resolved_base not in _CLIENTS:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        _CLIENTS[resolved_base] = OpenAI(api_key=api_key, base_url=resolved_base)
    return _CLIENTS[resolved_base]


def set_client(client: Any | None, base_url: str | None = None) -> None:
    """Override or clear the cached client (primarily for tests)."""
    resolved_base = _normalise_base_url(base_url)
    if client is None:
        _CLIENTS.pop(resolved_base, None)
    else:
        _CLIENTS[resolved_base] = client


def execute_chat_completion(payload: dict[str, Any], base_url: str | None = None) -> Any:
    """Execute a Chat Completions request against the DeepSeek endpoint."""
    client = get_client(base_url)
    return client.chat.completions.create(**payload)
