"""File system discovery for dependency manifest files."""

from __future__ import annotations

import fnmatch
from collections.abc import Iterable, Iterator
from pathlib import Path

from pathspec import PathSpec

from agentrules.config.exclusions import EXCLUDED_DIRS, EXCLUDED_EXTENSIONS, EXCLUDED_FILES
from agentrules.core.utils.file_system.file_retriever import list_files

from .constants import MANIFEST_FILENAMES, MANIFEST_PATTERNS


def iter_manifest_files(
    directory: Path,
    gitignore_spec: PathSpec | None,
    *,
    max_depth: int,
    exclude_relative_paths: set[str] | None = None,
) -> Iterator[Path]:
    """Yield manifest files within ``directory`` respecting exclusion rules."""
    include_files = MANIFEST_FILENAMES
    include_patterns = MANIFEST_PATTERNS

    # Build exclusion patterns but allow manifest files that are explicitly included.
    exclude_patterns: set[str] = set(EXCLUDED_FILES) - include_files
    for ext in EXCLUDED_EXTENSIONS:
        exclude_patterns.add(f"*{ext}")

    for path in list_files(
        directory,
        EXCLUDED_DIRS,
        exclude_patterns,
        max_depth=max_depth,
        gitignore_spec=gitignore_spec,
        root=directory,
        exclude_relative_paths=exclude_relative_paths,
    ):
        name = path.name
        if name in include_files or _matches_any_pattern(name, include_patterns):
            yield path


def _matches_any_pattern(name: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)
