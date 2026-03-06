"""Helpers for generating exclusion-aware project tree snapshots."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from agentrules.core.configuration import get_config_manager
from agentrules.core.utils.file_system.gitignore import load_gitignore_spec
from agentrules.core.utils.file_system.tree_generator import (
    get_project_tree,
    save_tree_to_file,
)


@dataclass(slots=True)
class TreeSnapshot:
    """Container describing a filtered project tree."""

    lines: list[str]
    respect_gitignore: bool
    gitignore_path: Path | None
    gitignore_used: bool
    max_depth: int

    def as_preview(self, limit: int | None = None) -> list[str]:
        """Return a possibly truncated copy of the tree for console display."""

        if limit is None or limit <= 0:
            return list(self.lines)
        if len(self.lines) <= limit:
            return list(self.lines)
        truncated = self.lines[: limit - 1]
        truncated.append("└── … (truncated; export for full tree)")
        return truncated

    def export(self, directory: Path, filename: str) -> Path:
        """Persist the tree to ``directory / filename`` in Markdown."""

        output_dir = directory
        output_dir.mkdir(parents=True, exist_ok=True)
        save_tree_to_file(self.lines, output_dir, rules_filename=filename)
        return output_dir / filename


def generate_tree_snapshot(directory: Path, *, max_depth: int | None = None) -> TreeSnapshot:
    """Build the exclusion-aware project tree for ``directory``."""

    config_manager = get_config_manager()
    exclude_dirs, exclude_files, exclude_exts = config_manager.get_effective_exclusions()
    exclude_relative_paths = config_manager.get_managed_output_relative_paths()

    gitignore_spec = None
    gitignore_path: Path | None = None
    respect_gitignore = config_manager.should_respect_gitignore()
    if respect_gitignore:
        loaded = load_gitignore_spec(directory)
        if loaded:
            gitignore_spec = loaded.spec
            gitignore_path = loaded.path

    effective_depth = max_depth if max_depth is not None else config_manager.get_tree_max_depth()

    lines = get_project_tree(
        directory,
        max_depth=effective_depth,
        exclude_dirs=exclude_dirs,
        exclude_files=exclude_files,
        exclude_extensions=exclude_exts,
        gitignore_spec=gitignore_spec,
        exclude_relative_paths=exclude_relative_paths,
    )

    return TreeSnapshot(
        lines=list(lines),
        respect_gitignore=respect_gitignore,
        gitignore_path=gitignore_path,
        gitignore_used=gitignore_spec is not None,
        max_depth=effective_depth,
    )


def export_tree_to_path(tree_lines: Sequence[str], output_path: Path) -> Path:
    """Persist ``tree_lines`` to ``output_path`` using the Markdown layout."""

    target_dir = output_path.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    save_tree_to_file(list(tree_lines), target_dir, rules_filename=output_path.name)
    return output_path
