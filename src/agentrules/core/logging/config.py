"""Rich logging configuration helpers for agentrules."""

from __future__ import annotations

import logging
from collections.abc import Iterable

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


class VendorNoiseFilter(logging.Filter):
    """Suppress known noisy warnings from third-party SDKs."""

    NOISY_SNIPPETS = (
        "Warning: there are non-text parts in the response",
        "Both GOOGLE_API_KEY and GEMINI_API_KEY are set.",
    )

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return not any(snippet in message for snippet in self.NOISY_SNIPPETS)


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
    if not any(isinstance(f, VendorNoiseFilter) for f in project_logger.filters):
        project_logger.addFilter(VendorNoiseFilter())

    root_logger = logging.getLogger()
    if not any(isinstance(f, VendorNoiseFilter) for f in root_logger.filters):
        root_logger.addFilter(VendorNoiseFilter())

    for name in filtered_loggers or ("openai", "httpx", "httpcore", "anthropic", "google", "genai"):
        logging.getLogger(name).setLevel(logging.WARNING)

    return project_logger
