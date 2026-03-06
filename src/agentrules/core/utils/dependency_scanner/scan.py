"""High-level orchestration for dependency manifest scanning."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pathspec import PathSpec

from .discovery import iter_manifest_files
from .metadata import build_summary, infer_manifest_type
from .models import ManifestRecord
from .parsers import build_parser_registry
from .registry import ManifestParserRegistry

_DEFAULT_REGISTRY = build_parser_registry()


def collect_dependency_info(
    directory: Path,
    *,
    gitignore_spec: PathSpec | None = None,
    max_depth: int = 5,
    exclude_relative_paths: set[str] | None = None,
    registry: ManifestParserRegistry | None = None,
) -> dict[str, Any]:
    """Collect dependency manifest data from the target directory."""
    active_registry = registry or _DEFAULT_REGISTRY
    records: list[ManifestRecord] = []

    for manifest_path in iter_manifest_files(
        directory,
        gitignore_spec,
        max_depth=max_depth,
        exclude_relative_paths=exclude_relative_paths,
    ):
        record = _parse_manifest(manifest_path, active_registry)
        records.append(record)

    manifests = [record.to_dict() for record in records]
    summary = build_summary(records)

    return {"manifests": manifests, "summary": summary}


def _parse_manifest(path: Path, registry: ManifestParserRegistry) -> ManifestRecord:
    parser = registry.resolve(path)
    try:
        payload = parser(path)
    except Exception as exc:  # noqa: BLE001
        payload = {"error": f"{type(exc).__name__}: {exc}"}

    return ManifestRecord(
        path=path,
        type=str(payload.get("type") or infer_manifest_type(path)),
        manager=payload.get("manager"),
        data=payload.get("data"),
        raw_excerpt=payload.get("raw_excerpt"),
        error=payload.get("error"),
    )
