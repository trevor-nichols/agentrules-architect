"""Client helpers for Gemini interactions."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from google import genai
from google.genai import types

logger = logging.getLogger("project_extractor")


def build_gemini_client(api_key: str | None) -> tuple[genai.Client | None, str | None]:
    """
    Attempt to build the Gemini client and return the instance plus an error hint.

    Returning the error string instead of raising preserves the legacy behaviour
    where client construction failures are surfaced on first use.
    """
    # The SDK gives Enterprise precedence over the older Vertex AI flag.
    managed_flag = os.getenv("GOOGLE_GENAI_USE_ENTERPRISE", os.getenv("GOOGLE_GENAI_USE_VERTEXAI", ""))
    http_options = None
    if managed_flag.lower() not in ("true", "1") and not os.getenv("GOOGLE_GENAI_API_VERSION"):
        # Keep Developer API preview IDs available under the SDK 3 default of v1.
        http_options = types.HttpOptions(api_version="v1beta")

    try:
        client = genai.Client(api_key=api_key, http_options=http_options)
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
    contents: Any,
    config: Any | None,
) -> Any:
    """Run ``models.generate_content`` on a thread to avoid blocking the event loop."""
    return await asyncio.to_thread(
        client.models.generate_content,
        model=model,
        contents=contents,
        config=config,
    )
