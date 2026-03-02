"""Validation helpers for CLI output artifact settings."""

from __future__ import annotations

from agentrules.core.utils.file_creation.snapshot_policy import GENERATED_PHASE_OUTPUT_DIR


def filenames_collide(left: str, right: str) -> bool:
    """Return ``True`` when two configured filenames resolve to the same value."""

    return left.strip().casefold() == right.strip().casefold()


def validate_snapshot_filename_distinct(*, rules_filename: str, snapshot_filename: str) -> None:
    """Ensure snapshot and rules artifacts do not target the same filename."""

    if filenames_collide(rules_filename, snapshot_filename):
        raise ValueError("Snapshot filename must differ from rules filename.")


def validate_snapshot_filename_reserved(snapshot_filename: str) -> None:
    """Reject snapshot names that collide with reserved managed artifacts."""

    normalized = snapshot_filename.strip()
    if normalized in {".", ".."}:
        raise ValueError("Snapshot filename must not be . or ..")

    if filenames_collide(snapshot_filename, ".cursorignore"):
        raise ValueError("Snapshot filename must not be .cursorignore.")
    if filenames_collide(snapshot_filename, GENERATED_PHASE_OUTPUT_DIR):
        raise ValueError(f"Snapshot filename must not be {GENERATED_PHASE_OUTPUT_DIR}.")


def validate_pipeline_output_filenames(
    *,
    rules_filename: str,
    snapshot_filename: str,
    generate_snapshot: bool,
) -> None:
    """Ensure enabled pipeline outputs do not collide on disk."""

    if not generate_snapshot:
        return

    validate_snapshot_filename_reserved(snapshot_filename)

    validate_snapshot_filename_distinct(
        rules_filename=rules_filename,
        snapshot_filename=snapshot_filename,
    )
