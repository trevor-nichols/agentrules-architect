"""Provider credential helpers."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from agentrules.core.agents.base import ModelProvider

from ..constants import PROVIDER_ENV_MAP
from ..models import CLIConfig, ProviderConfig
from . import codex


def set_provider_key(config: CLIConfig, provider: str, api_key: str | None) -> None:
    config.providers[provider] = ProviderConfig(api_key=api_key)


def current_provider_keys(config: CLIConfig) -> dict[str, str | None]:
    return {
        provider: config.providers.get(provider, ProviderConfig()).api_key
        for provider in PROVIDER_ENV_MAP
    }


def is_model_provider_available(
    config: CLIConfig,
    provider_slug: str,
    getenv: Callable[[str], str | None],
) -> bool:
    if provider_slug == ModelProvider.CODEX.value:
        return codex.is_codex_available(config)

    stored = config.providers.get(provider_slug)
    if stored and stored.api_key:
        return True

    env_var = PROVIDER_ENV_MAP.get(provider_slug)
    return bool(env_var and getenv(env_var))


def current_provider_availability(
    config: CLIConfig,
    getenv: Callable[[str], str | None],
    *,
    provider_slugs: Iterable[str] | None = None,
) -> dict[str, bool]:
    slugs = provider_slugs or (provider.value for provider in ModelProvider)
    return {
        provider_slug: is_model_provider_available(config, provider_slug, getenv)
        for provider_slug in slugs
    }


def has_tavily_credentials(config: CLIConfig, getenv: Callable[[str], str | None]) -> bool:
    stored = config.providers.get("tavily")
    if stored and stored.api_key:
        return True
    env_var = PROVIDER_ENV_MAP.get("tavily")
    return bool(env_var and getenv(env_var))
