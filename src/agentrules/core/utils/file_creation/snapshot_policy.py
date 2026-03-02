"""Shared policy for snapshot artifact generation behavior."""

from __future__ import annotations

GENERATED_PHASE_OUTPUT_DIR = "phases_output"


def build_snapshot_additional_exclude_paths(rules_filename: str) -> set[str]:
    """Return generated paths that should be excluded from snapshot inputs."""

    excludes = {GENERATED_PHASE_OUTPUT_DIR}
    normalized_rules_filename = rules_filename.strip()
    if normalized_rules_filename:
        excludes.add(normalized_rules_filename)
    return excludes
