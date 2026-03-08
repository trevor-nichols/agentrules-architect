"""Feature toggle helpers."""

from __future__ import annotations

from ..models import CLIConfig, ResearcherMode
from ..utils import normalize_researcher_mode


def set_researcher_mode(config: CLIConfig, mode: str | None) -> None:
    config.features.researcher_mode = normalize_researcher_mode(mode, default="off")


def get_researcher_mode(config: CLIConfig, default: ResearcherMode = "off") -> ResearcherMode:
    normalized = normalize_researcher_mode(config.features.researcher_mode, default=default)
    config.features.researcher_mode = normalized
    return normalized


def is_researcher_enabled(
    config: CLIConfig,
    *,
    offline_mode: bool,
    has_tavily_credentials: bool,
    supports_runtime_native_research: bool = False,
) -> bool:
    mode = normalize_researcher_mode(config.features.researcher_mode, default="off")

    if mode != "on":
        return False
    if offline_mode or supports_runtime_native_research:
        return True
    return has_tavily_credentials
