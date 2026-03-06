"""Exclusion override helpers."""

from __future__ import annotations

from agentrules.config.exclusions import EXCLUDED_DIRS, EXCLUDED_EXTENSIONS, EXCLUDED_FILES
from agentrules.core.utils.constants import DEFAULT_RULES_FILENAME, DEFAULT_SNAPSHOT_FILENAME
from agentrules.core.utils.file_creation.snapshot_policy import build_managed_output_relative_paths

from ..models import CLIConfig, ExclusionOverrides
from ..utils import (
    apply_overrides,
    exclusion_attr_names,
    normalize_exclusion_value,
    normalize_output_filename,
    normalize_rules_filename,
)


def get_exclusion_overrides(config: CLIConfig) -> ExclusionOverrides:
    return config.exclusions


def get_effective_exclusions(config: CLIConfig) -> tuple[set[str], set[str], set[str]]:
    overrides = config.exclusions
    directories = apply_overrides(EXCLUDED_DIRS, overrides.add_directories, overrides.remove_directories)
    files = apply_overrides(EXCLUDED_FILES, overrides.add_files, overrides.remove_files)
    extensions = apply_overrides(EXCLUDED_EXTENSIONS, overrides.add_extensions, overrides.remove_extensions)
    return directories, files, extensions


def get_managed_output_relative_paths(
    config: CLIConfig,
    *,
    rules_filename: str | None = None,
    snapshot_filename: str | None = None,
) -> set[str]:
    configured_rules_filename = config.outputs.rules_filename if config.outputs else None
    configured_snapshot_filename = config.outputs.snapshot_filename if config.outputs else None
    rules_filename = normalize_rules_filename(
        rules_filename if rules_filename is not None else configured_rules_filename,
        default=DEFAULT_RULES_FILENAME,
    )
    snapshot_filename = normalize_output_filename(
        snapshot_filename if snapshot_filename is not None else configured_snapshot_filename,
        default=DEFAULT_SNAPSHOT_FILENAME,
    )
    return build_managed_output_relative_paths(
        rules_filename=rules_filename,
        snapshot_filename=snapshot_filename,
    )


def add_exclusion_entry(config: CLIConfig, kind: str, value: str) -> str | None:
    normalized = normalize_exclusion_value(kind, value)
    if normalized is None:
        return None

    add_attr, remove_attr = exclusion_attr_names(kind)
    add_list = getattr(config.exclusions, add_attr)
    remove_list = getattr(config.exclusions, remove_attr)

    if normalized not in add_list:
        add_list.append(normalized)
    if normalized in remove_list:
        remove_list.remove(normalized)

    return normalized


def remove_exclusion_entry(config: CLIConfig, kind: str, value: str) -> str | None:
    normalized = normalize_exclusion_value(kind, value)
    if normalized is None:
        return None

    add_attr, remove_attr = exclusion_attr_names(kind)
    add_list = getattr(config.exclusions, add_attr)
    remove_list = getattr(config.exclusions, remove_attr)

    if normalized in add_list:
        add_list.remove(normalized)
    elif normalized not in remove_list:
        remove_list.append(normalized)

    return normalized


def reset_exclusions(config: CLIConfig) -> None:
    config.exclusions = ExclusionOverrides()


def set_respect_gitignore(config: CLIConfig, enabled: bool) -> None:
    config.exclusions.respect_gitignore = bool(enabled)


def should_respect_gitignore(config: CLIConfig, default: bool = True) -> bool:
    if config.exclusions is None:
        return default
    return bool(config.exclusions.respect_gitignore)


def get_tree_max_depth(config: CLIConfig, default: int = 5) -> int:
    depth = config.exclusions.tree_max_depth
    if depth is None:
        return max(default, 1)
    return max(depth, 1)


def set_tree_max_depth(config: CLIConfig, value: int | None) -> None:
    if value is not None and value < 1:
        raise ValueError("tree depth must be at least 1")
    config.exclusions.tree_max_depth = value


def reset_tree_max_depth(config: CLIConfig) -> None:
    config.exclusions.tree_max_depth = None
