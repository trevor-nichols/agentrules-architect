import pytest

from agentrules.cli.services.output_validation import (
    validate_snapshot_filename_reserved,
)


@pytest.mark.parametrize("filename", [".", ".."])
def test_validate_snapshot_filename_reserved_rejects_dot_segments(filename: str) -> None:
    with pytest.raises(ValueError, match=r"must not be \. or \.\."):
        validate_snapshot_filename_reserved(filename)

