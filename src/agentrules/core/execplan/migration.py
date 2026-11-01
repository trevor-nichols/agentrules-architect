"""
Move a legacy ``.agent/`` ExecPlan workspace to the ``.exec_plans/`` layout.

Migration converges: every step inspects the current state, so rerunning after
an interruption finishes the remaining work and rerunning after success is a
no-op. Files are only moved, never deleted; only empty legacy directories are
removed. ExecPlan and milestone bodies are user-authored records and are never
rewritten.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentrules.core.execplan.layout import CURRENT_LAYOUT, LEGACY_LAYOUT, MIGRATE_COMMAND
from agentrules.core.execplan.registry import (
    RegistryBuildResult,
    build_execplan_registry,
    collect_execplan_registry,
)
from agentrules.core.utils.constants import DEFAULT_RULES_FILENAME
from agentrules.core.utils.file_creation.atomic_write import atomic_write_text
from agentrules.core.utils.formatters.clean_agentrules import ensure_execplans_guidance

_GUIDE_MOVES: tuple[tuple[Path, Path], ...] = (
    (LEGACY_LAYOUT.plans_guide_path, CURRENT_LAYOUT.plans_guide_path),
    (LEGACY_LAYOUT.milestone_guide_path, CURRENT_LAYOUT.milestone_guide_path),
)
_LEGACY_PATH_REWRITES: tuple[tuple[str, str], ...] = (
    (LEGACY_LAYOUT.execplans_dir.as_posix(), CURRENT_LAYOUT.execplans_dir.as_posix()),
    (LEGACY_LAYOUT.milestone_guide_path.parent.as_posix(), CURRENT_LAYOUT.milestone_guide_path.parent.as_posix()),
    (LEGACY_LAYOUT.plans_guide_path.as_posix(), CURRENT_LAYOUT.plans_guide_path.as_posix()),
)
_LEGACY_DIRECTORIES_DEEPEST_FIRST: tuple[Path, ...] = (
    LEGACY_LAYOUT.milestone_guide_path.parent,
    LEGACY_LAYOUT.execplans_dir,
    LEGACY_LAYOUT.workspace_dir,
)
_SYMLINK_GUARDED_DIRECTORIES: tuple[Path, ...] = (
    *_LEGACY_DIRECTORIES_DEEPEST_FIRST,
    CURRENT_LAYOUT.workspace_dir,
    CURRENT_LAYOUT.milestone_guide_path.parent,
)


@dataclass(frozen=True, slots=True)
class WorkspaceMove:
    source: Path
    destination: Path


@dataclass(frozen=True, slots=True)
class ExecPlanMigrationResult:
    moves: tuple[WorkspaceMove, ...]
    rewritten_guides: tuple[Path, ...]
    removed_directories: tuple[Path, ...]
    rules_message: str | None
    registry_result: RegistryBuildResult | None
    dry_run: bool

    @property
    def is_noop(self) -> bool:
        return not (
            self.moves
            or self.rewritten_guides
            or self.removed_directories
            or self.rules_message
            or self.registry_result
        )


def _plan_moves(root: Path) -> tuple[WorkspaceMove, ...]:
    moves: list[WorkspaceMove] = []
    legacy_execplans_dir = root / LEGACY_LAYOUT.execplans_dir
    if legacy_execplans_dir.is_dir():
        current_execplans_dir = root / CURRENT_LAYOUT.execplans_dir
        for entry in sorted(legacy_execplans_dir.iterdir()):
            moves.append(WorkspaceMove(source=entry, destination=current_execplans_dir / entry.name))
    for legacy_guide, current_guide in _GUIDE_MOVES:
        source = root / legacy_guide
        if source.exists():
            moves.append(WorkspaceMove(source=source, destination=root / current_guide))
    return tuple(moves)


def _find_migration_conflicts(root: Path, moves: tuple[WorkspaceMove, ...]) -> list[str]:
    def relative(path: Path) -> str:
        return path.relative_to(root).as_posix()

    conflicts = [
        f"{directory.as_posix()} is a symlink"
        for directory in _SYMLINK_GUARDED_DIRECTORIES
        if (root / directory).is_symlink()
    ]
    conflicts.extend(
        f"{relative(move.destination)} already exists"
        for move in moves
        if move.destination.exists() or move.destination.is_symlink()
    )
    destinations = [move.destination for move in moves]
    for index, first in enumerate(destinations):
        for second in destinations[index + 1 :]:
            if first == second or first in second.parents or second in first.parents:
                conflicts.append(f"{relative(first)} and {relative(second)} overlap")
    return conflicts


def _rewrite_legacy_paths(text: str) -> str:
    for legacy_path, current_path in _LEGACY_PATH_REWRITES:
        text = text.replace(legacy_path, current_path)
    return text


def _rewrite_guides(root: Path) -> tuple[Path, ...]:
    rewritten: list[Path] = []
    for _, current_guide in _GUIDE_MOVES:
        guide_path = root / current_guide
        if not guide_path.is_file():
            continue
        original = guide_path.read_text(encoding="utf-8")
        updated = _rewrite_legacy_paths(original)
        if updated != original:
            atomic_write_text(guide_path, updated)
            rewritten.append(guide_path)
    return tuple(rewritten)


def _remove_empty_legacy_directories(root: Path) -> tuple[Path, ...]:
    removed: list[Path] = []
    for relative_directory in _LEGACY_DIRECTORIES_DEEPEST_FIRST:
        directory = root / relative_directory
        if directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
            removed.append(directory)
    return tuple(removed)


def _update_rules_guidance(root: Path, rules_filename: str) -> str | None:
    rules_path = root / rules_filename
    if not rules_path.is_file():
        return None
    original = rules_path.read_text(encoding="utf-8")
    legacy_guides = (LEGACY_LAYOUT.plans_guide_path.as_posix(), LEGACY_LAYOUT.milestone_guide_path.as_posix())
    if not any(guide in original for guide in legacy_guides):
        return None

    success, message = ensure_execplans_guidance(str(root), filename=rules_filename)
    if not success:
        raise ValueError(message)
    if rules_path.read_text(encoding="utf-8") == original:
        return None
    return message


def _stored_registry_matches(registry_path: Path, discovered_registry: dict[str, Any]) -> bool:
    try:
        stored_registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    if not isinstance(stored_registry, dict):
        return False
    stored_registry.pop("generated_at", None)
    return stored_registry == discovered_registry


def _rebuild_registry_if_stale(root: Path) -> RegistryBuildResult | None:
    registry_path = root / CURRENT_LAYOUT.registry_path
    if not registry_path.is_file():
        return None
    discovered = collect_execplan_registry(root=root, execplans_dir=root / CURRENT_LAYOUT.execplans_dir)
    if discovered.error_count == 0 and _stored_registry_matches(registry_path, discovered.registry):
        return None
    return build_execplan_registry(root=root, execplans_dir=CURRENT_LAYOUT.execplans_dir)


def migrate_execplan_workspace(
    root: Path,
    *,
    rules_filename: str | None,
    dry_run: bool = False,
) -> ExecPlanMigrationResult:
    """
    Move a legacy ``.agent/`` ExecPlan workspace under ``root`` to ``.exec_plans/``.

    Raises ``ValueError`` before changing anything when a destination already
    exists, two destinations overlap, or a workspace directory is a symlink.
    Dry-run plans and validates the moves without writing.
    """
    resolved_root = root.resolve()
    moves = _plan_moves(resolved_root)
    conflicts = _find_migration_conflicts(resolved_root, moves)
    if conflicts:
        raise ValueError(
            f"Cannot migrate the legacy {LEGACY_LAYOUT.workspace_dir.as_posix()}/ ExecPlan workspace: "
            f"{'; '.join(conflicts)}. Resolve these paths manually, then rerun `{MIGRATE_COMMAND}`."
        )
    if dry_run:
        return ExecPlanMigrationResult(
            moves=moves,
            rewritten_guides=(),
            removed_directories=(),
            rules_message=None,
            registry_result=None,
            dry_run=True,
        )

    for move in moves:
        move.destination.parent.mkdir(parents=True, exist_ok=True)
        os.replace(move.source, move.destination)
    rewritten_guides = _rewrite_guides(resolved_root)
    # Layout detection treats an empty legacy plans directory as legacy, so the
    # rules update must run after cleanup.
    removed_directories = _remove_empty_legacy_directories(resolved_root)
    rules_message = _update_rules_guidance(resolved_root, rules_filename or DEFAULT_RULES_FILENAME)
    registry_result = _rebuild_registry_if_stale(resolved_root)

    return ExecPlanMigrationResult(
        moves=moves,
        rewritten_guides=rewritten_guides,
        removed_directories=removed_directories,
        rules_message=rules_message,
        registry_result=registry_result,
        dry_run=False,
    )
