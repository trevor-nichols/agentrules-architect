"""
Logging utilities for agentrules.

Provides a small facade so callers can import ``configure_logging`` from
``agentrules.core.logging`` without depending on the underlying module layout.
"""

from __future__ import annotations

from .config import configure_logging

__all__ = ["configure_logging"]

