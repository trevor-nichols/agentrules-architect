"""Cross-process coordination helpers for ExecPlan mutations.

ExecPlan and milestone mutations must serialize per ExecPlan ID so concurrent
CLI invocations cannot allocate duplicate milestone identifiers. We lock the
owning ExecPlan markdown file directly, which avoids leaving historical
``.agent/exec_plans/.locks`` artifacts behind.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from agentrules.core.execplan.identity import extract_execplan_id_from_filename
from agentrules.core.execplan.paths import is_execplan_milestone_path

try:  # pragma: no cover - platform-specific import
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None  # type: ignore[assignment]

try:  # pragma: no cover - platform-specific import
    import msvcrt
except ImportError:  # pragma: no cover - POSIX
    msvcrt = None  # type: ignore[assignment]

EXECPLAN_ID_RE = re.compile(r"^EP-\d{8}-\d{3}$")
_LOCKS_DIRNAME = ".locks"


@contextmanager
def file_lock(lock_path: Path) -> Iterator[None]:
    """Acquire an exclusive advisory lock on an existing file path.

    Advisory locking is coordination only, so opening the ExecPlan must not
    require write permission on the markdown file itself.
    """
    resolved_lock_path = lock_path.resolve()
    with resolved_lock_path.open("rb") as handle:
        if fcntl is not None:  # pragma: no branch
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        elif msvcrt is not None:  # pragma: no cover - Windows-only branch
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:  # pragma: no cover - unsupported platform
            raise RuntimeError("No supported file locking implementation is available on this platform.")

        try:
            yield
        finally:
            if fcntl is not None:  # pragma: no branch
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            elif msvcrt is not None:  # pragma: no cover - Windows-only branch
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def get_execplan_lock_path(*, execplans_dir: Path, execplan_id: str) -> Path:
    """Return the historical lock path while validating call inputs."""
    if EXECPLAN_ID_RE.fullmatch(execplan_id) is None:
        raise ValueError(f"Invalid ExecPlan ID {execplan_id!r}. Expected EP-YYYYMMDD-NNN.")
    resolved_execplans_dir = execplans_dir.resolve()
    if not resolved_execplans_dir.exists():
        raise FileNotFoundError(f"ExecPlans directory not found: {resolved_execplans_dir}")
    return (resolved_execplans_dir / _LOCKS_DIRNAME / f"{execplan_id}.lock").resolve()


def _iter_execplan_files(execplans_dir: Path) -> tuple[Path, ...]:
    return tuple(
        candidate.resolve()
        for candidate in execplans_dir.rglob("EP-*.md")
        if candidate.is_file() and not is_execplan_milestone_path(candidate, execplans_root=execplans_dir)
    )


def _resolve_execplan_path(*, execplans_dir: Path, execplan_id: str) -> Path:
    if EXECPLAN_ID_RE.fullmatch(execplan_id) is None:
        raise ValueError(f"Invalid ExecPlan ID {execplan_id!r}. Expected EP-YYYYMMDD-NNN.")
    if not execplans_dir.exists():
        raise FileNotFoundError(f"ExecPlans directory not found: {execplans_dir}")

    matches = [
        candidate
        for candidate in _iter_execplan_files(execplans_dir)
        if extract_execplan_id_from_filename(candidate.name) == execplan_id
    ]
    if not matches:
        raise FileNotFoundError(f"ExecPlan {execplan_id!r} was not found under {execplans_dir}.")
    if len(matches) > 1:
        joined = ", ".join(path.as_posix() for path in sorted(matches))
        raise ValueError(f"ExecPlan ID {execplan_id!r} resolved to multiple files. Resolve duplicates first: {joined}")
    return matches[0]


@contextmanager
def execplan_mutation_lock(*, execplans_dir: Path, execplan_id: str) -> Iterator[None]:
    """Serialize mutations for one ExecPlan without creating lock artifacts."""
    get_execplan_lock_path(execplans_dir=execplans_dir, execplan_id=execplan_id)
    lock_target = _resolve_execplan_path(execplans_dir=execplans_dir, execplan_id=execplan_id)
    with file_lock(lock_target):
        yield
