"""Compatibility wrappers for disabled ExecPlan locking.

Lock files under ``.agent/exec_plans/.locks`` were intentionally removed due to
operator feedback. The public helpers remain as no-op context managers so
existing call sites keep working without creating lock artifacts.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

EXECPLAN_ID_RE = re.compile(r"^EP-\d{8}-\d{3}$")
_LOCKS_DIRNAME = ".locks"


@contextmanager
def file_lock(lock_path: Path) -> Iterator[None]:
    """No-op legacy lock context.

    The ``lock_path`` parameter is preserved for backwards compatibility.
    """
    _ = lock_path
    yield


def get_execplan_lock_path(*, execplans_dir: Path, execplan_id: str) -> Path:
    """Return the historical lock path while validating call inputs."""
    if EXECPLAN_ID_RE.fullmatch(execplan_id) is None:
        raise ValueError(f"Invalid ExecPlan ID {execplan_id!r}. Expected EP-YYYYMMDD-NNN.")
    resolved_execplans_dir = execplans_dir.resolve()
    if not resolved_execplans_dir.exists():
        raise FileNotFoundError(f"ExecPlans directory not found: {resolved_execplans_dir}")
    return (resolved_execplans_dir / _LOCKS_DIRNAME / f"{execplan_id}.lock").resolve()


@contextmanager
def execplan_mutation_lock(*, execplans_dir: Path, execplan_id: str) -> Iterator[None]:
    """No-op lock wrapper for ExecPlan mutation code paths."""
    # Preserve legacy argument validation behavior.
    get_execplan_lock_path(execplans_dir=execplans_dir, execplan_id=execplan_id)
    yield
