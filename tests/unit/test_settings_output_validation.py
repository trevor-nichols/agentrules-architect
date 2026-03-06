from agentrules.cli.ui.settings.outputs import (
    _validate_positive_depth_input,
    _validate_rules_filename_input,
    _validate_snapshot_filename_input,
)


def test_validate_snapshot_filename_input_rejects_reserved_names() -> None:
    assert isinstance(_validate_snapshot_filename_input(".cursorignore", rules_filename="AGENTS.md"), str)
    assert isinstance(_validate_snapshot_filename_input("phases_output", rules_filename="AGENTS.md"), str)
    assert isinstance(_validate_snapshot_filename_input(".", rules_filename="AGENTS.md"), str)
    assert isinstance(_validate_snapshot_filename_input("..", rules_filename="AGENTS.md"), str)


def test_validate_snapshot_filename_input_rejects_rules_collision() -> None:
    result = _validate_snapshot_filename_input("agents.md", rules_filename="AGENTS.md")
    assert isinstance(result, str)


def test_validate_snapshot_filename_input_accepts_safe_filename() -> None:
    assert _validate_snapshot_filename_input("SNAPSHOT.custom.md", rules_filename="AGENTS.md") is True


def test_validate_rules_filename_input_rejects_snapshot_collision() -> None:
    result = _validate_rules_filename_input("snapshot.md", snapshot_filename="SNAPSHOT.md")
    assert isinstance(result, str)


def test_validate_rules_filename_input_rejects_paths() -> None:
    result = _validate_rules_filename_input("nested/AGENTS.md", snapshot_filename="SNAPSHOT.md")
    assert isinstance(result, str)


def test_validate_positive_depth_input_rejects_invalid_values() -> None:
    assert isinstance(_validate_positive_depth_input(""), str)
    assert isinstance(_validate_positive_depth_input("abc"), str)
    assert isinstance(_validate_positive_depth_input("0"), str)


def test_validate_positive_depth_input_accepts_positive_integer() -> None:
    assert _validate_positive_depth_input("3") is True
