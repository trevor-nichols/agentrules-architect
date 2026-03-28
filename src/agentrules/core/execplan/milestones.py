"""Create, list, and complete ExecPlan milestones."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from importlib import resources
from pathlib import Path
from string import Template
from typing import Any, Literal

import yaml

from agentrules.core.execplan.identity import extract_execplan_id_from_filename
from agentrules.core.execplan.locks import execplan_mutation_lock
from agentrules.core.execplan.paths import (
    ACTIVE_DIR,
    COMPLETE_DIR,
    COMPLETE_DIR_ALIASES,
    MILESTONES_DIR,
    get_execplan_plan_root,
    is_execplan_complete_path,
    is_execplan_milestone_path,
)
from agentrules.core.execplan.registry import ALLOWED_DOMAINS, DEFAULT_EXECPLANS_DIR

EXECPLAN_ID_RE = re.compile(r"^EP-\d{8}-\d{3}$")
MILESTONE_ID_RE = re.compile(r"^(?P<execplan_id>EP-\d{8}-\d{3})/MS(?P<ms>\d{3})$")
LEGACY_MILESTONE_FILENAME_RE = re.compile(
    r"^(?P<execplan_id>EP-\d{8}-\d{3})_MS(?P<ms>\d{3})(?:[_-](?P<slug>[A-Za-z0-9][A-Za-z0-9_-]*))?\.md$"
)
MILESTONE_FILENAME_RE = re.compile(r"^MS(?P<ms>\d{3})(?:[_-](?P<slug>[A-Za-z0-9][A-Za-z0-9_-]*))?\.md$")
FRONT_MATTER_RE = re.compile(r"\A\s*---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)
DATE_YYYYMMDD_RE = re.compile(r"^\d{8}$")

_MILESTONE_CREATE_RETRIES = 32

_TEMPLATE_PACKAGE = "agentrules.core.execplan"
_MILESTONE_FILE_TEMPLATE_NAME = "MILESTONE_FILE_TEMPLATE.md"


@dataclass(frozen=True, slots=True)
class MilestoneCreateResult:
    milestone_id: str
    sequence: int
    milestone_path: Path
    execplan_id: str
    plan_path: Path
    title: str


@dataclass(frozen=True, slots=True)
class MilestoneArchiveResult:
    milestone_id: str
    sequence: int
    source_path: Path
    archived_path: Path
    execplan_id: str
    plan_path: Path


@dataclass(frozen=True, slots=True)
class MilestoneRef:
    milestone_id: str
    sequence: int
    execplan_id: str
    location: Literal["active", "archived"]
    path: Path


@dataclass(frozen=True, slots=True)
class MilestoneFileScan:
    path: Path
    sequence: int
    location: Literal["active", "archived"]
    execplan_id: str | None
    parse_error: str | None


@dataclass(frozen=True, slots=True)
class ActiveMilestoneArchiveScanEntry:
    path: Path
    execplan_id: str | None
    milestone_id: str | None
    sequence: int | None
    parse_error: str | None


@dataclass(frozen=True, slots=True)
class ActiveMilestoneArchiveScan:
    active_milestones_for_execplan: tuple[ActiveMilestoneArchiveScanEntry, ...]
    blocking_entries: tuple[ActiveMilestoneArchiveScanEntry, ...]


def parse_milestone_id(value: str) -> tuple[str, int] | None:
    """Parse milestone ID in EP-YYYYMMDD-NNN/MS### format."""
    match = MILESTONE_ID_RE.fullmatch(value.strip())
    if match is None:
        return None
    return match.group("execplan_id"), int(match.group("ms"))


def parse_milestone_filename(filename: str) -> tuple[str | None, int, str | None] | None:
    """
    Parse milestone filename in either format:
    - MS###_<slug>.md (current)
    - EP-YYYYMMDD-NNN_MS###_<slug>.md (legacy)
    """
    legacy_match = LEGACY_MILESTONE_FILENAME_RE.fullmatch(filename)
    if legacy_match is not None:
        return legacy_match.group("execplan_id"), int(legacy_match.group("ms")), legacy_match.group("slug")

    match = MILESTONE_FILENAME_RE.fullmatch(filename)
    if match is None:
        return None
    return None, int(match.group("ms")), match.group("slug")


def _extract_milestone_execplan_id_with_error(path: Path) -> tuple[str | None, str | None]:
    try:
        metadata = _extract_front_matter(path.read_text(encoding="utf-8"))
    except OSError as error:
        return None, f"could not read milestone file: {error}"
    except UnicodeDecodeError:
        return None, "milestone file is not valid UTF-8"
    except ValueError as error:
        return None, str(error)

    candidate = str(metadata.get("execplan_id", "")).strip()
    if EXECPLAN_ID_RE.fullmatch(candidate) is None:
        return None, "front matter must include execplan_id in EP-YYYYMMDD-NNN format"
    return candidate, None


def _extract_milestone_execplan_id(path: Path) -> str | None:
    filename_id = extract_execplan_id_from_filename(path.name)
    if filename_id is not None:
        return filename_id
    candidate_id, _ = _extract_milestone_execplan_id_with_error(path)
    return candidate_id


def _is_milestone_owned_by_execplan(path: Path, *, execplan_id: str) -> bool:
    parsed = parse_milestone_filename(path.name)
    if parsed is None:
        return False
    parsed_execplan_id, _, _ = parsed
    if parsed_execplan_id is not None:
        return parsed_execplan_id == execplan_id
    return _extract_milestone_execplan_id(path) == execplan_id


def scan_plan_milestone_files(*, plan_root: Path) -> tuple[MilestoneFileScan, ...]:
    milestones_root = (plan_root / MILESTONES_DIR).resolve()
    if not milestones_root.exists():
        return ()

    scanned: list[MilestoneFileScan] = []
    for candidate in milestones_root.rglob("*.md"):
        if not candidate.is_file():
            continue

        parsed = parse_milestone_filename(candidate.name)
        if parsed is None:
            continue

        resolved_candidate = candidate.resolve()
        relative = resolved_candidate.relative_to(milestones_root)
        if not relative.parts or relative.parts[0] not in {ACTIVE_DIR, *COMPLETE_DIR_ALIASES}:
            continue

        location: Literal["active", "archived"]
        if relative.parts[0] == ACTIVE_DIR:
            location = "active"
        else:
            location = "archived"

        parsed_execplan_id, sequence, _ = parsed
        parse_error: str | None = None
        execplan_id = parsed_execplan_id
        if parsed_execplan_id is None:
            execplan_id, parse_error = _extract_milestone_execplan_id_with_error(resolved_candidate)

        scanned.append(
            MilestoneFileScan(
                path=resolved_candidate,
                sequence=sequence,
                location=location,
                execplan_id=execplan_id,
                parse_error=parse_error,
            )
        )

    scanned.sort(key=lambda item: (item.sequence, 0 if item.location == "active" else 1, item.path.as_posix()))
    return tuple(scanned)


def list_invalid_active_milestone_files(*, plan_root: Path) -> tuple[MilestoneFileScan, ...]:
    return tuple(
        file
        for file in scan_plan_milestone_files(plan_root=plan_root)
        if file.location == "active" and file.parse_error is not None
    )


def _scan_active_milestone_front_matter(path: Path) -> ActiveMilestoneArchiveScanEntry:
    try:
        metadata = _extract_front_matter(path.read_text(encoding="utf-8"))
    except OSError as error:
        return ActiveMilestoneArchiveScanEntry(
            path=path,
            execplan_id=None,
            milestone_id=None,
            sequence=None,
            parse_error=f"could not read milestone file: {error}",
        )
    except UnicodeDecodeError:
        return ActiveMilestoneArchiveScanEntry(
            path=path,
            execplan_id=None,
            milestone_id=None,
            sequence=None,
            parse_error="milestone file is not valid UTF-8",
        )
    except ValueError as error:
        return ActiveMilestoneArchiveScanEntry(
            path=path,
            execplan_id=None,
            milestone_id=None,
            sequence=None,
            parse_error=str(error),
        )

    execplan_id = str(metadata.get("execplan_id", "")).strip()
    if EXECPLAN_ID_RE.fullmatch(execplan_id) is None:
        return ActiveMilestoneArchiveScanEntry(
            path=path,
            execplan_id=None,
            milestone_id=None,
            sequence=None,
            parse_error="front matter must include execplan_id in EP-YYYYMMDD-NNN format",
        )

    milestone_id = str(metadata.get("id", "")).strip()
    parsed_milestone_id = parse_milestone_id(milestone_id)
    if parsed_milestone_id is None:
        return ActiveMilestoneArchiveScanEntry(
            path=path,
            execplan_id=execplan_id,
            milestone_id=milestone_id or None,
            sequence=None,
            parse_error="front matter must include id in EP-YYYYMMDD-NNN/MS### format",
        )

    parsed_execplan_id, sequence = parsed_milestone_id
    if parsed_execplan_id != execplan_id:
        return ActiveMilestoneArchiveScanEntry(
            path=path,
            execplan_id=execplan_id,
            milestone_id=milestone_id,
            sequence=sequence,
            parse_error="front matter id and execplan_id refer to different ExecPlan IDs",
        )

    return ActiveMilestoneArchiveScanEntry(
        path=path,
        execplan_id=execplan_id,
        milestone_id=milestone_id,
        sequence=sequence,
        parse_error=None,
    )


def scan_active_milestones_for_archive(*, plan_root: Path, execplan_id: str) -> ActiveMilestoneArchiveScan:
    """
    Scan milestones/active for completion safety checks using front matter as source of truth.
    """
    active_root = (plan_root / MILESTONES_DIR / ACTIVE_DIR).resolve()
    if not active_root.exists():
        return ActiveMilestoneArchiveScan(active_milestones_for_execplan=(), blocking_entries=())

    active_milestones_for_execplan: list[ActiveMilestoneArchiveScanEntry] = []
    blocking_entries: list[ActiveMilestoneArchiveScanEntry] = []

    for candidate in active_root.rglob("*.md"):
        if not candidate.is_file():
            continue
        scanned = _scan_active_milestone_front_matter(candidate.resolve())
        if scanned.parse_error is not None:
            blocking_entries.append(scanned)
            continue
        if scanned.execplan_id != execplan_id:
            blocking_entries.append(
                ActiveMilestoneArchiveScanEntry(
                    path=scanned.path,
                    execplan_id=scanned.execplan_id,
                    milestone_id=scanned.milestone_id,
                    sequence=scanned.sequence,
                    parse_error=f"active milestone is owned by different ExecPlan ID {scanned.execplan_id!r}",
                )
            )
            continue
        active_milestones_for_execplan.append(scanned)

    active_milestones_for_execplan.sort(
        key=lambda item: (
            item.sequence if item.sequence is not None else -1,
            item.path.as_posix(),
        )
    )
    blocking_entries.sort(
        key=lambda item: (
            item.sequence if item.sequence is not None else -1,
            item.path.as_posix(),
        )
    )
    return ActiveMilestoneArchiveScan(
        active_milestones_for_execplan=tuple(active_milestones_for_execplan),
        blocking_entries=tuple(blocking_entries),
    )


def _resolve_path(root: Path, value: Path) -> Path:
    return value.resolve() if value.is_absolute() else (root / value).resolve()


def _today_yyyymmdd_local() -> str:
    return datetime.now().astimezone().strftime("%Y%m%d")


def _validate_date_yyyymmdd(value: str) -> datetime:
    if DATE_YYYYMMDD_RE.fullmatch(value) is None:
        raise ValueError(f"Date must use YYYYMMDD format (got {value!r}).")
    try:
        return datetime.strptime(value, "%Y%m%d")
    except ValueError as error:
        raise ValueError(f"Date must use YYYYMMDD format (got {value!r}).") from error


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


def _load_milestone_template() -> Template:
    template_path = resources.files(_TEMPLATE_PACKAGE).joinpath("templates", _MILESTONE_FILE_TEMPLATE_NAME)
    if not template_path.is_file():
        raise FileNotFoundError(f"Template not found: {_MILESTONE_FILE_TEMPLATE_NAME}")
    return Template(template_path.read_text(encoding="utf-8"))


def _extract_front_matter(content: str) -> dict[str, Any]:
    match = FRONT_MATTER_RE.search(content)
    if match is None:
        return {}
    try:
        loaded = yaml.safe_load(match.group(1))
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid YAML front matter: {error}") from error
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError("Front matter must be a YAML mapping/object.")
    metadata: dict[str, Any] = {}
    for key, value in loaded.items():
        if not isinstance(key, str):
            raise ValueError(f"Front matter keys must be strings (got {type(key).__name__}).")
        metadata[key] = value
    return metadata


def _resolve_parent_execplan(
    *,
    execplans_dir: Path,
    execplan_id: str,
) -> tuple[Path, Path, dict[str, Any]]:
    if EXECPLAN_ID_RE.fullmatch(execplan_id) is None:
        raise ValueError(f"Invalid ExecPlan ID {execplan_id!r}. Expected EP-YYYYMMDD-NNN.")

    if not execplans_dir.exists():
        raise FileNotFoundError(f"ExecPlans directory not found: {execplans_dir}")

    matches: list[Path] = []
    for candidate in execplans_dir.rglob("EP-*.md"):
        if not candidate.is_file() or is_execplan_milestone_path(candidate, execplans_root=execplans_dir):
            continue
        filename_id = extract_execplan_id_from_filename(candidate.name)
        if filename_id == execplan_id:
            matches.append(candidate.resolve())

    if not matches:
        raise FileNotFoundError(f"ExecPlan {execplan_id!r} was not found under {execplans_dir}.")

    matches.sort()
    if len(matches) > 1:
        joined = ", ".join(path.as_posix() for path in matches)
        raise ValueError(
            f"ExecPlan ID {execplan_id!r} resolved to multiple files. Resolve duplicates first: {joined}"
        )

    plan_path = matches[0]
    plan_root = get_execplan_plan_root(plan_path, execplans_root=execplans_dir)
    metadata = _extract_front_matter(plan_path.read_text(encoding="utf-8"))
    return plan_path, plan_root, metadata


def _ensure_execplan_mutable(
    *,
    execplan_id: str,
    plan_path: Path,
    metadata: dict[str, Any],
    execplans_dir: Path,
) -> None:
    if is_execplan_complete_path(plan_path, execplans_root=execplans_dir):
        raise ValueError(f"ExecPlan {execplan_id!r} is completed and cannot accept new milestones.")
    status = str(metadata.get("status", "")).strip().lower()
    if status == "archived":
        raise ValueError(f"ExecPlan {execplan_id!r} has archived status and cannot accept new milestones.")


def _uses_legacy_shared_active_root(*, plan_path: Path, plan_root: Path, execplans_dir: Path) -> bool:
    """
    Return True for legacy layout where multiple ExecPlans can share active/ as a single root.
    """
    legacy_active_root = (execplans_dir / ACTIVE_DIR).resolve()
    return plan_root == legacy_active_root and plan_path.parent.resolve() == legacy_active_root


def _iter_plan_milestone_files(*, plan_root: Path, execplan_id: str) -> list[Path]:
    files = [
        scanned.path
        for scanned in scan_plan_milestone_files(plan_root=plan_root)
        if scanned.execplan_id == execplan_id
    ]
    files.sort()
    return files


def _next_milestone_sequence(*, plan_root: Path, execplan_id: str) -> int:
    max_sequence = 0
    for scanned in scan_plan_milestone_files(plan_root=plan_root):
        if scanned.execplan_id == execplan_id:
            max_sequence = max(max_sequence, scanned.sequence)
            continue
        # Treat malformed active milestones as occupied sequence slots to prevent ID reuse.
        if scanned.location == "active" and scanned.parse_error is not None:
            max_sequence = max(max_sequence, scanned.sequence)
    return max_sequence + 1


def _validate_requested_sequence(
    *,
    requested_sequence: int,
    plan_root: Path,
    execplan_id: str,
) -> None:
    if requested_sequence < 1 or requested_sequence > 999:
        raise ValueError("Milestone sequence must be between 1 and 999.")

    collisions: list[Path] = []
    for scanned in scan_plan_milestone_files(plan_root=plan_root):
        if scanned.sequence != requested_sequence:
            continue
        if scanned.execplan_id == execplan_id:
            collisions.append(scanned.path)
            continue
        # For malformed active files we cannot trust ownership metadata.
        if scanned.location == "active" and scanned.parse_error is not None:
            collisions.append(scanned.path)

    if collisions:
        joined = ", ".join(path.as_posix() for path in sorted(collisions))
        raise ValueError(
            f"Milestone {execplan_id}/MS{requested_sequence:03d} already exists or is blocked by "
            f"invalid active metadata: {joined}"
        )


def _normalize_domain(domain: str | None, *, parent_metadata: dict[str, Any]) -> str:
    fallback = str(parent_metadata.get("domain", "")).strip()
    normalized = (domain if domain is not None else fallback or "backend").strip()
    if normalized not in ALLOWED_DOMAINS:
        raise ValueError(f"Invalid domain {normalized!r}. Allowed: {sorted(ALLOWED_DOMAINS)}")
    return normalized


def _normalize_owner(owner: str | None, *, parent_metadata: dict[str, Any]) -> str:
    fallback = str(parent_metadata.get("owner", "")).strip()
    chosen_owner = (owner if owner is not None else fallback or "@codex").strip()
    normalized = _validate_single_line_field(chosen_owner, field_name="owner")
    if not normalized:
        raise ValueError("Owner must be non-empty.")
    return normalized


def _milestone_id(execplan_id: str, *, sequence: int) -> str:
    return f"{execplan_id}/MS{sequence:03d}"


def create_execplan_milestone(
    *,
    root: Path,
    execplan_id: str,
    title: str,
    slug: str | None = None,
    owner: str | None = None,
    domain: str | None = None,
    execplans_dir: Path = DEFAULT_EXECPLANS_DIR,
    created_yyyymmdd: str | None = None,
    sequence: int | None = None,
) -> MilestoneCreateResult:
    resolved_root = root.resolve()
    resolved_execplans_dir = _resolve_path(resolved_root, execplans_dir)

    normalized_title = _validate_single_line_field(title.strip(), field_name="title")
    if not normalized_title:
        raise ValueError("Title is required.")

    milestone_slug = _slugify(slug if slug is not None else normalized_title)
    if not milestone_slug:
        raise ValueError("Could not derive a valid slug; provide --slug using letters/numbers.")

    day_token = created_yyyymmdd or _today_yyyymmdd_local()
    day_value = _validate_date_yyyymmdd(day_token)
    created_updated = day_value.strftime("%Y-%m-%d")
    template = _load_milestone_template()

    with execplan_mutation_lock(execplans_dir=resolved_execplans_dir, execplan_id=execplan_id):
        plan_path, plan_root, parent_metadata = _resolve_parent_execplan(
            execplans_dir=resolved_execplans_dir,
            execplan_id=execplan_id,
        )
        _ensure_execplan_mutable(
            execplan_id=execplan_id,
            plan_path=plan_path,
            metadata=parent_metadata,
            execplans_dir=resolved_execplans_dir,
        )
        normalized_owner = _normalize_owner(owner, parent_metadata=parent_metadata)
        normalized_domain = _normalize_domain(domain, parent_metadata=parent_metadata)
        active_dir = plan_root / MILESTONES_DIR / ACTIVE_DIR
        active_dir.mkdir(parents=True, exist_ok=True)
        invalid_active_milestones = list_invalid_active_milestone_files(plan_root=plan_root)
        if invalid_active_milestones:
            joined = ", ".join(
                f"{file.path.as_posix()} ({file.parse_error})"
                for file in invalid_active_milestones
            )
            raise ValueError(
                "Cannot create milestone because active milestone metadata is invalid. "
                f"Fix these files first: {joined}"
            )
        uses_legacy_filename = _uses_legacy_shared_active_root(
            plan_path=plan_path,
            plan_root=plan_root,
            execplans_dir=resolved_execplans_dir,
        )
        if sequence is not None:
            _validate_requested_sequence(
                requested_sequence=sequence,
                plan_root=plan_root,
                execplan_id=execplan_id,
            )
            milestone_id = _milestone_id(execplan_id, sequence=sequence)
            if uses_legacy_filename:
                filename = f"{execplan_id}_MS{sequence:03d}_{milestone_slug}.md"
            else:
                filename = f"MS{sequence:03d}_{milestone_slug}.md"
            milestone_path = active_dir / filename
            content = template.substitute(
                {
                    "milestone_id": milestone_id,
                    "execplan_id": execplan_id,
                    "ms": str(sequence),
                    "title_yaml": _yaml_dquote(normalized_title),
                    "title_text": normalized_title,
                    "domain": normalized_domain,
                    "owner_yaml": _yaml_dquote(normalized_owner),
                    "created": created_updated,
                    "updated": created_updated,
                }
            )
            try:
                with milestone_path.open("x", encoding="utf-8") as handle:
                    handle.write(content)
            except FileExistsError as error:
                raise ValueError(
                    f"Milestone {execplan_id}/MS{sequence:03d} already exists at {milestone_path.as_posix()}."
                ) from error

            return MilestoneCreateResult(
                milestone_id=milestone_id,
                sequence=sequence,
                milestone_path=milestone_path.resolve(),
                execplan_id=execplan_id,
                plan_path=plan_path,
                title=normalized_title,
            )

        for _ in range(_MILESTONE_CREATE_RETRIES):
            sequence = _next_milestone_sequence(plan_root=plan_root, execplan_id=execplan_id)
            if sequence > 999:
                raise ValueError(f"Milestone sequence overflow for {execplan_id}; max is 999.")

            milestone_id = _milestone_id(execplan_id, sequence=sequence)
            if uses_legacy_filename:
                filename = f"{execplan_id}_MS{sequence:03d}_{milestone_slug}.md"
            else:
                filename = f"MS{sequence:03d}_{milestone_slug}.md"
            milestone_path = active_dir / filename
            content = template.substitute(
                {
                    "milestone_id": milestone_id,
                    "execplan_id": execplan_id,
                    "ms": str(sequence),
                    "title_yaml": _yaml_dquote(normalized_title),
                    "title_text": normalized_title,
                    "domain": normalized_domain,
                    "owner_yaml": _yaml_dquote(normalized_owner),
                    "created": created_updated,
                    "updated": created_updated,
                }
            )

            try:
                with milestone_path.open("x", encoding="utf-8") as handle:
                    handle.write(content)
            except FileExistsError:
                continue

            return MilestoneCreateResult(
                milestone_id=milestone_id,
                sequence=sequence,
                milestone_path=milestone_path.resolve(),
                execplan_id=execplan_id,
                plan_path=plan_path,
                title=normalized_title,
            )

    raise FileExistsError("Could not allocate a unique milestone ID due to concurrent writes. Retry the command.")


def list_execplan_milestones(
    *,
    root: Path,
    execplan_id: str,
    execplans_dir: Path = DEFAULT_EXECPLANS_DIR,
    include_archived: bool = True,
) -> tuple[MilestoneRef, ...]:
    resolved_root = root.resolve()
    resolved_execplans_dir = _resolve_path(resolved_root, execplans_dir)
    _, plan_root, _ = _resolve_parent_execplan(
        execplans_dir=resolved_execplans_dir,
        execplan_id=execplan_id,
    )

    milestones_root = (plan_root / MILESTONES_DIR).resolve()
    refs: list[MilestoneRef] = []
    for path in _iter_plan_milestone_files(plan_root=plan_root, execplan_id=execplan_id):
        parsed = parse_milestone_filename(path.name)
        if parsed is None:
            continue
        _, sequence, _ = parsed
        relative = path.relative_to(milestones_root)
        location: Literal["active", "archived"]
        if relative.parts and relative.parts[0] == ACTIVE_DIR:
            location = "active"
        elif relative.parts and relative.parts[0] in COMPLETE_DIR_ALIASES:
            location = "archived"
        else:
            continue

        if location == "archived" and not include_archived:
            continue

        refs.append(
            MilestoneRef(
                milestone_id=_milestone_id(execplan_id, sequence=sequence),
                sequence=sequence,
                execplan_id=execplan_id,
                location=location,
                path=path,
            )
        )

    refs.sort(key=lambda item: (item.sequence, 0 if item.location == "active" else 1, item.path.as_posix()))
    return tuple(refs)


def archive_execplan_milestone(
    *,
    root: Path,
    execplan_id: str,
    sequence: int,
    execplans_dir: Path = DEFAULT_EXECPLANS_DIR,
    archive_date_yyyymmdd: str | None = None,
) -> MilestoneArchiveResult:
    if sequence < 1 or sequence > 999:
        raise ValueError("Milestone sequence must be between 1 and 999.")

    resolved_root = root.resolve()
    resolved_execplans_dir = _resolve_path(resolved_root, execplans_dir)
    with execplan_mutation_lock(execplans_dir=resolved_execplans_dir, execplan_id=execplan_id):
        plan_path, plan_root, _ = _resolve_parent_execplan(
            execplans_dir=resolved_execplans_dir,
            execplan_id=execplan_id,
        )
        active_dir = (plan_root / MILESTONES_DIR / ACTIVE_DIR).resolve()
        candidates = [
            path.resolve()
            for path in active_dir.glob("*.md")
            if path.is_file()
            and (
                (parsed := parse_milestone_filename(path.name)) is not None
                and parsed[1] == sequence
                and _is_milestone_owned_by_execplan(path.resolve(), execplan_id=execplan_id)
            )
        ]
        candidates.sort()
        if not candidates:
            raise FileNotFoundError(
                f"Active milestone {execplan_id}/MS{sequence:03d} was not found under {active_dir.as_posix()}."
            )
        if len(candidates) > 1:
            joined = ", ".join(path.as_posix() for path in candidates)
            raise ValueError(
                "Multiple active milestone files found for "
                f"{execplan_id}/MS{sequence:03d}. Resolve duplicates: {joined}"
            )

        # Keep `archive_date_yyyymmdd` for API compatibility even though complete
        # layout no longer shards by date.
        if archive_date_yyyymmdd is not None:
            _validate_date_yyyymmdd(archive_date_yyyymmdd)
        archive_dir = plan_root / MILESTONES_DIR / COMPLETE_DIR
        archive_dir.mkdir(parents=True, exist_ok=True)

        source_path = candidates[0]
        archived_path = (archive_dir / source_path.name).resolve()
        if archived_path.exists():
            raise FileExistsError(f"Archive destination already exists: {archived_path.as_posix()}")

        os.replace(source_path, archived_path)
    return MilestoneArchiveResult(
        milestone_id=_milestone_id(execplan_id, sequence=sequence),
        sequence=sequence,
        source_path=source_path,
        archived_path=archived_path,
        execplan_id=execplan_id,
        plan_path=plan_path,
    )
