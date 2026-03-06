"""Release metadata validation for tag-driven GitHub releases."""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

_STABLE_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
_STABLE_TAG_PATTERN = re.compile(r"^v\d+\.\d+\.\d+$")


@dataclass(frozen=True)
class ReleaseMetadata:
    """Validated release information for a GitHub tag."""

    version: str
    tag: str


def read_project_version(pyproject_path: Path) -> str:
    """Read the project version from pyproject.toml."""

    with pyproject_path.open("rb") as handle:
        payload = tomllib.load(handle)

    project = payload.get("project")
    if not isinstance(project, dict):
        raise ValueError("pyproject.toml is missing a [project] table.")

    version = project.get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("pyproject.toml is missing project.version.")

    return version.strip()


def validate_release_tag(*, tag: str, version: str) -> ReleaseMetadata:
    """Validate that a release tag and project version match stable X.Y.Z format."""

    normalized_tag = tag.strip()
    normalized_version = version.strip()

    if not _STABLE_VERSION_PATTERN.fullmatch(normalized_version):
        raise ValueError(
            "Automated GitHub releases require [project].version to use stable X.Y.Z format; "
            f"found '{normalized_version}'."
        )

    if not _STABLE_TAG_PATTERN.fullmatch(normalized_tag):
        raise ValueError(
            "Automated GitHub releases require tags in vX.Y.Z format; "
            f"found '{normalized_tag}'."
        )

    expected_tag = f"v{normalized_version}"
    if normalized_tag != expected_tag:
        raise ValueError(
            f"Release tag '{normalized_tag}' does not match project version '{normalized_version}'. "
            f"Expected '{expected_tag}'."
        )

    return ReleaseMetadata(version=normalized_version, tag=normalized_tag)


def write_github_outputs(output_path: Path, metadata: ReleaseMetadata) -> None:
    """Write GitHub Actions outputs for downstream workflow steps."""

    lines = [
        f"version={metadata.version}",
        f"tag={metadata.tag}",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a GitHub release tag against pyproject.toml version."
    )
    parser.add_argument(
        "--tag",
        required=True,
        help="Release tag to validate, for example v3.2.3.",
    )
    parser.add_argument(
        "--pyproject",
        default="pyproject.toml",
        help="Path to the pyproject.toml file to validate.",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional path to the GitHub Actions output file.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    pyproject_path = Path(args.pyproject)
    try:
        version = read_project_version(pyproject_path)
        metadata = validate_release_tag(tag=args.tag, version=version)
    except (OSError, tomllib.TOMLDecodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.github_output:
        write_github_outputs(Path(args.github_output), metadata)

    print(f"Validated release tag {metadata.tag} for version {metadata.version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
