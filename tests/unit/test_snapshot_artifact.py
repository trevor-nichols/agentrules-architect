import base64
import re
from pathlib import Path
from tempfile import TemporaryDirectory

from agentrules.core.utils.file_creation.snapshot_artifact import sync_snapshot_artifact


def test_sync_snapshot_artifact_preserves_comments_and_tracks_deltas() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        src = root / "src"
        src.mkdir()
        (src / "keep.py").write_text("print('keep')\n", encoding="utf-8")
        (src / "new.py").write_text("print('new')\n", encoding="utf-8")

        snapshot_path = root / "SNAPSHOT.md"
        snapshot_path.write_text(
            "\n".join(
                [
                    "<project_structure>",
                    "└── src  # source package",
                    "    ├── keep.py  # keep this comment",
                    "    └── removed.py  # removed file",
                    "</project_structure>",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        result = sync_snapshot_artifact(
            root,
            output_path=snapshot_path,
            tree_max_depth=4,
            exclude_dirs=set(),
            exclude_files=set(),
            exclude_extensions=set(),
            include_file_contents=True,
            write=True,
        )

        assert result.changed is True
        assert result.wrote is True
        assert "src/new.py" in result.added_paths
        assert "src/removed.py" in result.removed_paths
        assert result.preserved_comments >= 2

        content = snapshot_path.read_text(encoding="utf-8")
        assert "└── src  # source package" in content
        assert "keep.py  # keep this comment" in content
        assert "new.py  # " not in content
        assert '<file path="src/keep.py">' in content
        assert '<file path="src/new.py">' in content
        assert '<file path="SNAPSHOT.md">' not in content


def test_sync_snapshot_artifact_preserves_comment_for_paths_with_hashes() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "docs #draft.md").write_text("draft\n", encoding="utf-8")
        snapshot_path = root / "SNAPSHOT.md"
        snapshot_path.write_text(
            "\n".join(
                [
                    "<project_structure>",
                    "└── docs #draft.md  # keep this comment",
                    "</project_structure>",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        result = sync_snapshot_artifact(
            root,
            output_path=snapshot_path,
            tree_max_depth=4,
            exclude_dirs=set(),
            exclude_files=set(),
            exclude_extensions=set(),
            include_file_contents=False,
            write=True,
        )

        rendered = snapshot_path.read_text(encoding="utf-8")
        assert "└── docs #draft.md  # keep this comment" in rendered
        assert result.preserved_comments >= 1


def test_sync_snapshot_artifact_does_not_split_delimiter_text_in_file_name() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "foo  # bar.py").write_text("print('ok')\n", encoding="utf-8")
        snapshot_path = root / "SNAPSHOT.md"
        snapshot_path.write_text(
            "\n".join(
                [
                    "<project_structure>",
                    "└── foo  # bar.py",
                    "</project_structure>",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        result = sync_snapshot_artifact(
            root,
            output_path=snapshot_path,
            tree_max_depth=3,
            exclude_dirs=set(),
            exclude_files=set(),
            exclude_extensions=set(),
            include_file_contents=False,
            write=False,
        )

        assert result.added_paths == ()
        assert result.removed_paths == ()


def test_sync_snapshot_artifact_treats_ambiguous_delimiter_names_as_literal_entries() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "foo").write_text("plain\n", encoding="utf-8")
        (root / "foo  # bar.py").write_text("special\n", encoding="utf-8")
        snapshot_path = root / "SNAPSHOT.md"
        snapshot_path.write_text(
            "\n".join(
                [
                    "<project_structure>",
                    "├── foo",
                    "└── foo  # bar.py",
                    "</project_structure>",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        result = sync_snapshot_artifact(
            root,
            output_path=snapshot_path,
            tree_max_depth=3,
            exclude_dirs=set(),
            exclude_files=set(),
            exclude_extensions=set(),
            include_file_contents=False,
            write=False,
        )

        assert result.added_paths == ()
        assert result.removed_paths == ()


def test_sync_snapshot_artifact_preserves_trailing_slash_for_empty_directory() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "docs").mkdir()
        snapshot_path = root / "SNAPSHOT.md"
        snapshot_path.write_text(
            "\n".join(
                [
                    "<project_structure>",
                    "└── docs/  # keep slash style",
                    "</project_structure>",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        result = sync_snapshot_artifact(
            root,
            output_path=snapshot_path,
            tree_max_depth=3,
            exclude_dirs=set(),
            exclude_files=set(),
            exclude_extensions=set(),
            include_file_contents=False,
            write=True,
        )

        rendered = snapshot_path.read_text(encoding="utf-8")
        assert "└── docs/  # keep slash style" in rendered
        assert result.preserved_comments >= 1


def test_sync_snapshot_artifact_excludes_max_depth_marker_from_path_deltas() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        nested = root / "src" / "nested"
        nested.mkdir(parents=True)
        (root / "src" / "top.py").write_text("print('top')\n", encoding="utf-8")
        (nested / "deep.py").write_text("print('deep')\n", encoding="utf-8")

        snapshot_path = root / "SNAPSHOT.md"
        snapshot_path.write_text(
            "\n".join(
                [
                    "<project_structure>",
                    "└── src",
                    "    ├── nested",
                    "    └── top.py",
                    "</project_structure>",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        result = sync_snapshot_artifact(
            root,
            output_path=snapshot_path,
            tree_max_depth=2,
            exclude_dirs=set(),
            exclude_files=set(),
            exclude_extensions=set(),
            include_file_contents=False,
            write=False,
        )

        assert result.added_paths == ()
        assert result.removed_paths == ()


def test_sync_snapshot_artifact_dry_run_does_not_write() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "main.py").write_text("print('x')\n", encoding="utf-8")
        snapshot_path = root / "SNAPSHOT.md"

        result = sync_snapshot_artifact(
            root,
            output_path=snapshot_path,
            tree_max_depth=3,
            exclude_dirs=set(),
            exclude_files=set(),
            exclude_extensions=set(),
            include_file_contents=True,
            write=False,
        )

        assert result.changed is True
        assert result.wrote is False
        assert not snapshot_path.exists()


def test_sync_snapshot_artifact_no_change_is_idempotent() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "main.py").write_text("print('x')\n", encoding="utf-8")
        snapshot_path = root / "SNAPSHOT.md"

        first = sync_snapshot_artifact(
            root,
            output_path=snapshot_path,
            tree_max_depth=3,
            exclude_dirs=set(),
            exclude_files=set(),
            exclude_extensions=set(),
            include_file_contents=True,
            write=True,
        )
        second = sync_snapshot_artifact(
            root,
            output_path=snapshot_path,
            tree_max_depth=3,
            exclude_dirs=set(),
            exclude_files=set(),
            exclude_extensions=set(),
            include_file_contents=True,
            write=True,
        )

        assert first.changed is True
        assert first.wrote is True
        assert second.changed is False
        assert second.wrote is False


def test_sync_snapshot_artifact_base64_encodes_embedded_content() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        source = "line1\n```python\nprint('ok')\n```\n</file>\nline2\n"
        (root / "doc.md").write_text(source, encoding="utf-8")
        snapshot_path = root / "SNAPSHOT.md"

        sync_snapshot_artifact(
            root,
            output_path=snapshot_path,
            tree_max_depth=3,
            exclude_dirs=set(),
            exclude_files=set(),
            exclude_extensions=set(),
            include_file_contents=True,
            write=True,
        )

        rendered = snapshot_path.read_text(encoding="utf-8")
        assert "<content encoding=\"base64\" language=\"markdown\">" in rendered
        match = re.search(
            r"<file path=\"doc\.md\">\n<content encoding=\"base64\" language=\"markdown\">\n(.*?)\n</content>\n</file>",
            rendered,
            re.DOTALL,
        )
        assert match is not None
        encoded_payload = "".join(match.group(1).splitlines())
        decoded = base64.b64decode(encoded_payload.encode("ascii")).decode("utf-8")
        assert decoded == source


def test_sync_snapshot_artifact_escapes_xml_attribute_sensitive_paths() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        src = root / "src"
        src.mkdir()
        special_name = 'a"b & c.py'
        (src / special_name).write_text("print('ok')\n", encoding="utf-8")
        snapshot_path = root / "SNAPSHOT.md"

        sync_snapshot_artifact(
            root,
            output_path=snapshot_path,
            tree_max_depth=4,
            exclude_dirs=set(),
            exclude_files=set(),
            exclude_extensions=set(),
            include_file_contents=True,
            write=True,
        )

        rendered = snapshot_path.read_text(encoding="utf-8")
        assert '<file path="src/a&quot;b &amp; c.py">' in rendered
        assert '<file path="src/a"b & c.py">' not in rendered


def test_sync_snapshot_artifact_excludes_only_output_path() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        docs = root / "docs"
        docs.mkdir()
        (docs / "SNAPSHOT.md").write_text("inner snapshot\n", encoding="utf-8")
        (docs / "guide.md").write_text("guide\n", encoding="utf-8")
        output_path = root / "SNAPSHOT.md"

        sync_snapshot_artifact(
            root,
            output_path=output_path,
            tree_max_depth=4,
            exclude_dirs=set(),
            exclude_files=set(),
            exclude_extensions=set(),
            include_file_contents=True,
            write=True,
        )

        rendered = output_path.read_text(encoding="utf-8")
        assert "docs/SNAPSHOT.md" in rendered
        assert '<file path="docs/SNAPSHOT.md">' in rendered
        assert '<file path="SNAPSHOT.md">' not in rendered


def test_sync_snapshot_artifact_honors_additional_excluded_paths() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        generated = root / "phases_output"
        generated.mkdir()
        (generated / "metrics.md").write_text("generated\n", encoding="utf-8")
        (root / "main.py").write_text("print('ok')\n", encoding="utf-8")
        snapshot_path = root / "SNAPSHOT.md"

        sync_snapshot_artifact(
            root,
            output_path=snapshot_path,
            tree_max_depth=4,
            exclude_dirs=set(),
            exclude_files=set(),
            exclude_extensions=set(),
            include_file_contents=True,
            additional_exclude_relative_paths={"phases_output"},
            write=True,
        )

        rendered = snapshot_path.read_text(encoding="utf-8")
        assert "phases_output" not in rendered
        assert '<file path="phases_output/metrics.md">' not in rendered
        assert '<file path="main.py">' in rendered


def test_sync_snapshot_artifact_file_blocks_match_tree_depth_limit() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        nested = root / "src" / "nested"
        nested.mkdir(parents=True)
        (nested / "deep.py").write_text("print('deep')\n", encoding="utf-8")
        (root / "src" / "top.py").write_text("print('top')\n", encoding="utf-8")
        snapshot_path = root / "SNAPSHOT.md"

        sync_snapshot_artifact(
            root,
            output_path=snapshot_path,
            tree_max_depth=2,
            exclude_dirs=set(),
            exclude_files=set(),
            exclude_extensions=set(),
            include_file_contents=True,
            write=True,
        )

        rendered = snapshot_path.read_text(encoding="utf-8")
        assert "... (max depth reached)" in rendered
        assert '<file path="src/top.py">' in rendered
        assert '<file path="src/nested/deep.py">' not in rendered


def test_sync_snapshot_artifact_replaces_symlink_output_without_touching_target() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        external_target = root / "external_target.md"
        external_target.write_text("do not overwrite\n", encoding="utf-8")
        output_path = root / "SNAPSHOT.md"
        output_path.symlink_to(external_target)
        (root / "main.py").write_text("print('safe')\n", encoding="utf-8")

        result = sync_snapshot_artifact(
            root,
            output_path=output_path,
            tree_max_depth=3,
            exclude_dirs=set(),
            exclude_files=set(),
            exclude_extensions=set(),
            include_file_contents=True,
            write=True,
        )

        assert result.wrote is True
        assert output_path.exists()
        assert not output_path.is_symlink()
        assert external_target.read_text(encoding="utf-8") == "do not overwrite\n"
        rendered = output_path.read_text(encoding="utf-8")
        assert '<file path="SNAPSHOT.md">' not in rendered


def test_sync_snapshot_artifact_rejects_output_path_outside_directory() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "main.py").write_text("print('ok')\n", encoding="utf-8")
        outside = root.parent / "outside_snapshot.md"

        try:
            sync_snapshot_artifact(
                root,
                output_path=outside,
                tree_max_depth=3,
                exclude_dirs=set(),
                exclude_files=set(),
                exclude_extensions=set(),
                include_file_contents=True,
                write=True,
            )
        except ValueError as error:
            assert "output_path must be within directory" in str(error)
        else:
            raise AssertionError("expected ValueError")


def test_sync_snapshot_artifact_rejects_parent_traversal_output_path() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "main.py").write_text("print('ok')\n", encoding="utf-8")
        traversal_target = root / ".." / "outside_by_traversal.md"

        try:
            sync_snapshot_artifact(
                root,
                output_path=traversal_target,
                tree_max_depth=3,
                exclude_dirs=set(),
                exclude_files=set(),
                exclude_extensions=set(),
                include_file_contents=True,
                write=True,
            )
        except ValueError as error:
            assert "output_path must be within directory" in str(error)
        else:
            raise AssertionError("expected ValueError")


def test_sync_snapshot_artifact_recovers_from_non_utf8_existing_snapshot() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "main.py").write_text("print('ok')\n", encoding="utf-8")
        snapshot_path = root / "SNAPSHOT.md"
        snapshot_path.write_bytes(b"\xff\xfe\xfa")

        result = sync_snapshot_artifact(
            root,
            output_path=snapshot_path,
            tree_max_depth=3,
            exclude_dirs=set(),
            exclude_files=set(),
            exclude_extensions=set(),
            include_file_contents=False,
            write=True,
        )

        assert result.wrote is True
        assert result.changed is True
        rendered = snapshot_path.read_text(encoding="utf-8")
        assert "<project_structure>" in rendered
        assert "main.py" in rendered


def test_sync_snapshot_artifact_skips_symlinked_files_and_dirs() -> None:
    with TemporaryDirectory() as tmpdir, TemporaryDirectory() as external_tmpdir:
        root = Path(tmpdir)
        external_root = Path(external_tmpdir)
        external_secret = external_root / "external_secret.txt"
        external_secret.write_text("super-secret\n", encoding="utf-8")
        external_dir = external_root / "external_dir"
        external_dir.mkdir()
        (external_dir / "inside.txt").write_text("external-data\n", encoding="utf-8")

        (root / "src").mkdir()
        (root / "src" / "safe.py").write_text("print('safe')\n", encoding="utf-8")
        (root / "src" / "secret_link.txt").symlink_to(external_secret)
        (root / "linked_dir").symlink_to(external_dir, target_is_directory=True)

        snapshot_path = root / "SNAPSHOT.md"
        sync_snapshot_artifact(
            root,
            output_path=snapshot_path,
            tree_max_depth=4,
            exclude_dirs=set(),
            exclude_files=set(),
            exclude_extensions=set(),
            include_file_contents=True,
            write=True,
        )

        rendered = snapshot_path.read_text(encoding="utf-8")
        assert '<file path="src/safe.py">' in rendered
        assert '<file path="src/secret_link.txt">' not in rendered
        assert '<file path="linked_dir/inside.txt">' not in rendered
        assert "inside.txt" not in rendered
        assert "super-secret" not in rendered
        assert "external-data" not in rendered
