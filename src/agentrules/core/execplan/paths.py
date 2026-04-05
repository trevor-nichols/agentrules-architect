"""Path classification helpers for ExecPlan and milestone artifacts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

MILESTONES_DIR = "milestones"
ACTIVE_DIR = "active"
COMPLETE_DIR = "complete"
ARCHIVE_DIR = "archive"  # Legacy compatibility alias for complete milestone paths.
COMPLETE_DIR_ALIASES = frozenset({COMPLETE_DIR, ARCHIVE_DIR})
MILESTONE_LOCATION_DIRS = frozenset({ACTIVE_DIR, *COMPLETE_DIR_ALIASES})
EXECPLAN_ACTIVE_DIR = "active"
EXECPLAN_COMPLETE_DIR = COMPLETE_DIR
EXECPLAN_ARCHIVE_DIR = ARCHIVE_DIR  # Legacy compatibility alias for complete ExecPlan roots.
EXECPLAN_COMPLETE_DIR_ALIASES = frozenset({EXECPLAN_COMPLETE_DIR, EXECPLAN_ARCHIVE_DIR})

_YEAR_RE = re.compile(r"^\d{4}$")
_MONTH_RE = re.compile(r"^\d{2}$")
_DAY_RE = re.compile(r"^\d{2}$")


@dataclass(frozen=True, slots=True)
class _ExecPlanLayout:
    plan_root: Path
    is_archived: bool


def _parts_relative_to(path: Path, root: Path) -> tuple[str, ...] | None:
    try:
        return path.resolve().relative_to(root.resolve()).parts
    except ValueError:
        return None


def _looks_like_archive_date(year: str, month: str, day: str) -> bool:
    if _YEAR_RE.fullmatch(year) is None:
        return False
    if _MONTH_RE.fullmatch(month) is None:
        return False
    if _DAY_RE.fullmatch(day) is None:
        return False
    month_value = int(month)
    day_value = int(day)
    return 1 <= month_value <= 12 and 1 <= day_value <= 31


def _classify_execplan_layout(path: Path, *, execplans_root: Path) -> _ExecPlanLayout | None:
    parts = _parts_relative_to(path, execplans_root)
    if parts is None:
        return None

    root = execplans_root.resolve()

    # Current active root layout: active/<slug>/...
    if len(parts) >= 3 and parts[0] == EXECPLAN_ACTIVE_DIR:
        return _ExecPlanLayout(
            plan_root=(root / EXECPLAN_ACTIVE_DIR / parts[1]).resolve(),
            is_archived=False,
        )

    # Legacy active slug layout using reserved root name: active/EP-...md
    if len(parts) >= 2 and parts[0] == EXECPLAN_ACTIVE_DIR:
        return _ExecPlanLayout(
            plan_root=(root / EXECPLAN_ACTIVE_DIR).resolve(),
            is_archived=False,
        )

    # Current complete root layout: complete/YYYY/MM/DD/<slug>/...
    # Legacy alias: archive/YYYY/MM/DD/<slug>/...
    if (
        len(parts) >= 6
        and parts[0] in EXECPLAN_COMPLETE_DIR_ALIASES
        and _looks_like_archive_date(parts[1], parts[2], parts[3])
    ):
        return _ExecPlanLayout(
            plan_root=(root / parts[0] / parts[1] / parts[2] / parts[3] / parts[4]).resolve(),
            is_archived=True,
        )

    # Legacy complete layouts: <slug>/(complete|archive)/...
    # Exclude namespace-rooted active paths like active/complete/... .
    if len(parts) >= 3 and parts[1] in EXECPLAN_COMPLETE_DIR_ALIASES and parts[0] != EXECPLAN_ACTIVE_DIR:
        return _ExecPlanLayout(
            plan_root=(root / parts[0] / parts[1]).resolve(),
            is_archived=True,
        )

    # Legacy active layout: <slug>/...
    # Keep compatibility for historical top-level "archive" / "complete" slug directories.
    if len(parts) >= 2 and parts[0] != EXECPLAN_ACTIVE_DIR:
        return _ExecPlanLayout(
            plan_root=(root / parts[0]).resolve(),
            is_archived=False,
        )

    return None


def is_execplan_milestone_path(path: Path, *, execplans_root: Path) -> bool:
    """
    Return True when a path is under a milestone subtree.

    Supported layouts:
    - Legacy: <slug>/milestones/(active|complete|archive)/...
    - Active root: active/<slug>/milestones/(active|complete|archive)/...
    - Complete root: complete/YYYY/MM/DD/<slug>/milestones/(active|complete|archive)/...
      Legacy alias:
      archive/YYYY/MM/DD/<slug>/milestones/(active|complete|archive)/...
    """
    parts = _parts_relative_to(path, execplans_root)
    if parts is None:
        return False

    # Current active root: active/<slug>/milestones/(active|complete|archive)/...
    if (
        len(parts) >= 4
        and parts[0] == EXECPLAN_ACTIVE_DIR
        and parts[2] == MILESTONES_DIR
        and parts[3] in MILESTONE_LOCATION_DIRS
    ):
        return True

    # Current complete root: complete/YYYY/MM/DD/<slug>/milestones/(active|complete|archive)/...
    # Legacy alias: archive/... with the same milestone subtree rules.
    if (
        len(parts) >= 7
        and parts[0] in EXECPLAN_COMPLETE_DIR_ALIASES
        and _looks_like_archive_date(parts[1], parts[2], parts[3])
        and parts[5] == MILESTONES_DIR
        and parts[6] in MILESTONE_LOCATION_DIRS
    ):
        return True

    # Legacy active: <slug>/milestones/(active|complete|archive)/...
    if len(parts) >= 3 and parts[1] == MILESTONES_DIR and parts[2] in MILESTONE_LOCATION_DIRS:
        return True

    # Legacy complete layouts: <slug>/(complete|archive)/milestones/(active|complete|archive)/...
    if (
        len(parts) >= 4
        and parts[1] in EXECPLAN_COMPLETE_DIR_ALIASES
        and parts[2] == MILESTONES_DIR
        and parts[3] in MILESTONE_LOCATION_DIRS
    ):
        return True

    return False


def get_execplan_plan_root(path: Path, *, execplans_root: Path) -> Path:
    """
    Resolve the plan root directory that contains an ExecPlan file and milestone subtree.

    Supported layouts:
    - Legacy active: <slug>/EP-...md
    - Legacy reserved active slug: active/EP-...md
    - Legacy complete: <slug>/complete/EP-...md
    - Legacy alias: <slug>/archive/EP-...md
    - Active root: active/<slug>/EP-...md
    - Complete root: complete/YYYY/MM/DD/<slug>/EP-...md
      Legacy alias: archive/YYYY/MM/DD/<slug>/EP-...md
    """
    layout = _classify_execplan_layout(path, execplans_root=execplans_root)
    if layout is None:
        raise ValueError(
            f"ExecPlan path {path.as_posix()} is not under a recognized ExecPlan layout rooted at "
            f"{execplans_root.resolve().as_posix()}."
        )
    return layout.plan_root


def is_execplan_complete_path(path: Path, *, execplans_root: Path) -> bool:
    """
    Return True when a plan is under a structured complete subtree.

    Supported complete layouts:
    - Legacy: <slug>/complete/...
    - Legacy: <slug>/archive/...
    - Current: complete/YYYY/MM/DD/<slug>/...
    - Legacy alias: archive/YYYY/MM/DD/<slug>/...
    """
    if is_execplan_milestone_path(path, execplans_root=execplans_root):
        return False

    layout = _classify_execplan_layout(path, execplans_root=execplans_root)
    return layout.is_archived if layout is not None else False


def is_execplan_archive_path(path: Path, *, execplans_root: Path) -> bool:
    """Backward-compatible alias for `is_execplan_complete_path`."""
    return is_execplan_complete_path(path, execplans_root=execplans_root)
