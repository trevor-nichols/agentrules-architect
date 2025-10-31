"""Helper utilities for loading and applying .gitignore patterns."""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from pathspec import PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern


class GitIgnoreSpec(NamedTuple):
    spec: PathSpec
    path: Path


def load_gitignore_spec(directory: Path) -> GitIgnoreSpec | None:
    """Load .gitignore patterns from the provided directory.

    Args:
        directory: Project root to scan for .gitignore.

    Returns:
        GitIgnoreSpec tuple containing the compiled PathSpec and the file path,
        or None when no .gitignore is present or it contains no patterns.
    """

    gitignore_path = directory / ".gitignore"
    if not gitignore_path.is_file():
        return None

    with gitignore_path.open("r", encoding="utf-8", errors="replace") as fh:
        lines = [line.rstrip("\n") for line in fh]

    # pathspec gracefully handles empty lists, but return None to signal absence.
    if not any(line.strip() for line in lines):
        return None

    spec = PathSpec.from_lines(GitWildMatchPattern, lines)
    return GitIgnoreSpec(spec=spec, path=gitignore_path)
