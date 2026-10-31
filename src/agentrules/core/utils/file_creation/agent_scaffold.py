"""Helpers for creating the optional .agent planning scaffold.

This scaffold materializes human-facing planning guides (for example
``.agent/templates/MILESTONE_TEMPLATE.md``). It is intentionally separate
from internal runtime templates used by ExecPlan command handlers.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path

AGENT_DIRNAME = ".agent"
TEMPLATES_DIRNAME = "templates"
PLANS_FILENAME = "PLANS.md"
MILESTONE_GUIDE_TEMPLATE_FILENAME = "MILESTONE_TEMPLATE.md"


@dataclass(frozen=True, slots=True)
class AgentScaffoldSyncResult:
    ok: bool
    changed: bool
    messages: tuple[str, ...]


def _iter_scaffold_files(target_directory: Path) -> tuple[tuple[Path, str], ...]:
    agent_dir = target_directory / AGENT_DIRNAME
    templates_dir = agent_dir / TEMPLATES_DIRNAME
    return (
        (agent_dir / PLANS_FILENAME, PLANS_FILENAME),
        (templates_dir / MILESTONE_GUIDE_TEMPLATE_FILENAME, MILESTONE_GUIDE_TEMPLATE_FILENAME),
    )


def _load_template_text(template_name: str) -> str:
    resource_root = resources.files("agentrules.core.utils.file_creation")
    template_path = resource_root.joinpath("templates").joinpath(template_name)
    if not template_path.is_file():
        raise FileNotFoundError(f"Template not found: {template_name}")
    return template_path.read_text(encoding="utf-8")


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_path = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)


def _assert_scaffold_path_safe(destination: Path, *, target_directory: Path) -> None:
    resolved_target_directory = target_directory.resolve()
    try:
        relative_parts = destination.relative_to(target_directory).parts
    except ValueError as error:
        raise ValueError(f"Scaffold path must stay inside target directory: {destination}") from error

    current = target_directory
    for part in relative_parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise ValueError(f"Symlinked scaffold path is not allowed: {current}")

    if destination.exists():
        resolved_destination = destination.resolve()
    else:
        resolved_destination = destination.parent.resolve() / destination.name
    try:
        resolved_destination.relative_to(resolved_target_directory)
    except ValueError as error:
        raise ValueError(
            f"Scaffold path escapes target directory: {destination} -> {resolved_destination}"
        ) from error


def _create_file_from_template_if_missing(destination: Path, template_name: str) -> bool:
    if destination.exists():
        if destination.is_file():
            return False
        raise IsADirectoryError(f"Destination exists but is not a file: {destination}")
    _atomic_write_text(destination, _load_template_text(template_name))
    return True


def _backup_destination_file(destination: Path) -> Path:
    if destination.is_symlink():
        raise ValueError(f"Symlinked scaffold path is not allowed: {destination}")
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%SZ")
    backup_path = destination.with_name(f"{destination.name}.bak.{timestamp}")
    suffix = 1
    while backup_path.exists():
        backup_path = destination.with_name(f"{destination.name}.bak.{timestamp}.{suffix}")
        suffix += 1
    _atomic_write_text(backup_path, destination.read_text(encoding="utf-8"))
    return backup_path


def sync_agent_scaffold(
    target_directory: Path,
    *,
    check: bool = False,
    force: bool = False,
) -> AgentScaffoldSyncResult:
    """Sync .agent scaffold templates with optional drift-check and forced updates."""

    if check and force:
        raise ValueError("Cannot combine check and force modes.")
    if not target_directory.exists():
        raise FileNotFoundError(f"Target directory does not exist: {target_directory}")
    if not target_directory.is_dir():
        raise NotADirectoryError(f"Target path is not a directory: {target_directory}")

    files_to_sync = _iter_scaffold_files(target_directory)
    for destination, _ in files_to_sync:
        _assert_scaffold_path_safe(destination, target_directory=target_directory)
        if not check:
            destination.parent.mkdir(parents=True, exist_ok=True)

    messages: list[str] = []
    changed = False
    drift_detected = False

    for destination, template_name in files_to_sync:
        _assert_scaffold_path_safe(destination, target_directory=target_directory)
        expected_content = _load_template_text(template_name)
        relative_path = destination.relative_to(target_directory).as_posix()

        if not destination.exists():
            if check:
                drift_detected = True
                messages.append(f"Missing {relative_path}")
                continue

            _atomic_write_text(destination, expected_content)
            changed = True
            messages.append(f"Created {relative_path}")
            continue

        if not destination.is_file():
            raise IsADirectoryError(f"Destination exists but is not a file: {destination}")

        current_content = destination.read_text(encoding="utf-8")
        if current_content == expected_content:
            messages.append(f"Up-to-date {relative_path}")
            continue

        if check:
            drift_detected = True
            messages.append(f"Outdated {relative_path}")
            continue

        if not force:
            messages.append(f"Outdated {relative_path} (kept existing file; run with --force to update)")
            continue

        backup_path = _backup_destination_file(destination)
        _atomic_write_text(destination, expected_content)
        changed = True
        backup_relative = backup_path.relative_to(target_directory).as_posix()
        messages.append(f"Updated {relative_path} (backup: {backup_relative})")

    return AgentScaffoldSyncResult(ok=not drift_detected, changed=changed, messages=tuple(messages))


def create_agent_scaffold(target_directory: Path) -> tuple[bool, list[str]]:
    """Create .agent directories and template files without overwriting existing files."""
    try:
        files_to_create = _iter_scaffold_files(target_directory)
        for destination, _ in files_to_create:
            _assert_scaffold_path_safe(destination, target_directory=target_directory)
            destination.parent.mkdir(parents=True, exist_ok=True)

        messages: list[str] = []
        for destination, template_name in files_to_create:
            created = _create_file_from_template_if_missing(destination, template_name)
            relative_path = destination.relative_to(target_directory).as_posix()
            if created:
                messages.append(f"Created {relative_path}")
            else:
                messages.append(f"Skipped {relative_path} (already exists)")

        return True, messages
    except Exception as error:  # pragma: no cover - defensive error boundary
        return False, [f"Failed to create .agent scaffold: {error}"]
