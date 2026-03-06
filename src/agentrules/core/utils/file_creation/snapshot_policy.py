"""Shared policy for snapshot artifact generation behavior."""

from __future__ import annotations

GENERATED_PHASE_OUTPUT_DIR = "phases_output"
CURSORIGNORE_FILENAME = ".cursorignore"


def build_managed_output_relative_paths(
    *,
    rules_filename: str | None,
    snapshot_filename: str | None,
) -> set[str]:
    """Return root-relative managed output paths for analyzer and tree exclusions."""

    excludes = {GENERATED_PHASE_OUTPUT_DIR, CURSORIGNORE_FILENAME}
    normalized_rules_filename = _normalize_filename(rules_filename)
    normalized_snapshot_filename = _normalize_filename(snapshot_filename)
    if normalized_rules_filename:
        excludes.add(normalized_rules_filename)
    if normalized_snapshot_filename:
        excludes.add(normalized_snapshot_filename)
    return excludes


def build_snapshot_additional_exclude_paths(
    rules_filename: str,
    snapshot_filename: str | None = None,
) -> set[str]:
    """Return generated root-relative paths that should be excluded from snapshot inputs."""

    excludes = build_managed_output_relative_paths(
        rules_filename=rules_filename,
        snapshot_filename=snapshot_filename,
    )
    normalized_snapshot_filename = _normalize_filename(snapshot_filename)
    if normalized_snapshot_filename:
        excludes.discard(normalized_snapshot_filename)
    return excludes


def _normalize_filename(filename: str | None) -> str | None:
    if filename is None:
        return None
    normalized = filename.strip()
    return normalized or None
