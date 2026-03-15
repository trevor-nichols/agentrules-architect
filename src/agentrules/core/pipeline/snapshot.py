"""Utilities for preparing project metadata prior to analysis."""

from __future__ import annotations

from collections.abc import Sequence

from agentrules.core.pipeline.config import GitignoreSnapshot, PipelineSettings, ProjectSnapshot
from agentrules.core.pipeline.project_profile import build_project_profile
from agentrules.core.utils.dependency_scanner import collect_dependency_info
from agentrules.core.utils.file_system.gitignore import load_gitignore_spec
from agentrules.core.utils.file_system.tree_generator import get_project_tree


def build_project_snapshot(settings: PipelineSettings) -> ProjectSnapshot:
    """Collect the project state required by the analysis pipeline."""

    gitignore_spec = None
    gitignore_path = None
    if settings.respect_gitignore:
        gitignore_loaded = load_gitignore_spec(settings.target_directory)
        if gitignore_loaded:
            gitignore_spec = gitignore_loaded.spec
            gitignore_path = gitignore_loaded.path

    exclude_dirs = set(settings.effective_exclusions.directories)
    exclude_files = set(settings.effective_exclusions.files)
    exclude_exts = set(settings.effective_exclusions.extensions)

    tree_with_delimiters = get_project_tree(
        settings.target_directory,
        max_depth=settings.tree_max_depth,
        exclude_dirs=exclude_dirs,
        exclude_files=exclude_files,
        exclude_extensions=exclude_exts,
        gitignore_spec=gitignore_spec,
        exclude_relative_paths=set(settings.exclude_relative_paths),
    )
    tree = _strip_tree_delimiters(tree_with_delimiters)

    dependency_info = collect_dependency_info(
        settings.target_directory,
        gitignore_spec=gitignore_spec,
        max_depth=settings.tree_max_depth,
        exclude_relative_paths=set(settings.exclude_relative_paths),
    )
    explicit_exclude_files = set(settings.exclusion_overrides.add_files) if settings.exclusion_overrides else set()
    explicit_exclude_extensions = (
        set(settings.exclusion_overrides.add_extensions) if settings.exclusion_overrides else set()
    )
    project_profile = build_project_profile(
        target_directory=settings.target_directory,
        dependency_info=dependency_info,
        tree_max_depth=settings.tree_max_depth,
        gitignore_spec=gitignore_spec,
        exclude_dirs=exclude_dirs,
        exclude_files=exclude_files,
        exclude_extensions=exclude_exts,
        exclude_relative_paths=set(settings.exclude_relative_paths),
        explicit_exclude_files=explicit_exclude_files,
        explicit_exclude_extensions=explicit_exclude_extensions,
    )

    return ProjectSnapshot(
        tree_with_delimiters=tuple(tree_with_delimiters),
        tree=tuple(tree),
        dependency_info=dependency_info,
        gitignore=GitignoreSnapshot(spec=gitignore_spec, path=gitignore_path),
        project_profile=project_profile,
    )


def _strip_tree_delimiters(tree_with_delimiters: Sequence[str]) -> list[str]:
    has_wrapping_tags = (
        len(tree_with_delimiters) >= 2
        and tree_with_delimiters[0] == "<project_structure>"
        and tree_with_delimiters[-1] == "</project_structure>"
    )
    if has_wrapping_tags:
        return list(tree_with_delimiters[1:-1])
    return list(tree_with_delimiters)
