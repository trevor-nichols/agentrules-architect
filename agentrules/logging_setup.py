"""
agentrules.logging_setup

Utilities for configuring Rich-based logging consistently across the CLI.
"""

from __future__ import annotations

import logging
from typing import Iterable

from rich.logging import RichHandler


class HTTPRequestFilter(logging.Filter):
    """Filters verbose HTTP request logs from provider SDKs."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        if "HTTP Request:" not in message:
            return True

        if "api.openai.com" in message:
            record.msg = "Using OpenAI model"
            return True
        if "api.anthropic.com" in message:
            record.msg = "Using Anthropic model"
            return True
        if "generativelanguage.googleapis.com" in message:
            record.msg = "Using Google Gemini model"
            return True
        if "api.deepseek.com" in message:
            record.msg = "Using DeepSeek model"
            return True
        return False


def configure_logging(
    *,
    level: int = logging.INFO,
    filtered_loggers: Iterable[str] | None = None,
) -> logging.Logger:
    """
    Configure the Rich logging handler and return the project logger.

    Subsequent calls become no-ops because logging.basicConfig only applies once.
    """
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True, show_time=False, markup=True)],
    )

    project_logger = logging.getLogger("project_extractor")
    if not any(isinstance(f, HTTPRequestFilter) for f in project_logger.filters):
        project_logger.addFilter(HTTPRequestFilter())

    for name in filtered_loggers or ("openai", "httpx", "httpcore", "anthropic", "google", "genai"):
        logging.getLogger(name).setLevel(logging.WARNING)

    return project_logger

