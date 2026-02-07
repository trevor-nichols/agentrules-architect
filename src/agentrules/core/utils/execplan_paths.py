"""Path classification helpers for ExecPlan and milestone artifacts."""

from __future__ import annotations

from pathlib import Path

MILESTONES_DIR = "milestones"
ACTIVE_DIR = "active"
ARCHIVE_DIR = "archive"


def _parts_relative_to(path: Path, root: Path) -> tuple[str, ...] | None:
    try:
        return path.resolve().relative_to(root.resolve()).parts
    except ValueError:
        return None


def is_execplan_milestone_path(path: Path, *, execplans_root: Path) -> bool:
    """
    Return True when a path is under a structured milestone subtree:
    <slug>/milestones/(active|archive)/...
    """
    parts = _parts_relative_to(path, execplans_root)
    if parts is None or len(parts) < 4:
        return False
    return parts[1] == MILESTONES_DIR and parts[2] in {ACTIVE_DIR, ARCHIVE_DIR}


def is_execplan_archive_path(path: Path, *, execplans_root: Path) -> bool:
    """
    Return True when a plan is under a structured archive subtree:
    <slug>/archive/...
    """
    parts = _parts_relative_to(path, execplans_root)
    if parts is None or len(parts) < 3:
        return False
    return parts[1] == ARCHIVE_DIR
