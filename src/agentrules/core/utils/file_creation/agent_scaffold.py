"""Helpers for creating the optional .agent planning scaffold."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

AGENT_DIRNAME = ".agent"
TEMPLATES_DIRNAME = "templates"
PLANS_FILENAME = "PLANS.md"
MILESTONE_TEMPLATE_FILENAME = "MILESTONE_TEMPLATE.md"


def _load_template_text(template_name: str) -> str:
    template_path = resources.files("agentrules.core.utils.file_creation").joinpath(
        "templates",
        template_name,
    )
    if not template_path.is_file():
        raise FileNotFoundError(f"Template not found: {template_name}")
    return template_path.read_text(encoding="utf-8")


def _create_file_from_template_if_missing(destination: Path, template_name: str) -> bool:
    if destination.exists():
        if destination.is_file():
            return False
        raise IsADirectoryError(f"Destination exists but is not a file: {destination}")
    destination.write_text(_load_template_text(template_name), encoding="utf-8")
    return True


def create_agent_scaffold(target_directory: Path) -> tuple[bool, list[str]]:
    """Create .agent directories and template files without overwriting existing files."""
    try:
        agent_dir = target_directory / AGENT_DIRNAME
        templates_dir = agent_dir / TEMPLATES_DIRNAME
        agent_dir.mkdir(parents=True, exist_ok=True)
        templates_dir.mkdir(parents=True, exist_ok=True)

        files_to_create: tuple[tuple[Path, str], ...] = (
            (agent_dir / PLANS_FILENAME, PLANS_FILENAME),
            (templates_dir / MILESTONE_TEMPLATE_FILENAME, MILESTONE_TEMPLATE_FILENAME),
        )

        messages: list[str] = []
        for destination, template_name in files_to_create:
            created = _create_file_from_template_if_missing(destination, template_name)
            relative_path = destination.relative_to(target_directory).as_posix()
            if created:
                messages.append(f"Created {relative_path}")
            else:
                messages.append(f"Skipped {relative_path} (already exists)")

        return True, messages
    except Exception as error:  # pragma: no cover - defensive error boundary
        return False, [f"Failed to create .agent scaffold: {error}"]
