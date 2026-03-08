"""Shared provider capability helpers for pipeline branching."""

from __future__ import annotations

from typing import Any

from agentrules.core.agents.base import ModelProvider


def resolve_provider(subject: Any) -> ModelProvider | None:
    """Resolve a provider from a provider enum, model config, architect, or preset info."""

    if isinstance(subject, ModelProvider):
        return subject

    provider = getattr(subject, "provider", None)
    if isinstance(provider, ModelProvider):
        return provider

    model_config = getattr(subject, "_model_config", None) or getattr(subject, "model_config", None)
    provider = getattr(model_config, "provider", None)
    if isinstance(provider, ModelProvider):
        return provider

    return None


def uses_repo_runtime(subject: Any) -> bool:
    """Return whether the provider runs against a repository-aware runtime."""

    return resolve_provider(subject) == ModelProvider.CODEX


def uses_runtime_native_web_search(subject: Any) -> bool:
    """Return whether the provider ships its own runtime-managed web search."""

    return uses_repo_runtime(subject)


def requires_external_research_tool_loop(subject: Any) -> bool:
    """Return whether Phase 1 must manage an external Tavily tool loop."""

    return not uses_runtime_native_web_search(subject)


def should_embed_phase3_file_contents(subject: Any) -> bool:
    """Return whether Phase 3 should inline file contents into the prompt."""

    return not uses_repo_runtime(subject)
