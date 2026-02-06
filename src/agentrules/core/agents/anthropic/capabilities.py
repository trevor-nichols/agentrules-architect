"""Anthropic Claude model capability helpers.

Centralize provider-specific capability checks (effort/adaptive thinking) so we
don't duplicate allowlists across request builders and architects.
"""

from __future__ import annotations


def normalize_model_name(model_name: str) -> str:
    return model_name.strip().lower()


def supports_adaptive_thinking(model_name: str) -> bool:
    """Return True when the model supports thinking.type='adaptive'."""
    normalized = normalize_model_name(model_name)
    return normalized == "claude-opus-4-6" or normalized.startswith("claude-opus-4-6-")


def supports_effort(model_name: str) -> bool:
    """Return True when the model supports output_config.effort."""
    normalized = normalize_model_name(model_name)
    return (
        normalized == "claude-opus-4-6"
        or normalized.startswith("claude-opus-4-6-")
        or normalized == "claude-opus-4-5"
        or normalized.startswith("claude-opus-4-5-")
    )


def supports_max_effort(model_name: str) -> bool:
    """Return True when effort='max' is allowed (Opus 4.6 only)."""
    return supports_adaptive_thinking(model_name)

