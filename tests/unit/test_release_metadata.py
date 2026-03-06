from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from agentrules.core.utils.release_metadata import (
    ReleaseMetadata,
    main,
    read_project_version,
    validate_release_tag,
    write_github_outputs,
)


def _write_pyproject(path: Path, version: str) -> None:
    path.write_text(
        textwrap.dedent(
            f"""
            [project]
            name = "agentrules"
            version = "{version}"
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


class ReleaseMetadataTests(unittest.TestCase):
    def test_read_project_version_returns_declared_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pyproject_path = Path(temp_dir) / "pyproject.toml"
            _write_pyproject(pyproject_path, "3.2.3")

            self.assertEqual(read_project_version(pyproject_path), "3.2.3")

    def test_validate_release_tag_accepts_matching_stable_version(self) -> None:
        metadata = validate_release_tag(tag="v3.2.3", version="3.2.3")

        self.assertEqual(metadata, ReleaseMetadata(version="3.2.3", tag="v3.2.3"))

    def test_validate_release_tag_rejects_non_stable_version(self) -> None:
        with self.assertRaisesRegex(ValueError, "stable X.Y.Z format"):
            validate_release_tag(tag="v3.2.3-rc.1", version="3.2.3-rc.1")

    def test_validate_release_tag_rejects_tag_version_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not match project version"):
            validate_release_tag(tag="v3.2.4", version="3.2.3")

    def test_write_github_outputs_writes_expected_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "github_output.txt"

            write_github_outputs(output_path, ReleaseMetadata(version="3.2.3", tag="v3.2.3"))

            self.assertEqual(output_path.read_text(encoding="utf-8"), "version=3.2.3\ntag=v3.2.3\n")

    def test_main_validates_tag_and_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            pyproject_path = temp_path / "pyproject.toml"
            output_path = temp_path / "github_output.txt"
            _write_pyproject(pyproject_path, "3.2.3")

            exit_code = main(
                [
                    "--tag",
                    "v3.2.3",
                    "--pyproject",
                    str(pyproject_path),
                    "--github-output",
                    str(output_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "version=3.2.3\ntag=v3.2.3\n")
