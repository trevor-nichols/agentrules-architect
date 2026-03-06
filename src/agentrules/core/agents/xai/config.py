"""Model defaults and configuration helpers for the xAI architect."""

from __future__ import annotations

import os
from dataclasses import dataclass

from agentrules.core.agents.base import ReasoningMode

DEFAULT_BASE_URL = "https://api.x.ai/v1"
API_BASE_ENV_VAR = "XAI_API_BASE"


@dataclass(frozen=True)
class ModelDefaults:
    """Provider-specific defaults applied when initialising an xAI architect."""

    default_reasoning: ReasoningMode
    tools_allowed: bool = True
    reasoning_effort_supported: bool = False


_MODEL_DEFAULTS: dict[str, ModelDefaults] = {
    "grok-code-fast-1": ModelDefaults(
        default_reasoning=ReasoningMode.ENABLED,
        reasoning_effort_supported=True,
    ),
    "grok-4-1-fast-reasoning": ModelDefaults(
        default_reasoning=ReasoningMode.ENABLED,
        reasoning_effort_supported=True,
    ),
    "grok-4-1-fast-non-reasoning": ModelDefaults(
        default_reasoning=ReasoningMode.DISABLED,
        reasoning_effort_supported=False,
    ),
    "grok-4-fast-reasoning": ModelDefaults(
        default_reasoning=ReasoningMode.ENABLED,
        reasoning_effort_supported=True,
    ),
    "grok-4-fast-non-reasoning": ModelDefaults(
        default_reasoning=ReasoningMode.DISABLED,
        reasoning_effort_supported=False,
    ),
    "grok-4-0709": ModelDefaults(
        default_reasoning=ReasoningMode.ENABLED,
        reasoning_effort_supported=False,
    ),
}

_FALLBACK_DEFAULTS = ModelDefaults(default_reasoning=ReasoningMode.DISABLED)


def resolve_model_defaults(model_name: str) -> ModelDefaults:
    """Return the default configuration bundle for the supplied xAI model."""
    normalized = model_name.lower()
    return _MODEL_DEFAULTS.get(normalized, _FALLBACK_DEFAULTS)


def resolve_base_url(explicit_base_url: str | None) -> str:
    """
    Resolve the API base URL for Grok requests.

    Preference order:
    1. Explicit base URL passed to the architect constructor.
    2. Environment variable ``XAI_API_BASE``.
    3. Provider default ``https://api.x.ai/v1``.
    """
    if explicit_base_url:
        return explicit_base_url
    env_base = os.environ.get(API_BASE_ENV_VAR)
    if env_base:
        return env_base
    return DEFAULT_BASE_URL
