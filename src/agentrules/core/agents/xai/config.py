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
    accepted_reasoning_efforts: frozenset[str] = frozenset()
    enabled_reasoning_effort: str | None = None
    normalize_higher_efforts_to_high: bool = False
    fixed_reasoning_mode: ReasoningMode | None = None


_LEGACY_ACCEPTED_REASONING_EFFORTS = frozenset({"none", "minimal", "low", "medium", "high"})


_MODEL_DEFAULTS: dict[str, ModelDefaults] = {
    "grok-4.5": ModelDefaults(
        default_reasoning=ReasoningMode.HIGH,
        accepted_reasoning_efforts=frozenset({"low", "medium", "high"}),
        enabled_reasoning_effort="high",
    ),
    "grok-4.20-0309-reasoning": ModelDefaults(
        default_reasoning=ReasoningMode.ENABLED,
        fixed_reasoning_mode=ReasoningMode.ENABLED,
    ),
    "grok-4.20-0309-non-reasoning": ModelDefaults(
        default_reasoning=ReasoningMode.DISABLED,
        fixed_reasoning_mode=ReasoningMode.DISABLED,
    ),
    "grok-4.3": ModelDefaults(
        default_reasoning=ReasoningMode.LOW,
        accepted_reasoning_efforts=_LEGACY_ACCEPTED_REASONING_EFFORTS,
        enabled_reasoning_effort="medium",
        normalize_higher_efforts_to_high=True,
    ),
    # Grok Build reasons by default, but the chat-completions API rejects the
    # explicit reasoning_effort parameter for this model family.
    "grok-build-0.1": ModelDefaults(
        default_reasoning=ReasoningMode.ENABLED,
    ),
    # Legacy alias retained for backwards compatibility with grok-build-0.1.
    "grok-code-fast-1": ModelDefaults(
        default_reasoning=ReasoningMode.ENABLED,
    ),
    "grok-4-1-fast-reasoning": ModelDefaults(
        default_reasoning=ReasoningMode.ENABLED,
        accepted_reasoning_efforts=_LEGACY_ACCEPTED_REASONING_EFFORTS,
        enabled_reasoning_effort="medium",
        normalize_higher_efforts_to_high=True,
    ),
    # Legacy alias retained for backwards compatibility with Grok 4.3.
    "grok-4-1-fast-non-reasoning": ModelDefaults(
        default_reasoning=ReasoningMode.DISABLED,
        accepted_reasoning_efforts=_LEGACY_ACCEPTED_REASONING_EFFORTS,
        enabled_reasoning_effort="medium",
        normalize_higher_efforts_to_high=True,
    ),
    "grok-4-fast-reasoning": ModelDefaults(
        default_reasoning=ReasoningMode.ENABLED,
        accepted_reasoning_efforts=_LEGACY_ACCEPTED_REASONING_EFFORTS,
        enabled_reasoning_effort="medium",
        normalize_higher_efforts_to_high=True,
    ),
    # Legacy alias retained for backwards compatibility with Grok 4.3.
    "grok-4-fast-non-reasoning": ModelDefaults(
        default_reasoning=ReasoningMode.DISABLED,
        accepted_reasoning_efforts=_LEGACY_ACCEPTED_REASONING_EFFORTS,
        enabled_reasoning_effort="medium",
        normalize_higher_efforts_to_high=True,
    ),
    # Legacy alias retained for backwards compatibility with Grok 4.3.
    "grok-4-0709": ModelDefaults(
        default_reasoning=ReasoningMode.MEDIUM,
        accepted_reasoning_efforts=_LEGACY_ACCEPTED_REASONING_EFFORTS,
        enabled_reasoning_effort="medium",
        normalize_higher_efforts_to_high=True,
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
