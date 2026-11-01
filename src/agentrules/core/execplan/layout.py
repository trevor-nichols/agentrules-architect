"""Locate the ExecPlan workspace a repository uses.

Current repositories keep the guides, registry, and plans together under
``.exec_plans/``. Older repositories keep the guides under ``.agent/`` and the
plans under ``.agent/exec_plans/``; they stay supported until migrated with
``agentrules execplan migrate``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

REGISTRY_FILENAME = "registry.json"
PLANS_GUIDE_FILENAME = "PLANS.md"
GUIDE_TEMPLATES_DIRNAME = "templates"
MILESTONE_GUIDE_FILENAME = "MILESTONE_TEMPLATE.md"
MIGRATE_COMMAND = "agentrules execplan migrate"


class AmbiguousExecPlanLayoutError(ValueError):
    """Raised when a repository contains both the current and the legacy workspace."""


@dataclass(frozen=True, slots=True)
class ExecPlanLayout:
    workspace_dir: Path
    execplans_dir: Path
    is_legacy: bool

    @property
    def registry_path(self) -> Path:
        return self.execplans_dir / REGISTRY_FILENAME

    @property
    def plans_guide_path(self) -> Path:
        return self.workspace_dir / PLANS_GUIDE_FILENAME

    @property
    def milestone_guide_path(self) -> Path:
        return self.workspace_dir / GUIDE_TEMPLATES_DIRNAME / MILESTONE_GUIDE_FILENAME

    @property
    def markers(self) -> tuple[Path, ...]:
        """Root-relative entries whose presence means a repository uses this layout."""
        return (self.execplans_dir, self.plans_guide_path, self.milestone_guide_path)

    def is_present(self, root: Path) -> bool:
        return any((root / marker).exists() for marker in self.markers)


CURRENT_LAYOUT = ExecPlanLayout(
    workspace_dir=Path(".exec_plans"),
    execplans_dir=Path(".exec_plans"),
    is_legacy=False,
)
LEGACY_LAYOUT = ExecPlanLayout(
    workspace_dir=Path(".agent"),
    execplans_dir=Path(".agent/exec_plans"),
    is_legacy=True,
)

DEFAULT_EXECPLANS_DIR = CURRENT_LAYOUT.execplans_dir
DEFAULT_REGISTRY_PATH = CURRENT_LAYOUT.registry_path


@dataclass(frozen=True, slots=True)
class ResolvedExecPlanPaths:
    layout: ExecPlanLayout
    execplans_dir: Path
    registry_path: Path


def detect_execplan_layout(root: Path) -> ExecPlanLayout:
    """
    Return the workspace layout used under ``root``.

    Repositories with no workspace yet use the current layout. A bare ``.agent/``
    directory without legacy ExecPlan entries does not count as legacy.
    """
    current_present = CURRENT_LAYOUT.is_present(root)
    legacy_present = LEGACY_LAYOUT.is_present(root)
    if current_present and legacy_present:
        raise AmbiguousExecPlanLayoutError(
            f"Found both {CURRENT_LAYOUT.workspace_dir.as_posix()}/ and a legacy "
            f"{LEGACY_LAYOUT.workspace_dir.as_posix()}/ ExecPlan workspace under {root.as_posix()}. "
            f"Run `{MIGRATE_COMMAND}` to move the legacy workspace, or pass --execplans-dir explicitly."
        )
    return LEGACY_LAYOUT if legacy_present else CURRENT_LAYOUT


def _resolve_against(root: Path, value: Path) -> Path:
    return value.resolve() if value.is_absolute() else (root / value).resolve()


def resolve_execplan_paths(
    root: Path,
    *,
    execplans_dir: Path | None = None,
    registry_path: Path | None = None,
) -> ResolvedExecPlanPaths:
    """
    Resolve absolute ExecPlan paths for ``root``.

    Without ``execplans_dir`` the workspace is detected. An explicit directory is
    used as given and reports the legacy layout only when it is the legacy plans
    directory. The registry defaults to ``<execplans_dir>/registry.json``.
    """
    resolved_root = root.resolve()
    if execplans_dir is None:
        layout = detect_execplan_layout(resolved_root)
        resolved_execplans_dir = (resolved_root / layout.execplans_dir).resolve()
    else:
        resolved_execplans_dir = _resolve_against(resolved_root, execplans_dir)
        legacy_execplans_dir = (resolved_root / LEGACY_LAYOUT.execplans_dir).resolve()
        layout = LEGACY_LAYOUT if resolved_execplans_dir == legacy_execplans_dir else CURRENT_LAYOUT

    resolved_registry_path = (
        _resolve_against(resolved_root, registry_path)
        if registry_path is not None
        else resolved_execplans_dir / REGISTRY_FILENAME
    )
    return ResolvedExecPlanPaths(
        layout=layout,
        execplans_dir=resolved_execplans_dir,
        registry_path=resolved_registry_path,
    )
