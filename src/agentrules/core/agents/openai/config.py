"""Model defaults and configuration helpers for the OpenAI architect."""

from __future__ import annotations

from dataclasses import dataclass

from agentrules.core.agents.base import ReasoningMode


@dataclass(frozen=True)
class ModelDefaults:
    """Configuration bundle describing how to talk to a given OpenAI model."""

    default_reasoning: ReasoningMode
    default_temperature: float | None = None
    use_responses_api: bool = False


_MODEL_DEFAULTS: dict[str, ModelDefaults] = {
    "o3": ModelDefaults(default_reasoning=ReasoningMode.HIGH),
    "o4-mini": ModelDefaults(default_reasoning=ReasoningMode.HIGH),
    "gpt-4.1": ModelDefaults(
        default_reasoning=ReasoningMode.TEMPERATURE,
        default_temperature=0.7,
    ),
}

_GPT5_RESPONSES_DEFAULTS = ModelDefaults(
    default_reasoning=ReasoningMode.MEDIUM,
    use_responses_api=True,
)

_PREFIX_DEFAULTS: tuple[tuple[str, ModelDefaults], ...] = (
    ("gpt-5.2", _GPT5_RESPONSES_DEFAULTS),
    ("gpt-5.1", _GPT5_RESPONSES_DEFAULTS),
    ("gpt-5", _GPT5_RESPONSES_DEFAULTS),
)

_FALLBACK_DEFAULTS = ModelDefaults(default_reasoning=ReasoningMode.DISABLED)


def resolve_model_defaults(model_name: str) -> ModelDefaults:
    """Return the defaults to apply for the supplied model name."""
    normalized = model_name.lower()

    if normalized in _MODEL_DEFAULTS:
        return _MODEL_DEFAULTS[normalized]

    for prefix, defaults in _PREFIX_DEFAULTS:
        if normalized.startswith(prefix):
            return defaults

    return _FALLBACK_DEFAULTS


def should_use_responses_api(model_name: str) -> bool:
    """Indicate whether the Responses API should be used for the model."""
    return resolve_model_defaults(model_name).use_responses_api
