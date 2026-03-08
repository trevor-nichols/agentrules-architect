"""Reusable helper functions for configuration services."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import cast

from .models import CodexHomeStrategy, ResearcherMode


def coerce_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def coerce_positive_int(
    value: object,
    *,
    minimum: int = 1,
    default: int | None = None,
) -> int | None:
    if value is None:
        return default
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value if value >= minimum else default
    if isinstance(value, float):
        return int(value) if value >= minimum else default
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return default
        try:
            parsed = int(float(stripped))
        except ValueError:
            return default
        return parsed if parsed >= minimum else default
    return default


def coerce_string_list(payload: object, key: str) -> list[str]:
    if not isinstance(payload, Mapping):
        return []
    value = payload.get(key)
    if value is None:
        return []
    items: Iterable[object]
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, Iterable):
        items = value
    else:
        return []
    result: list[str] = []
    for item in items:
        if isinstance(item, str):
            stripped = item.strip()
            if stripped:
                result.append(stripped)
    return result


def normalize_output_filename(value: object, *, default: str) -> str:
    if isinstance(value, str) and value.strip():
        candidate = value.strip()
        if "/" in candidate or "\\" in candidate:
            return default
        return candidate
    return default


def normalize_rules_filename(value: object, *, default: str) -> str:
    return normalize_output_filename(value, default=default)


def normalize_optional_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def normalize_codex_home_strategy(
    value: object,
    *,
    default: CodexHomeStrategy,
) -> CodexHomeStrategy:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"managed", "inherit"}:
            return cast(CodexHomeStrategy, normalized)
    return default


def apply_overrides(
    base: Iterable[str],
    additions: Iterable[str],
    removals: Iterable[str],
) -> set[str]:
    updated = set(base)
    for item in additions:
        if item:
            updated.add(item)
    for item in removals:
        if item in updated:
            updated.remove(item)
    return updated


def normalize_exclusion_value(kind: str, value: str) -> str | None:
    if not value:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None

    if kind == "extensions":
        if "/" in cleaned or "\\" in cleaned:
            return None
        if not cleaned.startswith("."):
            cleaned = f".{cleaned}"
        return cleaned

    if kind == "files":
        if "\n" in cleaned:
            return None
        return cleaned

    if kind == "directories":
        if "/" in cleaned or "\\" in cleaned:
            return None
        return cleaned

    return cleaned


def exclusion_attr_names(kind: str) -> tuple[str, str]:
    mapping = {
        "directories": ("add_directories", "remove_directories"),
        "files": ("add_files", "remove_files"),
        "extensions": ("add_extensions", "remove_extensions"),
    }
    if kind not in mapping:
        raise ValueError(f"Unknown exclusion kind: {kind}")
    return mapping[kind]


def normalize_researcher_mode(value: object, *, default: ResearcherMode) -> ResearcherMode:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"on", "off"}:
            return cast(ResearcherMode, normalized)
    if isinstance(value, bool):
        return "on" if value else "off"
    return default


def normalize_verbosity_label(label: str | None) -> str | None:
    if not label:
        return None
    normalized = label.strip().lower()
    if normalized in {"quiet", "standard", "verbose"}:
        return normalized
    if normalized in {"warn", "warning"}:
        return "quiet"
    if normalized in {"info", "default", "standard"}:
        return "standard"
    if normalized in {"debug", "verbose"}:
        return "verbose"
    return None


def is_truthy_string(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}
