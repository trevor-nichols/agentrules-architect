"""Client helpers for Gemini interactions."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from google import genai

logger = logging.getLogger("project_extractor")


def build_gemini_client(api_key: str | None) -> tuple[genai.Client | None, str | None]:
    """
    Attempt to build the Gemini client and return the instance plus an error hint.

    Returning the error string instead of raising preserves the legacy behaviour
    where client construction failures are surfaced on first use.
    """
    try:
        client = genai.Client(api_key=api_key) if api_key else genai.Client()
        return client, None
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.debug("Gemini client creation failed", exc_info=exc)
        hint = (
            "Gemini client not initialized. Provide GEMINI_API_KEY or pass api_key "
            "directly to GeminiArchitect."
        )
        return None, hint


async def generate_content_async(
    client: genai.Client,
    *,
    model: str,
    contents: str,
    config: Any | None,
) -> Any:
    """Run ``models.generate_content`` on a thread to avoid blocking the event loop."""
    return await asyncio.to_thread(
        client.models.generate_content,
        model=model,
        contents=contents,
        config=config,
    )
