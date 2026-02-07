"""Build and validate the ExecPlan registry under .agent/exec_plans."""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Literal

import yaml

from agentrules.core.utils.execplan_identity import extract_execplan_id_from_filename
from agentrules.core.utils.execplan_paths import is_execplan_archive_path, is_execplan_milestone_path

FRONT_MATTER_RE = re.compile(r"\A\s*---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)
EXECPLAN_ID_RE = re.compile(r"^EP-\d{8}-\d{3}$")

REQUIRED_KEYS = frozenset(
    {
        "id",
        "title",
        "status",
        "kind",
        "domain",
        "owner",
        "created",
        "updated",
    }
)

ALLOWED_STATUSES = frozenset({"planned", "active", "paused", "done", "archived"})
ALLOWED_KINDS = frozenset({"feature", "refactor", "bugfix", "migration", "infra", "spike", "perf", "docs", "tests"})
ALLOWED_DOMAINS = frozenset({"backend", "frontend", "console", "infra", "cross-cutting"})
ALLOWED_TOUCHES = frozenset({"api", "db", "ui", "cli", "agents", "ops", "security", "tests", "docs"})
ALLOWED_RISK = frozenset({"low", "med", "high"})

DEFAULT_EXECPLANS_DIR = Path(".agent/exec_plans")
DEFAULT_REGISTRY_PATH = Path(".agent/exec_plans/registry.json")


def _resolve_path(root: Path, value: Path) -> Path:
    return value.resolve() if value.is_absolute() else (root / value).resolve()


@dataclass(frozen=True, slots=True)
class RegistryIssue:
    severity: Literal["warning", "error"]
    message: str
    path: str | None = None


@dataclass(frozen=True, slots=True)
class RegistryPlan:
    id: str
    title: str
    status: str
    kind: str
    domain: str
    owner: str
    created: str
    updated: str
    tags: tuple[str, ...]
    touches: tuple[str, ...]
    risk: str | None
    breaking: bool | None
    migration: bool | None
    links: dict[str, str]
    depends_on: tuple[str, ...]
    supersedes: tuple[str, ...]
    path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "kind": self.kind,
            "domain": self.domain,
            "owner": self.owner,
            "created": self.created,
            "updated": self.updated,
            "tags": list(self.tags),
            "touches": list(self.touches),
            "risk": self.risk,
            "breaking": self.breaking,
            "migration": self.migration,
            "links": dict(self.links),
            "depends_on": list(self.depends_on),
            "supersedes": list(self.supersedes),
            "path": self.path,
        }


@dataclass(frozen=True, slots=True)
class RegistryBuildResult:
    registry: dict[str, Any]
    issues: tuple[RegistryIssue, ...]
    output_path: Path | None = None
    wrote_registry: bool = False

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")


def _iso_utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_inline_list(raw: str) -> list[str]:
    value = raw.strip()
    if not value:
        return []
    if not (value.startswith("[") and value.endswith("]")):
        return [value]

    inner = value[1:-1].strip()
    if not inner:
        return []

    result: list[str] = []
    token = ""
    quote: str | None = None
    for char in inner:
        if char in {"'", '"'}:
            if quote is None:
                quote = char
                continue
            if quote == char:
                quote = None
                continue
        if char == "," and quote is None:
            cleaned = token.strip()
            if cleaned:
                result.append(cleaned)
            token = ""
            continue
        token += char

    cleaned = token.strip()
    if cleaned:
        result.append(cleaned)

    normalized: list[str] = []
    for item in result:
        stripped = item.strip()
        if (stripped.startswith("'") and stripped.endswith("'")) or (
            stripped.startswith('"') and stripped.endswith('"')
        ):
            stripped = stripped[1:-1]
        stripped = stripped.strip()
        if stripped:
            normalized.append(stripped)
    return normalized


def _parse_front_matter(yaml_text: str) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(yaml_text)
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


def _extract_front_matter(content: str) -> dict[str, Any]:
    match = FRONT_MATTER_RE.search(content)
    if match is None:
        raise ValueError("Missing YAML front matter. File must start with a '---' block.")
    return _parse_front_matter(match.group(1))


def _normalize_str_list(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, list):
        return tuple(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, str):
        parsed = _parse_inline_list(value)
        if len(parsed) == 1 and value.strip() == parsed[0]:
            return (parsed[0],)
        return tuple(parsed)
    return (str(value).strip(),) if str(value).strip() else ()


def _ensure_bool_or_none(value: Any) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "false"}:
            return lowered == "true"
    raise ValueError(f"Expected boolean or empty value, got {value!r}.")


def _ensure_date(value: Any, *, field_name: str) -> str:
    if isinstance(value, datetime):
        candidate = value.date().isoformat()
    elif isinstance(value, date):
        candidate = value.isoformat()
    elif isinstance(value, str) and value.strip():
        candidate = value.strip()
    else:
        raise ValueError(f"Field '{field_name}' must be a YYYY-MM-DD string.")

    try:
        datetime.strptime(candidate, "%Y-%m-%d")
    except ValueError as error:
        raise ValueError(f"Field '{field_name}' must be YYYY-MM-DD (got {candidate!r}).") from error
    return candidate


def _to_rel_posix(path: Path, root: Path) -> str:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError:
        return resolved_path.as_posix()


def _discover_execplan_files(execplans_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in execplans_dir.rglob("EP-*.md")
        if path.is_file() and not is_execplan_milestone_path(path, execplans_root=execplans_dir)
    )


def _build_plan(
    metadata: dict[str, Any],
    *,
    plan_path: Path,
    root: Path,
    execplans_dir: Path,
) -> tuple[RegistryPlan | None, tuple[RegistryIssue, ...]]:
    issues: list[RegistryIssue] = []
    path_text = _to_rel_posix(plan_path, root)

    missing = sorted(REQUIRED_KEYS - set(metadata.keys()))
    if missing:
        issues.append(RegistryIssue("error", f"Missing required front matter keys: {missing}.", path=path_text))
        return None, tuple(issues)

    plan_id = str(metadata["id"]).strip()
    if not EXECPLAN_ID_RE.match(plan_id):
        issues.append(
            RegistryIssue(
                "error",
                f"Invalid ExecPlan id '{plan_id}'. Expected format EP-YYYYMMDD-NNN.",
                path=path_text,
            )
        )

    filename_id = extract_execplan_id_from_filename(plan_path.name)
    if filename_id is None:
        issues.append(
            RegistryIssue(
                "error",
                f"Filename '{plan_path.name}' must start with canonical id EP-YYYYMMDD-NNN.",
                path=path_text,
            )
        )
    elif plan_id != filename_id:
        issues.append(
            RegistryIssue(
                "error",
                f"Front matter id '{plan_id}' must match filename id '{filename_id}'.",
                path=path_text,
            )
        )

    status = str(metadata["status"]).strip()
    if status not in ALLOWED_STATUSES:
        issues.append(
            RegistryIssue(
                "error",
                f"Invalid status '{status}'. Allowed values: {sorted(ALLOWED_STATUSES)}.",
                path=path_text,
            )
        )

    kind = str(metadata["kind"]).strip()
    if kind not in ALLOWED_KINDS:
        issues.append(
            RegistryIssue(
                "error",
                f"Invalid kind '{kind}'. Allowed values: {sorted(ALLOWED_KINDS)}.",
                path=path_text,
            )
        )

    domain = str(metadata["domain"]).strip()
    if domain not in ALLOWED_DOMAINS:
        issues.append(
            RegistryIssue(
                "error",
                f"Invalid domain '{domain}'. Allowed values: {sorted(ALLOWED_DOMAINS)}.",
                path=path_text,
            )
        )

    title = str(metadata["title"]).strip()
    owner = str(metadata["owner"]).strip()
    if not title:
        issues.append(RegistryIssue("error", "Field 'title' must be non-empty.", path=path_text))
    if not owner:
        issues.append(RegistryIssue("error", "Field 'owner' must be non-empty.", path=path_text))

    try:
        created = _ensure_date(metadata["created"], field_name="created")
        updated = _ensure_date(metadata["updated"], field_name="updated")
    except ValueError as error:
        issues.append(RegistryIssue("error", str(error), path=path_text))
        created = ""
        updated = ""

    tags = _normalize_str_list(metadata.get("tags"))
    touches = _normalize_str_list(metadata.get("touches"))
    for touch in touches:
        if touch not in ALLOWED_TOUCHES:
            issues.append(
                RegistryIssue(
                    "error",
                    f"Invalid touches entry '{touch}'. Allowed values: {sorted(ALLOWED_TOUCHES)}.",
                    path=path_text,
                )
            )

    risk_raw = metadata.get("risk")
    risk: str | None
    if risk_raw in (None, ""):
        risk = None
    else:
        risk = str(risk_raw).strip()
        if risk not in ALLOWED_RISK:
            issues.append(
                RegistryIssue(
                    "error",
                    f"Invalid risk '{risk}'. Allowed values: {sorted(ALLOWED_RISK)}.",
                    path=path_text,
                )
            )

    breaking: bool | None = None
    migration: bool | None = None
    try:
        breaking = _ensure_bool_or_none(metadata.get("breaking"))
        migration = _ensure_bool_or_none(metadata.get("migration"))
    except ValueError as error:
        issues.append(RegistryIssue("error", str(error), path=path_text))

    links_raw = metadata.get("links", {})
    links: dict[str, str] = {}
    if links_raw in (None, ""):
        links = {}
    elif isinstance(links_raw, dict):
        links = {str(key): str(value) for key, value in links_raw.items()}
    else:
        issues.append(RegistryIssue("error", "Field 'links' must be a mapping when provided.", path=path_text))

    depends_on = _normalize_str_list(metadata.get("depends_on"))
    supersedes = _normalize_str_list(metadata.get("supersedes"))

    in_archive = is_execplan_archive_path(plan_path, execplans_root=execplans_dir)
    if status == "archived" and not in_archive:
        issues.append(
            RegistryIssue(
                "warning",
                "status is 'archived' but plan file is not under an archive path.",
                path=path_text,
            )
        )
    if status != "archived" and in_archive:
        issues.append(
            RegistryIssue(
                "warning",
                "Plan file is under archive path but status is not 'archived'.",
                path=path_text,
            )
        )

    if any(issue.severity == "error" for issue in issues):
        return None, tuple(issues)

    return (
        RegistryPlan(
            id=plan_id,
            title=title,
            status=status,
            kind=kind,
            domain=domain,
            owner=owner,
            created=created,
            updated=updated,
            tags=tags,
            touches=touches,
            risk=risk,
            breaking=breaking,
            migration=migration,
            links=links,
            depends_on=depends_on,
            supersedes=supersedes,
            path=path_text,
        ),
        tuple(issues),
    )


def collect_execplan_registry(
    *,
    root: Path,
    execplans_dir: Path = DEFAULT_EXECPLANS_DIR,
    include_timestamp: bool = False,
) -> RegistryBuildResult:
    resolved_root = root.resolve()
    resolved_execplans_dir = _resolve_path(resolved_root, execplans_dir)
    if not resolved_execplans_dir.exists():
        raise FileNotFoundError(f"ExecPlans directory not found: {resolved_execplans_dir}")

    issues: list[RegistryIssue] = []
    plans: list[RegistryPlan] = []
    discovered = _discover_execplan_files(resolved_execplans_dir)

    for plan_path in discovered:
        path_text = _to_rel_posix(plan_path, resolved_root)
        try:
            content = plan_path.read_text(encoding="utf-8")
            metadata = _extract_front_matter(content)
        except Exception as error:
            issues.append(
                RegistryIssue(
                    "error",
                    f"Failed to parse ExecPlan front matter: {error}",
                    path=path_text,
                )
            )
            continue

        parsed_plan, plan_issues = _build_plan(
            metadata,
            plan_path=plan_path,
            root=resolved_root,
            execplans_dir=resolved_execplans_dir,
        )
        issues.extend(plan_issues)
        if parsed_plan is not None:
            plans.append(parsed_plan)

    by_id: dict[str, RegistryPlan] = {}
    for plan in plans:
        existing = by_id.get(plan.id)
        if existing is not None:
            issues.append(
                RegistryIssue(
                    "error",
                    (
                        f"Duplicate ExecPlan id '{plan.id}' found in "
                        f"'{existing.path}' and '{plan.path}'."
                    ),
                )
            )
        by_id[plan.id] = plan

    for plan in plans:
        for relation_name, related_ids in (("depends_on", plan.depends_on), ("supersedes", plan.supersedes)):
            for related_id in related_ids:
                if not EXECPLAN_ID_RE.match(related_id):
                    issues.append(
                        RegistryIssue(
                            "error",
                            f"Invalid {relation_name} id '{related_id}' in plan '{plan.id}'.",
                            path=plan.path,
                        )
                    )
                    continue
                if related_id not in by_id:
                    issues.append(
                        RegistryIssue(
                            "error",
                            f"Unknown {relation_name} id '{related_id}' referenced by '{plan.id}'.",
                            path=plan.path,
                        )
                    )

    ordered_plans = sorted(plans, key=lambda plan: plan.id)
    registry: dict[str, Any] = {
        "schema_version": 1,
        "plans": [plan.to_dict() for plan in ordered_plans],
    }
    if include_timestamp:
        registry["generated_at"] = _iso_utc_now()

    return RegistryBuildResult(
        registry=registry,
        issues=tuple(issues),
    )


def write_registry_atomic(registry: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_fd, temp_path = tempfile.mkstemp(prefix=".registry-", suffix=".json", dir=output_path.parent)
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as file_handle:
            file_handle.write(json.dumps(registry, indent=2, sort_keys=True))
            file_handle.write("\n")
            file_handle.flush()
            os.fsync(file_handle.fileno())
        os.replace(temp_path, output_path)
        return output_path
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def build_execplan_registry(
    *,
    root: Path,
    execplans_dir: Path = DEFAULT_EXECPLANS_DIR,
    output_path: Path = DEFAULT_REGISTRY_PATH,
    include_timestamp: bool = False,
    fail_on_warn: bool = False,
) -> RegistryBuildResult:
    resolved_root = root.resolve()
    resolved_execplans_dir = _resolve_path(resolved_root, execplans_dir)
    resolved_output_path = _resolve_path(resolved_root, output_path)

    result = collect_execplan_registry(
        root=resolved_root,
        execplans_dir=resolved_execplans_dir,
        include_timestamp=include_timestamp,
    )
    if result.error_count > 0:
        return result
    if fail_on_warn and result.warning_count > 0:
        return result

    written_path = write_registry_atomic(result.registry, resolved_output_path)
    return RegistryBuildResult(
        registry=result.registry,
        issues=result.issues,
        output_path=written_path,
        wrote_registry=True,
    )
