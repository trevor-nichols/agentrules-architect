"""Shared styling helpers for Questionary prompts."""

from __future__ import annotations

from typing import Any

import questionary
from questionary import Style

_PROVIDER_BADGES: dict[str, str] = {
    "codex": "CX",
    "xai": "XA",
    "deepseek": "DS",
    "openai": "OA",
    "anthropic": "AN",
    "gemini": "GM",
}

# Central style for all CLI Questionary prompts. Keeps the pointer and highlights
# branded while dimming navigation actions like "Back" and "Done".
CLI_STYLE = Style(
    [
        ("qmark", "fg:#00d1b2 bold"),
        ("question", "bold"),
        ("answer", "fg:#00d1b2 bold"),
        ("pointer", "fg:#00d1b2 bold"),
        ("highlighted", "fg:#00d1b2 bold"),
        ("selected", "fg:#00d1b2"),
        ("instruction", ""),
        ("text", ""),
        ("navigation", "fg:#888888 italic"),
        ("status.enabled", "fg:#00d1b2 bold"),
        ("status.disabled", "fg:#ff5f5f bold"),
        ("status.separator", "fg:#444444"),
        ("status.bracket", "fg:#666666"),
        ("status.value", "fg:#00d1b2"),
        ("status.model", "fg:#00d1b2 bold"),
        ("status.provider", "fg:#888888"),
        ("status.variant", "fg:#00d1b2"),
        ("provider.codex", "fg:#f97316 bold"),
        ("provider.xai", "fg:#ef4444 bold"),
        ("provider.deepseek", "fg:#14b8a6 bold"),
        ("provider.openai", "fg:#10a37f bold"),
        ("provider.anthropic", "fg:#d97706 bold"),
        ("provider.gemini", "fg:#4285f4 bold"),
        ("provider.unknown", "fg:#888888 bold"),
    ]
)


def navigation_choice(label: str, *, value: Any) -> questionary.Choice:
    """Return a dimmed navigation choice (e.g. Back, Done)."""

    tokens: list[tuple[str, str]] = [("class:navigation", label)]
    return questionary.Choice(tokens, value=value)


def toggle_choice(label: str, enabled: bool, *, value: Any) -> questionary.Choice:
    """Return a choice with a color-coded ON/OFF status badge."""

    status_class = "status.enabled" if enabled else "status.disabled"
    status_text = "ON" if enabled else "OFF"
    tokens: list[tuple[str, str]] = [
        ("class:text", label),
        ("class:status.separator", "  "),
        ("class:status.bracket", "["),
        (f"class:{status_class}", status_text),
        ("class:status.bracket", "]"),
    ]
    return questionary.Choice(tokens, value=value)


def value_choice(label: str, value_text: str, *, value: Any) -> questionary.Choice:
    """Return a choice showing the current value in accent color."""

    tokens: list[tuple[str, str]] = [
        ("class:text", label),
        ("class:status.separator", "  "),
        ("class:status.bracket", "["),
        ("class:status.value", value_text),
        ("class:status.bracket", "]"),
    ]
    return questionary.Choice(tokens, value=value)


def model_display_choice(
    label: str,
    detail_label: str,
    provider_label: str,
    *,
    provider_slug: str | None = None,
    detail_style: str = "status.model",
    value: Any,
) -> questionary.Choice:
    """Render a phase row with colored model/provider segments."""

    tokens: list[tuple[str, str]] = []
    _append_provider_badge_tokens(tokens, provider_label=provider_label, provider_slug=provider_slug)
    if label:
        tokens.append(("class:text", label))
    if detail_label:
        tokens.append(("class:text", " "))
        tokens.append(("class:status.separator", "  "))
        tokens.append((f"class:{detail_style}", detail_label))
    return questionary.Choice(tokens, value=value)


def model_variant_choice(
    label: str,
    variant: str | None,
    provider: str,
    *,
    provider_slug: str | None = None,
    value: Any,
) -> questionary.Choice:
    """Colored choice for variant entries when expanding a model group."""

    tokens: list[tuple[str, str]] = []
    _append_provider_badge_tokens(tokens, provider_label=provider, provider_slug=provider_slug)
    tokens.append(("class:status.variant", label))
    return questionary.Choice(tokens, value=value)


def provider_section_separator(provider_label: str) -> questionary.Separator:
    """Return a lightweight provider header separator for grouped choices."""

    return questionary.Separator(f"---- {provider_label} ----")


def _append_provider_badge_tokens(
    tokens: list[tuple[str, str]],
    *,
    provider_label: str,
    provider_slug: str | None = None,
) -> None:
    slug = _resolve_provider_slug(provider_slug, provider_label)
    if slug is None:
        return
    badge = _PROVIDER_BADGES.get(slug, provider_label[:2].upper())
    style_class = "provider.unknown"
    if slug in _PROVIDER_BADGES:
        style_class = f"provider.{slug}"
    tokens.append((f"class:{style_class}", f"[{badge}]"))
    tokens.append(("class:text", " "))


def _resolve_provider_slug(provider_slug: str | None, provider_label: str) -> str | None:
    if provider_slug:
        return provider_slug
    normalized_label = provider_label.strip().lower()
    if not normalized_label:
        return None
    if "codex" in normalized_label:
        return "codex"
    if "xai" in normalized_label or "grok" in normalized_label:
        return "xai"
    if "deepseek" in normalized_label:
        return "deepseek"
    if "openai" in normalized_label:
        return "openai"
    if "anthropic" in normalized_label:
        return "anthropic"
    if "gemini" in normalized_label:
        return "gemini"
    return "unknown"
