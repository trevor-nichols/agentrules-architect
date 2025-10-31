"""Model defaults and configuration helpers for the DeepSeek architect."""

from __future__ import annotations

import os
from dataclasses import dataclass

from core.agents.base import ReasoningMode

DEFAULT_BASE_URL = "https://api.deepseek.com"
API_BASE_ENV_VAR = "DEEPSEEK_API_BASE"


@dataclass(frozen=True)
class ModelDefaults:
    """Provider-specific defaults applied when initialising an architect."""

    default_reasoning: ReasoningMode
    max_output_tokens: int | None = None
    tools_allowed: bool = True


_MODEL_DEFAULTS: dict[str, ModelDefaults] = {
    "deepseek-chat": ModelDefaults(
        default_reasoning=ReasoningMode.DISABLED,
        tools_allowed=True,
    ),
    "deepseek-reasoner": ModelDefaults(
        default_reasoning=ReasoningMode.ENABLED,
        max_output_tokens=32_000,
        tools_allowed=False,
    ),
}

_FALLBACK_DEFAULTS = ModelDefaults(
    default_reasoning=ReasoningMode.DISABLED,
    tools_allowed=True,
)


def resolve_model_defaults(model_name: str) -> ModelDefaults:
    """Return the default configuration bundle for the supplied DeepSeek model."""
    normalized = model_name.lower()
    return _MODEL_DEFAULTS.get(normalized, _FALLBACK_DEFAULTS)


def resolve_base_url(explicit_base_url: str | None) -> str:
    """
    Resolve the API base URL for DeepSeek requests.

    Preference order:
    1. Explicit base URL passed to the architect constructor.
    2. Environment variable ``DEEPSEEK_API_BASE``.
    3. Provider default ``https://api.deepseek.com``.
    """
    if explicit_base_url:
        return explicit_base_url
    env_base = os.environ.get(API_BASE_ENV_VAR)
    if env_base:
        return env_base
    return DEFAULT_BASE_URL
