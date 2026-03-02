"""Atomic file write helpers."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def atomic_write_text(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    """Write ``content`` to ``path`` atomically.

    The target file is replaced in a single ``os.replace`` operation so readers
    either see the previous content or the new full content.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    temp_file = Path(tmp_path)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_file, path)
    finally:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except OSError:
                pass

