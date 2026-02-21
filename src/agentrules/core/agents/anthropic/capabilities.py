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


def supports_structured_output_format(model_name: str) -> bool:
    """
    Return True when the model supports `output_config.format` JSON schema outputs.

    Based on provider integration guidance, structured JSON outputs are available on
    Claude Sonnet 4.5/4.6, Claude Opus 4.5/4.6, and Claude Haiku 4.5 families.
    """
    normalized = normalize_model_name(model_name)
    return (
        normalized == "claude-sonnet-4-6"
        or normalized.startswith("claude-sonnet-4-6-")
        or normalized == "claude-sonnet-4-5"
        or normalized.startswith("claude-sonnet-4-5-")
        or normalized == "claude-opus-4-6"
        or normalized.startswith("claude-opus-4-6-")
        or normalized == "claude-opus-4-5"
        or normalized.startswith("claude-opus-4-5-")
        or normalized == "claude-haiku-4-5"
        or normalized.startswith("claude-haiku-4-5-")
    )
