"""Create ExecPlan documents and optionally refresh the ExecPlan registry."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from importlib import resources
from pathlib import Path
from string import Template

from agentrules.core.execplan.identity import parse_execplan_filename
from agentrules.core.execplan.paths import is_execplan_milestone_path
from agentrules.core.execplan.registry import (
    ALLOWED_DOMAINS,
    ALLOWED_KINDS,
    DEFAULT_EXECPLANS_DIR,
    DEFAULT_REGISTRY_PATH,
    RegistryBuildResult,
    build_execplan_registry,
)

DATE_YYYYMMDD_RE = re.compile(r"^\d{8}$")

_TEMPLATE_PACKAGE = "agentrules.core.execplan"
_TEMPLATE_NAME = "EXECPLAN_TEMPLATE.md"


@dataclass(frozen=True, slots=True)
class ExecPlanCreateResult:
    plan_id: str
    plan_path: Path
    slug: str
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
    for candidate in execplans_dir.rglob("EP-*.md"):
        if not candidate.is_file() or is_execplan_milestone_path(candidate, execplans_root=execplans_dir):
            continue
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

    day_token = date_yyyymmdd or _today_yyyymmdd_local()
    date_value = _validate_date_yyyymmdd(day_token)
    created_updated = date_value.strftime("%Y-%m-%d")

    resolved_execplans_dir.mkdir(parents=True, exist_ok=True)
    sequence = _next_sequence_for_date(resolved_execplans_dir, day_token)
    if sequence > 999:
        raise ValueError(f"ExecPlan sequence overflow for {day_token}; max is 999.")

    plan_id = f"EP-{day_token}-{sequence:03d}"
    filename = f"{plan_id}_{chosen_slug}.md"
    plan_path = resolved_execplans_dir / chosen_slug / filename
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
