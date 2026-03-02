from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from agentrules.cli.services.output_validation import (
    validate_pipeline_output_filenames,
    validate_snapshot_filename_reserved,
)


@pytest.mark.parametrize("filename", [".", ".."])
def test_validate_snapshot_filename_reserved_rejects_dot_segments(filename: str) -> None:
    with pytest.raises(ValueError, match=r"must not be \. or \.\."):
        validate_snapshot_filename_reserved(filename)


def test_validate_pipeline_output_filenames_rejects_existing_directory_target() -> None:
    with TemporaryDirectory() as tmpdir:
        target_directory = Path(tmpdir)
        (target_directory / "snapshot").mkdir()
        with pytest.raises(ValueError, match=r"points to an existing directory"):
            validate_pipeline_output_filenames(
                target_directory=target_directory,
                rules_filename="AGENTS.md",
                snapshot_filename="snapshot",
                generate_snapshot=True,
            )


def test_validate_pipeline_output_filenames_allows_existing_file_target() -> None:
    with TemporaryDirectory() as tmpdir:
        target_directory = Path(tmpdir)
        (target_directory / "SNAPSHOT.md").write_text("existing\n", encoding="utf-8")
        validate_pipeline_output_filenames(
            target_directory=target_directory,
            rules_filename="AGENTS.md",
            snapshot_filename="SNAPSHOT.md",
            generate_snapshot=True,
        )
