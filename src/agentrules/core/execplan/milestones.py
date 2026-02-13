"""Create, list, and archive ExecPlan milestones."""

from __future__ import annotations

import os
import re
import time
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from importlib import resources
from pathlib import Path
from string import Template
from typing import Any, BinaryIO, Literal, cast

import yaml

try:
    import fcntl
except ImportError:  # pragma: no cover - not available on Windows.
    fcntl = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - not available on POSIX.
    msvcrt = None

from agentrules.core.execplan.identity import extract_execplan_id_from_filename
from agentrules.core.execplan.paths import ACTIVE_DIR, ARCHIVE_DIR, MILESTONES_DIR, is_execplan_milestone_path
from agentrules.core.execplan.registry import ALLOWED_DOMAINS, DEFAULT_EXECPLANS_DIR

EXECPLAN_ID_RE = re.compile(r"^EP-\d{8}-\d{3}$")
MILESTONE_ID_RE = re.compile(r"^(?P<execplan_id>EP-\d{8}-\d{3})/MS(?P<ms>\d{3})$")
MILESTONE_FILENAME_RE = re.compile(
    r"^(?P<execplan_id>EP-\d{8}-\d{3})_MS(?P<ms>\d{3})(?:[_-](?P<slug>[A-Za-z0-9][A-Za-z0-9_-]*))?\.md$"
)
FRONT_MATTER_RE = re.compile(r"\A\s*---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)
DATE_YYYYMMDD_RE = re.compile(r"^\d{8}$")

_MILESTONE_CREATE_RETRIES = 32
_WINDOWS_LOCK_RETRIES = 200
_WINDOWS_LOCK_RETRY_DELAY_SECONDS = 0.05

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


def parse_milestone_id(value: str) -> tuple[str, int] | None:
    """Parse milestone ID in EP-YYYYMMDD-NNN/MS### format."""
    match = MILESTONE_ID_RE.fullmatch(value.strip())
    if match is None:
        return None
    return match.group("execplan_id"), int(match.group("ms"))


def parse_milestone_filename(filename: str) -> tuple[str, int, str | None] | None:
    """Parse milestone filename in EP-YYYYMMDD-NNN_MS###_<slug>.md format."""
    match = MILESTONE_FILENAME_RE.fullmatch(filename)
    if match is None:
        return None
    return match.group("execplan_id"), int(match.group("ms")), match.group("slug")


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
    relative = plan_path.relative_to(execplans_dir.resolve())
    if len(relative.parts) < 2:
        raise ValueError(
            f"ExecPlan file {plan_path.as_posix()} is not under expected <slug>/EP-... layout."
        )
    plan_root = (execplans_dir / relative.parts[0]).resolve()
    metadata = _extract_front_matter(plan_path.read_text(encoding="utf-8"))
    return plan_path, plan_root, metadata


def _iter_plan_milestone_files(*, plan_root: Path, execplan_id: str) -> list[Path]:
    milestones_root = (plan_root / MILESTONES_DIR).resolve()
    if not milestones_root.exists():
        return []

    files: list[Path] = []
    for candidate in milestones_root.rglob(f"{execplan_id}_MS*.md"):
        if not candidate.is_file():
            continue
        parsed = parse_milestone_filename(candidate.name)
        if parsed is None:
            continue
        parsed_execplan_id, _, _ = parsed
        if parsed_execplan_id != execplan_id:
            continue
        relative = candidate.resolve().relative_to(milestones_root)
        if not relative.parts:
            continue
        if relative.parts[0] not in {ACTIVE_DIR, ARCHIVE_DIR}:
            continue
        files.append(candidate.resolve())
    files.sort()
    return files


def _next_milestone_sequence(*, plan_root: Path, execplan_id: str) -> int:
    max_sequence = 0
    for candidate in _iter_plan_milestone_files(plan_root=plan_root, execplan_id=execplan_id):
        parsed = parse_milestone_filename(candidate.name)
        if parsed is None:
            continue
        _, sequence, _ = parsed
        max_sequence = max(max_sequence, sequence)
    return max_sequence + 1


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


def _acquire_windows_lock(lock_handle: BinaryIO) -> None:
    if msvcrt is None:
        raise RuntimeError("msvcrt backend is unavailable.")

    locking_func = getattr(msvcrt, "locking", None)
    nonblocking_lock_mode = getattr(msvcrt, "LK_NBLCK", None)
    if locking_func is None or nonblocking_lock_mode is None:
        raise RuntimeError("msvcrt backend does not expose required locking symbols.")

    lock = cast(Callable[[int, int, int], None], locking_func)

    lock_handle.seek(0, os.SEEK_END)
    if lock_handle.tell() == 0:
        lock_handle.write(b"\0")
        lock_handle.flush()
        os.fsync(lock_handle.fileno())

    for _ in range(_WINDOWS_LOCK_RETRIES):
        try:
            lock_handle.seek(0)
            lock(lock_handle.fileno(), int(nonblocking_lock_mode), 1)
            return
        except OSError:
            time.sleep(_WINDOWS_LOCK_RETRY_DELAY_SECONDS)

    raise TimeoutError("Could not acquire milestone lock within retry budget.")


def _release_windows_lock(lock_handle: BinaryIO) -> None:
    if msvcrt is None:
        raise RuntimeError("msvcrt backend is unavailable.")

    locking_func = getattr(msvcrt, "locking", None)
    unlock_mode = getattr(msvcrt, "LK_UNLCK", None)
    if locking_func is None or unlock_mode is None:
        raise RuntimeError("msvcrt backend does not expose required locking symbols.")

    lock = cast(Callable[[int, int, int], None], locking_func)
    lock_handle.seek(0)
    lock(lock_handle.fileno(), int(unlock_mode), 1)


@contextmanager
def _plan_milestone_lock(plan_root: Path):
    lock_path = plan_root / MILESTONES_DIR / ".milestones.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock_handle:
        if fcntl is not None:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        elif msvcrt is not None:
            _acquire_windows_lock(lock_handle)
        else:
            raise RuntimeError("No supported file-locking backend available for milestone sequencing.")
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
            elif msvcrt is not None:
                _release_windows_lock(lock_handle)


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
) -> MilestoneCreateResult:
    resolved_root = root.resolve()
    resolved_execplans_dir = _resolve_path(resolved_root, execplans_dir)
    plan_path, plan_root, parent_metadata = _resolve_parent_execplan(
        execplans_dir=resolved_execplans_dir,
        execplan_id=execplan_id,
    )

    normalized_title = _validate_single_line_field(title.strip(), field_name="title")
    if not normalized_title:
        raise ValueError("Title is required.")

    milestone_slug = _slugify(slug if slug is not None else normalized_title)
    if not milestone_slug:
        raise ValueError("Could not derive a valid slug; provide --slug using letters/numbers.")

    normalized_owner = _normalize_owner(owner, parent_metadata=parent_metadata)
    normalized_domain = _normalize_domain(domain, parent_metadata=parent_metadata)

    day_token = created_yyyymmdd or _today_yyyymmdd_local()
    day_value = _validate_date_yyyymmdd(day_token)
    created_updated = day_value.strftime("%Y-%m-%d")
    template = _load_milestone_template()

    active_dir = plan_root / MILESTONES_DIR / ACTIVE_DIR
    active_dir.mkdir(parents=True, exist_ok=True)

    with _plan_milestone_lock(plan_root):
        for _ in range(_MILESTONE_CREATE_RETRIES):
            sequence = _next_milestone_sequence(plan_root=plan_root, execplan_id=execplan_id)
            if sequence > 999:
                raise ValueError(f"Milestone sequence overflow for {execplan_id}; max is 999.")

            milestone_id = _milestone_id(execplan_id, sequence=sequence)
            filename = f"{execplan_id}_MS{sequence:03d}_{milestone_slug}.md"
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
        parsed_execplan_id, sequence, _ = parsed
        relative = path.relative_to(milestones_root)
        location: Literal["active", "archived"]
        if relative.parts and relative.parts[0] == ACTIVE_DIR:
            location = "active"
        elif relative.parts and relative.parts[0] == ARCHIVE_DIR:
            location = "archived"
        else:
            continue

        if location == "archived" and not include_archived:
            continue

        refs.append(
            MilestoneRef(
                milestone_id=_milestone_id(parsed_execplan_id, sequence=sequence),
                sequence=sequence,
                execplan_id=parsed_execplan_id,
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
    plan_path, plan_root, _ = _resolve_parent_execplan(
        execplans_dir=resolved_execplans_dir,
        execplan_id=execplan_id,
    )

    with _plan_milestone_lock(plan_root):
        active_dir = (plan_root / MILESTONES_DIR / ACTIVE_DIR).resolve()
        sequence_token = f"MS{sequence:03d}"
        candidates = [
            path.resolve()
            for path in active_dir.glob(f"{execplan_id}_{sequence_token}*.md")
            if path.is_file()
            and (
                (parsed := parse_milestone_filename(path.name)) is not None
                and parsed[0] == execplan_id
                and parsed[1] == sequence
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

        day_token = archive_date_yyyymmdd or _today_yyyymmdd_local()
        day_value = _validate_date_yyyymmdd(day_token)
        archive_dir = (
            plan_root
            / MILESTONES_DIR
            / ARCHIVE_DIR
            / day_value.strftime("%Y")
            / day_value.strftime("%m")
            / day_value.strftime("%d")
        )
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
