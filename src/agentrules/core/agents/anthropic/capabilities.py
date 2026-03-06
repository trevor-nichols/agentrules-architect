"""Anthropic Claude model capability helpers.

Centralize provider capability metadata so new Claude families can be added by
describing their supported features instead of scattering string checks across
the request builders.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from agentrules.core.types.models import AnthropicEffort


@dataclass(frozen=True)
class CapabilityProfile:
    """Capability metadata for a Claude model family."""

    family_prefix: str
    display_name: str
    supports_structured_output_format: bool = False
    supports_adaptive_thinking: bool = False
    supported_effort_levels: frozenset[AnthropicEffort] = frozenset()

    def matches(self, model_name: str) -> bool:
        normalized = normalize_model_name(model_name)
        return normalized == self.family_prefix or normalized.startswith(f"{self.family_prefix}-")


_DEFAULT_PROFILE = CapabilityProfile(
    family_prefix="",
    display_name="Unknown Claude family",
)

_CAPABILITY_PROFILES: tuple[CapabilityProfile, ...] = (
    CapabilityProfile(
        family_prefix="claude-sonnet-4-6",
        display_name="Claude Sonnet 4.6",
        supports_structured_output_format=True,
        supports_adaptive_thinking=True,
        supported_effort_levels=frozenset({"low", "medium", "high"}),
    ),
    CapabilityProfile(
        family_prefix="claude-sonnet-4-5",
        display_name="Claude Sonnet 4.5",
        supports_structured_output_format=True,
    ),
    CapabilityProfile(
        family_prefix="claude-haiku-4-5",
        display_name="Claude Haiku 4.5",
        supports_structured_output_format=True,
    ),
    CapabilityProfile(
        family_prefix="claude-opus-4-6",
        display_name="Claude Opus 4.6",
        supports_structured_output_format=True,
        supports_adaptive_thinking=True,
        supported_effort_levels=frozenset({"low", "medium", "high", "max"}),
    ),
    CapabilityProfile(
        family_prefix="claude-opus-4-5",
        display_name="Claude Opus 4.5",
        supports_structured_output_format=True,
        supported_effort_levels=frozenset({"low", "medium", "high"}),
    ),
)


def normalize_model_name(model_name: str) -> str:
    return model_name.strip().lower()


def resolve_capability_profile(model_name: str) -> CapabilityProfile:
    """Return the capability profile for the supplied Claude model family."""

    for profile in _CAPABILITY_PROFILES:
        if profile.matches(model_name):
            return profile
    return _DEFAULT_PROFILE


def supports_adaptive_thinking(model_name: str) -> bool:
    """Return True when the model supports thinking.type='adaptive'."""

    return resolve_capability_profile(model_name).supports_adaptive_thinking


def supported_effort_levels(model_name: str) -> frozenset[AnthropicEffort]:
    """Return the supported output_config.effort levels for the model."""

    return resolve_capability_profile(model_name).supported_effort_levels


def supports_effort(model_name: str) -> bool:
    """Return True when the model supports output_config.effort."""

    return bool(supported_effort_levels(model_name))


def supports_max_effort(model_name: str) -> bool:
    """Return True when effort='max' is allowed."""

    return "max" in supported_effort_levels(model_name)


def supports_structured_output_format(model_name: str) -> bool:
    """Return True when the model supports output_config.format JSON schemas."""

    return resolve_capability_profile(model_name).supports_structured_output_format


def describe_profiles_with_adaptive_thinking() -> str:
    """Return a human-readable list of model families that support adaptive thinking."""

    return _describe_profiles(
        profile for profile in _CAPABILITY_PROFILES if profile.supports_adaptive_thinking
    )


def describe_profiles_with_effort() -> str:
    """Return a human-readable list of model families that support effort selection."""

    return _describe_profiles(
        profile for profile in _CAPABILITY_PROFILES if profile.supported_effort_levels
    )


def _describe_profiles(profiles: Iterable[CapabilityProfile]) -> str:
    labels = [profile.display_name for profile in profiles]
    if not labels:
        return "no Claude families"
    if len(labels) == 1:
        return labels[0]
    return ", ".join(labels[:-1]) + f", and {labels[-1]}"
