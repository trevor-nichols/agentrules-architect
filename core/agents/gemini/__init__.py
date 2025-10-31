"""
Provider-specific Gemini package.

This module exposes the public architect surface while maintaining backwards
compatibility with existing imports that expect ``core.agents.gemini`` to
export the Google SDK symbols.
"""

from __future__ import annotations

from google import genai  # Re-exported for tests that monkeypatch the client.

from .architect import GeminiArchitect
from .legacy import GeminiAgent

__all__ = ["GeminiArchitect", "GeminiAgent", "genai"]

# Backwards-compatibility shims ------------------------------------------------
# Historical tests reach into this module for asyncio to drive the event loop.
# Import lazily so we only pay the cost when the attribute is accessed.

import asyncio as _asyncio  # noqa: E402  (deferred import above)

asyncio = _asyncio

