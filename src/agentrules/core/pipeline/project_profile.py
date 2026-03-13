"""Project-profile discovery for Phase 1 context routing."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from pathspec import PathSpec

from agentrules.core.utils.file_system.file_retriever import list_files

_FRONTEND_CONFIG_FILES = frozenset(
    {
        "next.config.js",
        "next.config.mjs",
        "next.config.ts",
        "tailwind.config.js",
        "tailwind.config.cjs",
        "tailwind.config.mjs",
        "tailwind.config.ts",
        "postcss.config.js",
        "postcss.config.cjs",
        "postcss.config.mjs",
        "vite.config.js",
        "vite.config.ts",
    }
)

_PYTHON_PACKAGING_FILES = frozenset(
    {
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "pipfile",
        "requirements.txt",
    }
)

_PYTHON_TASK_RUNNER_FILES = frozenset({"makefile", "justfile"})
_PYTHON_TOOLING_FILES = frozenset({"tox.ini", "noxfile.py"})
_STYLE_EXTENSIONS = frozenset({".css", ".scss", ".sass", ".less", ".styl"})
_PYTHON_MANAGERS = frozenset({"python", "pip", "pipenv", "conda"})
_FRONTEND_DEPENDENCY_MAP = {
    "next": "nextjs",
    "react": "react",
    "vue": "vue",
    "svelte": "svelte",
    "@sveltejs/kit": "sveltekit",
}
_STYLING_DEPENDENCY_MAP = {
    "tailwindcss": "tailwindcss",
    "styled-components": "styled-components",
    "@emotion/react": "emotion",
    "sass": "sass",
    "less": "less",
}


def build_project_profile(
    *,
    target_directory: Path,
    dependency_info: Mapping[str, Any] | None,
    tree_max_depth: int,
    gitignore_spec: PathSpec | None,
    exclude_dirs: set[str],
    exclude_files: set[str],
    exclude_extensions: set[str],
    exclude_relative_paths: set[str],
) -> dict[str, Any]:
    """
    Build deterministic repository profile metadata for Phase 1 agent routing.

    The profile is intentionally rule-based and provider-independent so it can be
    used as routing context without introducing model or network dependencies.
    """

    visible_files = _list_visible_files(
        target_directory=target_directory,
        tree_max_depth=tree_max_depth,
        gitignore_spec=gitignore_spec,
        exclude_dirs=exclude_dirs,
        exclude_files=exclude_files,
        exclude_extensions=exclude_extensions,
        exclude_relative_paths=exclude_relative_paths,
    )

    manifest_records = _manifest_records(dependency_info)
    managers = _dependency_managers(dependency_info)
    manifest_types = _manifest_types(manifest_records)
    manifest_paths = _manifest_paths(manifest_records, target_directory=target_directory)

    npm_dependencies = _npm_dependency_names(manifest_records)
    frontend_profile = _build_frontend_profile(visible_files, npm_dependencies)
    python_profile = _build_python_profile(visible_files, managers)

    detected_types = _detected_types(frontend_profile=frontend_profile, python_profile=python_profile)

    return {
        "schema_version": "1.0",
        "detected_types": detected_types,
        "ecosystem": {
            "dependency_managers": managers,
            "manifest_types": manifest_types,
            "manifest_paths": manifest_paths,
        },
        "frontend": frontend_profile,
        "python": python_profile,
        "signals": {
            "tree_max_depth": tree_max_depth,
            "files_scanned": len(visible_files),
        },
    }


def _list_visible_files(
    *,
    target_directory: Path,
    tree_max_depth: int,
    gitignore_spec: PathSpec | None,
    exclude_dirs: set[str],
    exclude_files: set[str],
    exclude_extensions: set[str],
    exclude_relative_paths: set[str],
) -> list[str]:
    patterns = set(exclude_files)
    patterns.update(f"*{ext}" for ext in exclude_extensions)

    visible_files: list[str] = []
    for path in list_files(
        target_directory,
        exclude_dirs,
        patterns,
        max_depth=tree_max_depth,
        gitignore_spec=gitignore_spec,
        root=target_directory,
        exclude_relative_paths=exclude_relative_paths,
    ):
        try:
            relative = path.relative_to(target_directory).as_posix()
        except ValueError:
            relative = path.as_posix()
        visible_files.append(relative)

    return _sorted_unique(visible_files)


def _build_frontend_profile(
    visible_files: list[str],
    npm_dependencies: set[str],
) -> dict[str, Any]:
    lower_to_original = {path.casefold(): path for path in visible_files}
    basename_to_paths: dict[str, list[str]] = {}
    for path in visible_files:
        basename_to_paths.setdefault(Path(path).name.casefold(), []).append(path)

    frameworks = {
        label
        for dep_name, label in _FRONTEND_DEPENDENCY_MAP.items()
        if dep_name in npm_dependencies
    }
    signal_files = [
        path
        for name in _FRONTEND_CONFIG_FILES
        for path in basename_to_paths.get(name.casefold(), [])
    ]

    styling_systems = {
        label
        for dep_name, label in _STYLING_DEPENDENCY_MAP.items()
        if dep_name in npm_dependencies
    }
    style_file_count = sum(
        1 for path in visible_files if Path(path).suffix.casefold() in _STYLE_EXTENSIONS
    )
    if style_file_count > 0:
        styling_systems.add("css")

    has_frontend_dirs = any(
        key in lower_to_original
        for key in (
            "src/app/page.tsx",
            "src/app/layout.tsx",
            "app/page.tsx",
            "app/layout.tsx",
            "pages/index.tsx",
            "pages/_app.tsx",
        )
    )
    detected = bool(frameworks or signal_files or has_frontend_dirs)

    # Tailwind configs should always imply tailwind styling classification.
    if any(Path(path).name.casefold().startswith("tailwind.config") for path in signal_files):
        styling_systems.add("tailwindcss")

    return {
        "detected": detected,
        "frameworks": _sorted_unique(frameworks),
        "styling_systems": _sorted_unique(styling_systems),
        "signal_files": _sorted_unique(signal_files),
        "style_file_count": style_file_count,
    }


def _build_python_profile(visible_files: list[str], managers: list[str]) -> dict[str, Any]:
    packaging_files: list[str] = []
    task_runner_files: list[str] = []
    tooling_files: list[str] = []

    for path in visible_files:
        file_name = Path(path).name.casefold()
        if file_name in _PYTHON_PACKAGING_FILES:
            packaging_files.append(path)
            continue
        if file_name.startswith("requirements") and file_name.endswith((".txt", ".in")):
            packaging_files.append(path)
            continue
        if file_name in _PYTHON_TASK_RUNNER_FILES:
            task_runner_files.append(path)
            continue
        if file_name in _PYTHON_TOOLING_FILES:
            tooling_files.append(path)

    matching_managers = [
        manager
        for manager in managers
        if manager.casefold() in _PYTHON_MANAGERS
    ]
    detected = bool(packaging_files or task_runner_files or tooling_files or matching_managers)

    return {
        "detected": detected,
        "managers": _sorted_unique(matching_managers),
        "packaging_files": _sorted_unique(packaging_files),
        "task_runner_files": _sorted_unique(task_runner_files),
        "tooling_files": _sorted_unique(tooling_files),
    }


def _detected_types(*, frontend_profile: Mapping[str, Any], python_profile: Mapping[str, Any]) -> list[str]:
    detected_types: list[str] = []
    frontend_detected = bool(frontend_profile.get("detected"))
    python_detected = bool(python_profile.get("detected"))
    frontend_frameworks = {
        str(value).casefold()
        for value in (frontend_profile.get("frameworks") or [])
        if isinstance(value, str)
    }

    if frontend_detected:
        detected_types.append("frontend-web")
        if "nextjs" in frontend_frameworks:
            detected_types.append("frontend-nextjs")
    if python_detected:
        detected_types.append("python")
    if frontend_detected and python_detected:
        detected_types.append("polyglot")
    if not detected_types:
        detected_types.append("generic")
    return detected_types


def _manifest_records(dependency_info: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    if not isinstance(dependency_info, Mapping):
        return []
    manifests = dependency_info.get("manifests")
    if not isinstance(manifests, list):
        return []
    return [entry for entry in manifests if isinstance(entry, Mapping)]


def _dependency_managers(dependency_info: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(dependency_info, Mapping):
        return []
    summary = dependency_info.get("summary")
    if not isinstance(summary, Mapping):
        return []
    return _sorted_unique(
        manager
        for manager in summary
        if isinstance(manager, str) and manager.strip()
    )


def _manifest_types(manifests: list[Mapping[str, Any]]) -> list[str]:
    return _sorted_unique(
        str(manifest_type)
        for manifest in manifests
        for manifest_type in (manifest.get("type"),)
        if isinstance(manifest_type, str) and manifest_type.strip()
    )


def _manifest_paths(manifests: list[Mapping[str, Any]], *, target_directory: Path) -> list[str]:
    paths: list[str] = []
    for manifest in manifests:
        path_value = manifest.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            continue
        normalized = _normalize_path(path_value, target_directory=target_directory)
        paths.append(normalized)
    return _sorted_unique(paths)


def _normalize_path(path_value: str, *, target_directory: Path) -> str:
    path = Path(path_value)
    if path.is_absolute():
        try:
            return path.relative_to(target_directory).as_posix()
        except ValueError:
            return path.as_posix()
    return path.as_posix()


def _npm_dependency_names(manifests: list[Mapping[str, Any]]) -> set[str]:
    names: set[str] = set()
    for manifest in manifests:
        manager = manifest.get("manager")
        if not isinstance(manager, str) or manager.casefold() != "npm":
            continue

        data = manifest.get("data")
        if not isinstance(data, Mapping):
            continue

        for section in data.values():
            if not isinstance(section, Mapping):
                continue
            for dependency_name in section:
                if isinstance(dependency_name, str) and dependency_name.strip():
                    names.add(dependency_name)
    return names


def _sorted_unique(values: Iterable[str]) -> list[str]:
    return sorted({value for value in values if value})
