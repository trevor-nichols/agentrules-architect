"""Create ExecPlan documents and optionally refresh the ExecPlan registry."""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime
from importlib import resources
from pathlib import Path
from string import Template
from typing import Literal

import yaml

from agentrules.core.execplan.identity import extract_execplan_id_from_filename, parse_execplan_filename
from agentrules.core.execplan.locks import execplan_mutation_lock
from agentrules.core.execplan.milestones import scan_active_milestones_for_archive
from agentrules.core.execplan.paths import (
    EXECPLAN_ACTIVE_DIR,
    EXECPLAN_ARCHIVE_DIR,
    EXECPLAN_COMPLETE_DIR,
    MILESTONE_LOCATION_DIRS,
    MILESTONES_DIR,
    get_execplan_plan_root,
    is_execplan_complete_path,
    is_execplan_milestone_path,
)
from agentrules.core.execplan.registry import (
    ALLOWED_DOMAINS,
    ALLOWED_KINDS,
    DEFAULT_EXECPLANS_DIR,
    DEFAULT_REGISTRY_PATH,
    RegistryBuildResult,
    build_execplan_registry,
)

DATE_YYYYMMDD_RE = re.compile(r"^\d{8}$")
EXECPLAN_ID_RE = re.compile(r"^EP-\d{8}-\d{3}$")
FRONT_MATTER_RE = re.compile(r"\A\s*---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)
RESERVED_EXECPLAN_ROOT_SLUGS = frozenset(
    {EXECPLAN_ACTIVE_DIR, EXECPLAN_COMPLETE_DIR, EXECPLAN_ARCHIVE_DIR}
)
RESERVED_ACTIVE_PLAN_SLUGS = frozenset({MILESTONES_DIR})
_ARCHIVE_DESTINATION_DIRS = frozenset({EXECPLAN_COMPLETE_DIR, EXECPLAN_ARCHIVE_DIR})

_TEMPLATE_PACKAGE = "agentrules.core.execplan"
_TEMPLATE_NAME = "EXECPLAN_TEMPLATE.md"


@dataclass(frozen=True, slots=True)
class ExecPlanCreateResult:
    plan_id: str
    plan_path: Path
    slug: str
    registry_result: RegistryBuildResult | None = None


@dataclass(frozen=True, slots=True)
class ExecPlanArchiveResult:
    plan_id: str
    source_plan_path: Path
    archived_plan_path: Path
    source_plan_root: Path
    archived_plan_root: Path
    registry_result: RegistryBuildResult | None = None


def _today_yyyymmdd_local() -> str:
    return datetime.now().astimezone().strftime("%Y%m%d")


def _slugify(value: str) -> str:
    lowered = value.strip().lower()
    if not lowered:
        return ""
    collapsed = re.sub(r"\s+", "-", lowered)
    cleaned = re.sub(r"[^a-z0-9_-]+", "-", collapsed)
    deduped = re.sub(r"-{2,}", "-", cleaned)
    return deduped.strip("-_")


def _yaml_dquote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _validate_single_line_field(value: str, *, field_name: str) -> str:
    if any(char in value for char in ("\n", "\r", "\t")):
        raise ValueError(f"Field '{field_name}' must be a single-line value without control characters.")
    return value


def _validate_date_yyyymmdd(value: str) -> datetime:
    if DATE_YYYYMMDD_RE.fullmatch(value) is None:
        raise ValueError(f"Date must use YYYYMMDD format (got {value!r}).")
    try:
        return datetime.strptime(value, "%Y%m%d")
    except ValueError as error:
        raise ValueError(f"Date must use YYYYMMDD format (got {value!r}).") from error


def _next_sequence_for_date(execplans_dir: Path, date_yyyymmdd: str) -> int:
    max_sequence = 0
    for candidate in _iter_execplan_files(execplans_dir):
        parsed = parse_execplan_filename(candidate.name)
        if parsed is None:
            continue
        _, parsed_date, sequence = parsed
        if parsed_date != date_yyyymmdd:
            continue
        max_sequence = max(max_sequence, sequence)
    return max_sequence + 1


def _load_execplan_template() -> Template:
    template_path = resources.files(_TEMPLATE_PACKAGE).joinpath("templates", _TEMPLATE_NAME)
    if not template_path.is_file():
        raise FileNotFoundError(f"Template not found: {_TEMPLATE_NAME}")
    return Template(template_path.read_text(encoding="utf-8"))


def _resolve_path(root: Path, value: Path) -> Path:
    return value.resolve() if value.is_absolute() else (root / value).resolve()


def _normalize_archive_destination_dir(destination_dir: str) -> str:
    normalized = destination_dir.strip().lower()
    if normalized not in _ARCHIVE_DESTINATION_DIRS:
        allowed = ", ".join(sorted(_ARCHIVE_DESTINATION_DIRS))
        raise ValueError(
            f"Unsupported archive destination directory {destination_dir!r}. "
            f"Expected one of: {allowed}."
        )
    return normalized


def _iter_execplan_files(execplans_dir: Path) -> tuple[Path, ...]:
    return tuple(
        candidate.resolve()
        for candidate in execplans_dir.rglob("EP-*.md")
        if candidate.is_file() and not is_execplan_milestone_path(candidate, execplans_root=execplans_dir)
    )


def _resolve_execplan_by_id(*, execplans_dir: Path, execplan_id: str) -> Path:
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
        raise ValueError(
            f"ExecPlan ID {execplan_id!r} resolved to multiple files. Resolve duplicates first: {joined}"
        )
    return matches[0]


def _iter_execplan_files_within_plan_root(*, plan_root: Path, execplans_dir: Path) -> tuple[Path, ...]:
    return tuple(
        candidate.resolve()
        for candidate in plan_root.rglob("EP-*.md")
        if candidate.is_file() and not is_execplan_milestone_path(candidate, execplans_root=execplans_dir)
    )


def _iter_foreign_milestone_files_within_plan_root(*, plan_root: Path, execplan_id: str) -> tuple[Path, ...]:
    """
    Return milestone artifacts under plan_root that belong to a different ExecPlan id.

    This detects both canonical and legacy-inherited milestone subtree shapes:
    - milestones/(active|complete|archive)/...
    - (active|complete|archive)/...  # when legacy milestones collide under modern slug roots
    """
    foreign: list[Path] = []
    resolved_plan_root = plan_root.resolve()
    for candidate in resolved_plan_root.rglob("*.md"):
        if not candidate.is_file():
            continue
        candidate_id = _extract_milestone_execplan_id(candidate.resolve())
        if candidate_id is None or candidate_id == execplan_id:
            continue
        relative_parts = candidate.resolve().relative_to(resolved_plan_root).parts
        if (
            len(relative_parts) >= 3
            and relative_parts[0] == MILESTONES_DIR
            and relative_parts[1] in MILESTONE_LOCATION_DIRS
        ):
            foreign.append(candidate.resolve())
            continue
        if len(relative_parts) >= 2 and relative_parts[0] in MILESTONE_LOCATION_DIRS:
            foreign.append(candidate.resolve())
            continue
    return tuple(sorted(foreign))


def _extract_milestone_execplan_id(path: Path) -> str | None:
    filename_id = extract_execplan_id_from_filename(path.name)
    if filename_id is not None:
        return filename_id
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    match = FRONT_MATTER_RE.search(content)
    if match is None:
        return None
    try:
        metadata = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None
    if not isinstance(metadata, dict):
        return None
    candidate = str(metadata.get("execplan_id", "")).strip()
    if EXECPLAN_ID_RE.fullmatch(candidate) is None:
        return None
    return candidate


def _iter_unexpected_entries_in_legacy_milestones_root(*, milestones_root: Path, execplan_id: str) -> tuple[Path, ...]:
    """
    Return files inside legacy active-root milestones that are not owned milestone files for execplan_id.
    """
    unexpected: list[Path] = []
    resolved_root = milestones_root.resolve()
    for candidate in resolved_root.rglob("*.md"):
        if not candidate.is_file():
            continue
        candidate_id = _extract_milestone_execplan_id(candidate.resolve())
        relative_parts = candidate.resolve().relative_to(resolved_root).parts
        allowed = (
            len(relative_parts) >= 2
            and relative_parts[0] in MILESTONE_LOCATION_DIRS
            and candidate_id == execplan_id
        )
        if not allowed:
            unexpected.append(candidate.resolve())
    return tuple(sorted(unexpected))


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_path = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)


def _mark_execplan_archived(*, plan_path: Path, updated_yyyy_mm_dd: str) -> None:
    content = plan_path.read_text(encoding="utf-8")
    match = FRONT_MATTER_RE.search(content)
    if match is None:
        raise ValueError(f"ExecPlan {plan_path.as_posix()} is missing YAML front matter.")

    metadata = yaml.safe_load(match.group(1))
    if not isinstance(metadata, dict):
        raise ValueError(f"ExecPlan {plan_path.as_posix()} has invalid YAML front matter.")

    metadata["status"] = "archived"
    metadata["updated"] = updated_yyyy_mm_dd
    updated_front_matter = yaml.safe_dump(metadata, sort_keys=False).strip()
    updated_content = f"{content[:match.start(1)]}{updated_front_matter}{content[match.end(1):]}"
    _atomic_write_text(plan_path, updated_content)


def create_execplan(
    *,
    root: Path,
    title: str,
    slug: str | None = None,
    owner: str = "@codex",
    kind: str = "feature",
    domain: str = "backend",
    date_yyyymmdd: str | None = None,
    execplans_dir: Path = DEFAULT_EXECPLANS_DIR,
    update_registry: bool = True,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    include_registry_timestamp: bool = False,
    fail_on_registry_warn: bool = False,
) -> ExecPlanCreateResult:
    resolved_root = root.resolve()
    resolved_execplans_dir = _resolve_path(resolved_root, execplans_dir)
    resolved_registry_path = _resolve_path(resolved_root, registry_path)

    normalized_title = _validate_single_line_field(title.strip(), field_name="title")
    if not normalized_title:
        raise ValueError("Title is required.")

    normalized_kind = kind.strip()
    if normalized_kind not in ALLOWED_KINDS:
        raise ValueError(f"Invalid kind {normalized_kind!r}. Allowed: {sorted(ALLOWED_KINDS)}")

    normalized_domain = domain.strip()
    if normalized_domain not in ALLOWED_DOMAINS:
        raise ValueError(f"Invalid domain {normalized_domain!r}. Allowed: {sorted(ALLOWED_DOMAINS)}")

    normalized_owner = _validate_single_line_field(owner.strip(), field_name="owner")
    if not normalized_owner:
        raise ValueError("Owner must be non-empty.")

    chosen_slug = _slugify(slug if slug is not None else normalized_title)
    if not chosen_slug:
        raise ValueError("Could not derive a valid slug; provide --slug using letters/numbers.")
    if chosen_slug in RESERVED_EXECPLAN_ROOT_SLUGS:
        raise ValueError(
            f"Slug {chosen_slug!r} is reserved for ExecPlan directory layout roots; choose a different slug."
        )
    if chosen_slug in RESERVED_ACTIVE_PLAN_SLUGS:
        raise ValueError(
            f"Slug {chosen_slug!r} is reserved for internal milestone namespace paths; choose a different slug."
        )

    day_token = date_yyyymmdd or _today_yyyymmdd_local()
    date_value = _validate_date_yyyymmdd(day_token)
    created_updated = date_value.strftime("%Y-%m-%d")

    resolved_execplans_dir.mkdir(parents=True, exist_ok=True)
    plan_root = resolved_execplans_dir / EXECPLAN_ACTIVE_DIR / chosen_slug
    existing_plan_files = ()
    if plan_root.exists():
        existing_plan_files = _iter_execplan_files_within_plan_root(
            plan_root=plan_root,
            execplans_dir=resolved_execplans_dir,
        )
    if existing_plan_files:
        existing_joined = ", ".join(path.as_posix() for path in sorted(existing_plan_files))
        raise ValueError(
            "Cannot create ExecPlan because the active slug directory already contains an ExecPlan file. "
            f"Slug: {chosen_slug!r}. Existing files: {existing_joined}. Use a new slug or complete/migrate the "
            "existing plan first."
        )

    sequence = _next_sequence_for_date(resolved_execplans_dir, day_token)
    if sequence > 999:
        raise ValueError(f"ExecPlan sequence overflow for {day_token}; max is 999.")

    plan_id = f"EP-{day_token}-{sequence:03d}"
    filename = f"{plan_id}_{chosen_slug}.md"
    plan_path = plan_root / filename
    plan_path.parent.mkdir(parents=True, exist_ok=True)

    content = _load_execplan_template().substitute(
        {
            "id": plan_id,
            "title_yaml": _yaml_dquote(normalized_title),
            "title_text": normalized_title,
            "kind": normalized_kind,
            "domain": normalized_domain,
            "owner_yaml": _yaml_dquote(normalized_owner),
            "created": created_updated,
            "updated": created_updated,
        }
    )

    with plan_path.open("x", encoding="utf-8") as handle:
        handle.write(content)

    registry_result: RegistryBuildResult | None = None
    if update_registry:
        registry_result = build_execplan_registry(
            root=resolved_root,
            execplans_dir=resolved_execplans_dir,
            output_path=resolved_registry_path,
            include_timestamp=include_registry_timestamp,
            fail_on_warn=fail_on_registry_warn,
        )

    return ExecPlanCreateResult(
        plan_id=plan_id,
        plan_path=plan_path,
        slug=chosen_slug,
        registry_result=registry_result,
    )


def archive_execplan(
    *,
    root: Path,
    execplan_id: str,
    execplans_dir: Path = DEFAULT_EXECPLANS_DIR,
    archive_date_yyyymmdd: str | None = None,
    destination_dir: Literal["complete", "archive"] = EXECPLAN_COMPLETE_DIR,
    update_registry: bool = True,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    include_registry_timestamp: bool = False,
    fail_on_registry_warn: bool = False,
) -> ExecPlanArchiveResult:
    resolved_root = root.resolve()
    resolved_execplans_dir = _resolve_path(resolved_root, execplans_dir)
    resolved_registry_path = _resolve_path(resolved_root, registry_path)

    archive_destination_dir = _normalize_archive_destination_dir(destination_dir)

    with execplan_mutation_lock(execplans_dir=resolved_execplans_dir, execplan_id=execplan_id):
        source_plan_path = _resolve_execplan_by_id(execplans_dir=resolved_execplans_dir, execplan_id=execplan_id)
        if is_execplan_complete_path(source_plan_path, execplans_root=resolved_execplans_dir):
            raise ValueError(f"ExecPlan {execplan_id!r} is already completed.")

        source_plan_root = get_execplan_plan_root(source_plan_path, execplans_root=resolved_execplans_dir)
        source_plan_path = source_plan_path.resolve()
        legacy_active_root = (
            source_plan_root == (resolved_execplans_dir / EXECPLAN_ACTIVE_DIR).resolve()
            and source_plan_path.parent == source_plan_root
        )
        if legacy_active_root:
            top_level_plan_files = tuple(
                candidate.resolve()
                for candidate in source_plan_root.glob("EP-*.md")
                if candidate.is_file()
                and not is_execplan_milestone_path(
                    candidate,
                    execplans_root=resolved_execplans_dir,
                )
            )
            if len(top_level_plan_files) != 1 or top_level_plan_files[0] != source_plan_path:
                joined = ", ".join(path.as_posix() for path in sorted(top_level_plan_files))
                raise ValueError(
                    "Cannot complete legacy active-root ExecPlan safely because multiple top-level ExecPlan files "
                    f"were found under {source_plan_root.as_posix()}: {joined}"
                )
        else:
            files_in_plan_root = _iter_execplan_files_within_plan_root(
                plan_root=source_plan_root,
                execplans_dir=resolved_execplans_dir,
            )
            if len(files_in_plan_root) != 1 or files_in_plan_root[0] != source_plan_path:
                joined = ", ".join(path.as_posix() for path in sorted(files_in_plan_root))
                raise ValueError(
                    "Cannot complete entire ExecPlan directory safely because it contains multiple ExecPlan files. "
                    f"Plan root: {source_plan_root.as_posix()}. Files: {joined}"
                )
            foreign_milestones = _iter_foreign_milestone_files_within_plan_root(
                plan_root=source_plan_root,
                execplan_id=execplan_id,
            )
            if foreign_milestones:
                joined = ", ".join(path.as_posix() for path in foreign_milestones)
                raise ValueError(
                    "Cannot complete ExecPlan safely because the plan root contains milestone files for other "
                    f"ExecPlan IDs. Plan root: {source_plan_root.as_posix()}. Files: {joined}"
                )

        active_milestone_scan = scan_active_milestones_for_archive(
            plan_root=source_plan_root,
            execplan_id=execplan_id,
        )
        if active_milestone_scan.blocking_entries:
            joined = ", ".join(
                f"{file.path.as_posix()} ({file.parse_error})"
                for file in active_milestone_scan.blocking_entries
            )
            raise ValueError(
                "Cannot complete ExecPlan because active milestone metadata is invalid. "
                "Fix or complete these milestones first. "
                f"ExecPlan: {execplan_id}. Invalid active milestones: {joined}"
            )

        active_milestones = active_milestone_scan.active_milestones_for_execplan
        if active_milestones:
            joined = ", ".join(file.path.as_posix() for file in active_milestones)
            raise ValueError(
                "Cannot complete ExecPlan while active milestones still exist. "
                "Complete those milestones first. "
                f"ExecPlan: {execplan_id}. Active milestones: {joined}"
            )

        day_token = archive_date_yyyymmdd or _today_yyyymmdd_local()
        day_value = _validate_date_yyyymmdd(day_token)
        archive_parent = (
            resolved_execplans_dir
            / archive_destination_dir
            / day_value.strftime("%Y")
            / day_value.strftime("%m")
            / day_value.strftime("%d")
        )

        archive_leaf = f"{execplan_id}_{source_plan_root.name}"
        archived_plan_root = (archive_parent / archive_leaf).resolve()
        if archived_plan_root == source_plan_root or archived_plan_root.is_relative_to(source_plan_root):
            raise ValueError(
                "Cannot complete ExecPlan safely because the destination resolves inside the source plan root. "
                "This usually indicates a legacy top-level slug that conflicts with the destination namespace "
                f"({archive_destination_dir!r}). Rename or migrate the "
                "legacy plan directory first."
            )
        if legacy_active_root:
            legacy_milestones_root = (source_plan_root / MILESTONES_DIR).resolve()
            if legacy_milestones_root.exists():
                unexpected_entries = _iter_unexpected_entries_in_legacy_milestones_root(
                    milestones_root=legacy_milestones_root,
                    execplan_id=execplan_id,
                )
                if unexpected_entries:
                    joined = ", ".join(path.as_posix() for path in unexpected_entries)
                    raise ValueError(
                        "Cannot complete legacy active-root ExecPlan because mixed ownership artifacts were found "
                        f"under {legacy_milestones_root.as_posix()}: {joined}"
                    )

            archive_parent.mkdir(parents=True, exist_ok=True)
            if archived_plan_root.exists():
                raise FileExistsError(f"Archive destination already exists: {archived_plan_root.as_posix()}")
            archived_plan_root.mkdir(parents=False, exist_ok=False)

            archived_plan_path = (archived_plan_root / source_plan_path.name).resolve()
            archived_milestones_root = (archived_plan_root / MILESTONES_DIR).resolve()
            moved_plan = False
            moved_milestones = False
            try:
                os.replace(source_plan_path, archived_plan_path)
                moved_plan = True
                if legacy_milestones_root.exists():
                    os.replace(legacy_milestones_root, archived_milestones_root)
                    moved_milestones = True

                _mark_execplan_archived(
                    plan_path=archived_plan_path,
                    updated_yyyy_mm_dd=day_value.strftime("%Y-%m-%d"),
                )
            except Exception as error:
                if moved_milestones:
                    try:
                        os.replace(archived_milestones_root, legacy_milestones_root)
                    except OSError as rollback_error:
                        raise RuntimeError(
                            "Legacy milestone subtree was moved but rollback did not succeed. "
                            f"Moved path: {archived_milestones_root.as_posix()}, rollback error: {rollback_error}"
                        ) from error
                if moved_plan:
                    try:
                        os.replace(archived_plan_path, source_plan_path)
                    except OSError as rollback_error:
                        raise RuntimeError(
                            "Legacy ExecPlan file was moved but rollback did not succeed. "
                            f"Moved path: {archived_plan_path.as_posix()}, rollback error: {rollback_error}"
                        ) from error
                try:
                    archived_plan_root.rmdir()
                except OSError:
                    pass
                raise
        else:
            archive_parent.mkdir(parents=True, exist_ok=True)
            if archived_plan_root.exists():
                raise FileExistsError(f"Archive destination already exists: {archived_plan_root.as_posix()}")

            moved = False
            try:
                os.replace(source_plan_root, archived_plan_root)
                moved = True
                archived_plan_path = (archived_plan_root / source_plan_path.relative_to(source_plan_root)).resolve()
                _mark_execplan_archived(
                    plan_path=archived_plan_path,
                    updated_yyyy_mm_dd=day_value.strftime("%Y-%m-%d"),
                )
            except Exception as error:
                if moved:
                    try:
                        os.replace(archived_plan_root, source_plan_root)
                    except OSError as rollback_error:
                        raise RuntimeError(
                            "ExecPlan directory was moved but metadata update failed, and rollback did not succeed. "
                            f"Moved path: {archived_plan_root.as_posix()}, rollback error: {rollback_error}"
                        ) from error
                raise

    registry_result: RegistryBuildResult | None = None
    if update_registry:
        registry_result = build_execplan_registry(
            root=resolved_root,
            execplans_dir=resolved_execplans_dir,
            output_path=resolved_registry_path,
            include_timestamp=include_registry_timestamp,
            fail_on_warn=fail_on_registry_warn,
        )

    return ExecPlanArchiveResult(
        plan_id=execplan_id,
        source_plan_path=source_plan_path,
        archived_plan_path=archived_plan_path,
        source_plan_root=source_plan_root,
        archived_plan_root=archived_plan_root,
        registry_result=registry_result,
    )
