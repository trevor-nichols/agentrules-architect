"""SNAPSHOT artifact generation with comment-preserving tree sync."""

from __future__ import annotations

import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from pathspec import PathSpec

from agentrules.core.utils.file_creation.atomic_write import atomic_write_text
from agentrules.core.utils.file_system.tree_generator import get_project_tree

_TREE_BLOCK_PATTERN = re.compile(
    r"<project_structure>\n?(.*?)\n?</project_structure>",
    re.DOTALL,
)
_TREE_LINE_PATTERN = re.compile(r"^((?:[│ ]{4})*)(├── |└── )(.*)$")
_TREE_COMMENT_DELIMITER = "  # "
_TREE_COMMENT_PATTERN = re.compile(r"^(?P<name>.+)\s+#\s+(?P<comment>\S.*)$")
_TREE_MAX_DEPTH_MARKER = "..."
_LEGACY_TREE_MAX_DEPTH_MARKER = "... (max depth reached)"


@dataclass(frozen=True)
class SnapshotSyncResult:
    """Result metadata from a snapshot generation/sync operation."""

    output_path: Path
    changed: bool
    wrote: bool
    tree_entries: int
    preserved_comments: int
    added_paths: tuple[str, ...]
    removed_paths: tuple[str, ...]


def sync_snapshot_artifact(
    directory: Path,
    *,
    output_path: Path,
    tree_max_depth: int | None,
    exclude_dirs: set[str],
    exclude_files: set[str],
    exclude_extensions: set[str],
    gitignore_spec: PathSpec | None = None,
    additional_exclude_relative_paths: set[str] | None = None,
    write: bool = True,
) -> SnapshotSyncResult:
    """Generate or sync a snapshot file while preserving inline tree comments."""

    if tree_max_depth is not None and tree_max_depth < 1:
        raise ValueError("tree_max_depth must be at least 1")

    directory, output_path, output_relative_path = _normalize_snapshot_output_path(
        directory=directory,
        output_path=output_path,
    )

    existing_content = _load_existing_snapshot_content(output_path)
    comment_map, trailing_slash_dirs = _parse_existing_tree_comments(
        existing_content or "",
        directory=directory,
    )

    effective_exclude_files = set(exclude_files)
    exclude_relative_paths = _build_exclude_relative_paths(
        output_relative_path=output_relative_path,
        additional_exclude_relative_paths=additional_exclude_relative_paths,
    )

    tree_with_tags = get_project_tree(
        directory,
        max_depth=tree_max_depth,
        exclude_dirs=exclude_dirs,
        exclude_files=effective_exclude_files,
        exclude_extensions=exclude_extensions,
        gitignore_spec=gitignore_spec,
        exclude_relative_paths=exclude_relative_paths,
        follow_symlinks=False,
    )
    tree_lines = _unwrap_tree_lines(tree_with_tags)
    annotated_tree_lines, new_paths, preserved_comments = _annotate_tree_lines(
        tree_lines,
        comment_map,
        trailing_slash_dirs,
        directory=directory,
    )

    old_paths = set(comment_map.keys())
    added_paths = tuple(sorted(new_paths - old_paths))
    removed_paths = tuple(sorted(old_paths - new_paths))

    rendered_content = _render_snapshot_content(annotated_tree_lines)

    changed = existing_content != rendered_content
    wrote = False
    if write and changed:
        atomic_write_text(output_path, rendered_content)
        wrote = True

    return SnapshotSyncResult(
        output_path=output_path,
        changed=changed,
        wrote=wrote,
        tree_entries=len(annotated_tree_lines),
        preserved_comments=preserved_comments,
        added_paths=added_paths,
        removed_paths=removed_paths,
    )


def _normalize_snapshot_output_path(*, directory: Path, output_path: Path) -> tuple[Path, Path, str]:
    """Return canonicalized paths anchored to ``directory``.

    This normalizes ``..`` segments and enforces that the output's real parent
    directory stays within the project directory, while keeping the final output
    filename unresolved so symlink targets are never followed during writes.
    """

    directory_lexical_path = Path(os.path.abspath(directory))
    directory_real_path = directory_lexical_path.resolve(strict=False)

    raw_output_path = output_path if output_path.is_absolute() else directory_lexical_path / output_path
    normalized_output_path = Path(os.path.abspath(raw_output_path))

    parent_real_path = normalized_output_path.parent.resolve(strict=False)
    if not _is_relative_to(parent_real_path, directory_real_path):
        raise ValueError(f"output_path must be within directory: {normalized_output_path}")

    try:
        output_relative_path = normalized_output_path.relative_to(directory_lexical_path).as_posix()
    except ValueError as error:
        raise ValueError(f"output_path must be within directory: {normalized_output_path}") from error

    return directory_lexical_path, normalized_output_path, output_relative_path


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _load_existing_snapshot_content(output_path: Path) -> str | None:
    """Load existing snapshot content when safe to do so."""

    if not output_path.exists() or output_path.is_symlink():
        return None
    try:
        return output_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _build_exclude_relative_paths(
    *,
    output_relative_path: str,
    additional_exclude_relative_paths: set[str] | None = None,
) -> set[str]:
    excluded = _normalize_relative_paths(additional_exclude_relative_paths)
    excluded.add(output_relative_path)
    return excluded


def _normalize_relative_paths(paths: Iterable[str] | None) -> set[str]:
    normalized: set[str] = set()
    for path in paths or set():
        candidate = path.strip().replace("\\", "/").strip("/")
        if candidate:
            normalized.add(candidate)
    return normalized


def _unwrap_tree_lines(lines: Iterable[str]) -> list[str]:
    tree_lines = list(lines)
    if (
        len(tree_lines) >= 2
        and tree_lines[0] == "<project_structure>"
        and tree_lines[-1] == "</project_structure>"
    ):
        return tree_lines[1:-1]
    return tree_lines


def _extract_tree_lines(content: str) -> list[str]:
    if not content:
        return []
    match = _TREE_BLOCK_PATTERN.search(content)
    if match:
        raw = match.group(1)
    else:
        raw = content
    return [line for line in raw.splitlines() if line.strip()]


def _split_name_and_comment(
    name_with_comment: str,
    *,
    directory: Path | None = None,
    parent_parts: list[str] | None = None,
) -> tuple[str, str | None]:
    raw_name = name_with_comment.rstrip()
    match = _TREE_COMMENT_PATTERN.match(raw_name)
    if match is None:
        return raw_name, None

    stripped_name = match.group("name").rstrip()
    stripped_comment = match.group("comment").strip()
    if not stripped_name or not stripped_comment:
        return raw_name, None

    # Backward-compatible disambiguation:
    # if the unsplit name exists in the current tree and the split candidate does
    # not, treat delimiter text as part of the file/dir name instead of metadata.
    if (
        directory is not None
        and parent_parts is not None
        and _snapshot_entry_exists(directory, parent_parts, raw_name)
    ):
        # If the unsplit name exists, treat delimiter text as part of the
        # literal entry name. This avoids false path/comment rewrites when
        # valid names include "  # " (including ambiguous cases where both
        # split and unsplit candidates exist).
        return raw_name, None

    return stripped_name, stripped_comment


def _snapshot_entry_exists(directory: Path, parent_parts: list[str], name: str) -> bool:
    normalized_name = name.rstrip("/").strip()
    if not normalized_name:
        return False
    if any(part == "<unknown>" for part in parent_parts):
        return False
    try:
        return directory.joinpath(*parent_parts, normalized_name).exists()
    except OSError:
        return False


def _snapshot_directory_exists(directory: Path, parent_parts: list[str], name: str) -> bool:
    normalized_name = name.rstrip("/").strip()
    if not normalized_name:
        return False
    if any(part == "<unknown>" for part in parent_parts):
        return False
    try:
        return directory.joinpath(*parent_parts, normalized_name).is_dir()
    except OSError:
        return False


def _is_tree_max_depth_marker(name: str) -> bool:
    normalized_name = name.strip()
    return normalized_name in {_TREE_MAX_DEPTH_MARKER, _LEGACY_TREE_MAX_DEPTH_MARKER}


def _parse_existing_tree_comments(
    content: str,
    *,
    directory: Path | None = None,
) -> tuple[dict[str, str | None], set[str]]:
    comment_map: dict[str, str | None] = {}
    trailing_slash_dirs: set[str] = set()
    stack: list[str] = []

    for line in _extract_tree_lines(content):
        parsed = _parse_tree_line(line)
        if parsed is None:
            continue
        depth, _prefix, _connector, name_with_comment = parsed

        if depth < len(stack):
            stack = stack[:depth]
        elif depth > len(stack):
            while len(stack) < depth:
                stack.append("<unknown>")

        parent_parts = stack[:depth]
        name, comment = _split_name_and_comment(
            name_with_comment,
            directory=directory,
            parent_parts=parent_parts,
        )
        had_trailing_slash = name.endswith("/")
        normalized_name = name.rstrip("/").strip()
        if not normalized_name:
            continue
        if _is_tree_max_depth_marker(normalized_name):
            continue

        stack = parent_parts
        stack.append(normalized_name)
        rel_path = "/".join(stack)
        comment_map[rel_path] = comment
        if had_trailing_slash:
            trailing_slash_dirs.add(rel_path)

    return comment_map, trailing_slash_dirs


def _annotate_tree_lines(
    tree_lines: list[str],
    comment_map: dict[str, str | None],
    trailing_slash_dirs: set[str],
    *,
    directory: Path,
) -> tuple[list[str], set[str], int]:
    parsed_entries: list[tuple[int, str, str, str] | None] = [_parse_tree_line(line) for line in tree_lines]
    stack: list[str] = []
    new_paths: set[str] = set()
    preserved_comments = 0
    rendered: list[str] = []

    for index, parsed in enumerate(parsed_entries):
        line = tree_lines[index]
        if parsed is None:
            rendered.append(line)
            continue

        depth, prefix, connector, raw_name = parsed
        normalized_name = raw_name.strip()
        if not normalized_name:
            rendered.append(line)
            continue
        normalized_name = normalized_name.rstrip("/")
        if _is_tree_max_depth_marker(normalized_name):
            rendered.append(line)
            continue

        if depth < len(stack):
            stack = stack[:depth]
        elif depth > len(stack):
            while len(stack) < depth:
                stack.append("<unknown>")

        stack = stack[:depth]
        stack.append(normalized_name)
        rel_path = "/".join(stack)
        new_paths.add(rel_path)

        comment = comment_map.get(rel_path)
        if comment:
            preserved_comments += 1

        next_parsed = parsed_entries[index + 1] if index + 1 < len(parsed_entries) else None
        is_directory = bool(next_parsed and next_parsed[0] > depth)
        if not is_directory:
            is_directory = _snapshot_directory_exists(directory, stack[:-1], stack[-1])
        display_name = normalized_name
        if is_directory and rel_path in trailing_slash_dirs:
            display_name = f"{display_name}/"

        comment_suffix = f"{_TREE_COMMENT_DELIMITER}{comment}" if comment else ""
        rendered.append(f"{prefix}{connector}{display_name}{comment_suffix}")

    return rendered, new_paths, preserved_comments


def _parse_tree_line(line: str) -> tuple[int, str, str, str] | None:
    stripped = line.strip()
    if not stripped or stripped == ".":
        return None

    match = _TREE_LINE_PATTERN.match(line.rstrip("\n"))
    if not match:
        return None
    prefix, connector, name = match.groups()
    depth = len(prefix) // 4
    return depth, prefix, connector, name.strip()


def _render_snapshot_content(
    tree_lines: list[str],
) -> str:
    sections: list[str] = ["<project_structure>"]
    sections.extend(tree_lines)
    sections.append("</project_structure>")
    return "\n".join(sections).rstrip() + "\n"
