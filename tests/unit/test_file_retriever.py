from pathlib import Path

from pathspec import PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern

from agentrules.core.utils.file_system.file_retriever import (
    get_file_contents,
    get_filtered_formatted_contents,
    list_files,
    read_file_with_fallback,
    should_exclude,
)


def test_should_exclude_dir_and_pattern(tmp_path: Path):
    p_dir = tmp_path / "node_modules"
    p_dir.mkdir()
    p_file = tmp_path / "file.log"
    p_file.write_text("x")

    assert should_exclude(p_dir, {"node_modules"}, set()) is True
    assert should_exclude(p_file, set(), {"*.log"}) is True
    assert should_exclude(tmp_path / "keep.py", set(), set()) is False


def test_read_file_with_fallback_encoding(tmp_path: Path):
    # Write latin-1 text that is not valid utf-8
    p = tmp_path / "latin1.txt"
    p.write_bytes("caf\xe9".encode("latin-1", errors="ignore"))

    content, enc = read_file_with_fallback(p)
    assert "café" in content
    assert enc == "latin-1"


def test_list_files_respects_exclusions_and_depth(tmp_path: Path):
    # Create files
    (tmp_path / "a.py").write_text("print('a')")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.txt").write_text("b")
    # excluded dir and ext
    ex = sub / "__pycache__"
    ex.mkdir()
    (ex / "mod.cpython-311.pyc").write_bytes(b"bin")
    # deep path
    d1 = tmp_path / "deep" / "d1" / "d2" / "d3"
    d1.mkdir(parents=True)
    (d1 / "deep.py").write_text("x")

    files = list(list_files(tmp_path, max_depth=1))
    rels = {f.relative_to(tmp_path).as_posix() for f in files}
    assert "a.py" in rels
    assert "sub/b.txt" in rels
    assert "sub/__pycache__/mod.cpython-311.pyc" not in rels
    assert "deep/d1/d2/d3/deep.py" not in rels  # beyond max_depth


def test_list_files_applies_new_default_exclusion_patterns(tmp_path: Path):
    (tmp_path / "keep.py").write_text("print('keep')")
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "config.md").write_text("claude")
    (tmp_path / ".codex").mkdir()
    (tmp_path / ".codex" / "state.json").write_text("{}")
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "rules.mdc").write_text("x")
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "workflow.yml").write_text("name: ci")
    (tmp_path / ".custom_cache").mkdir()
    (tmp_path / ".custom_cache" / "cached.py").write_text("cached")
    (tmp_path / "pkg.egg-info").mkdir()
    (tmp_path / "pkg.egg-info" / "PKG-INFO").write_text("metadata")
    (tmp_path / "AGENTS.md").write_text("rules")
    (tmp_path / "CLAUDE.md").write_text("rules")
    (tmp_path / "diagram.svgz").write_text("svg")
    (tmp_path / "animation.gifv").write_text("gif")
    (tmp_path / "PHOTO.PNG").write_text("png")

    files = list(list_files(tmp_path, max_depth=3))
    rels = {f.relative_to(tmp_path).as_posix() for f in files}

    assert "keep.py" in rels
    assert ".claude/config.md" not in rels
    assert ".codex/state.json" not in rels
    assert ".cursor/rules.mdc" not in rels
    assert ".github/workflow.yml" not in rels
    assert ".custom_cache/cached.py" not in rels
    assert "pkg.egg-info/PKG-INFO" not in rels
    assert "AGENTS.md" not in rels
    assert "CLAUDE.md" not in rels
    assert "diagram.svgz" not in rels
    assert "animation.gifv" not in rels
    assert "PHOTO.PNG" not in rels


def test_list_files_skips_symlink_entries_when_follow_symlinks_disabled(tmp_path: Path):
    external = tmp_path / "external"
    external.mkdir()
    (external / "secret.txt").write_text("secret")

    (tmp_path / "linked").symlink_to(external, target_is_directory=True)
    (tmp_path / "keep.py").write_text("print('ok')")

    files = list(list_files(tmp_path, max_depth=3, follow_symlinks=False))
    rels = {f.relative_to(tmp_path).as_posix() for f in files}

    assert "keep.py" in rels
    assert "linked/secret.txt" not in rels


def test_list_files_exclude_relative_paths_matches_case_insensitively(tmp_path: Path):
    (tmp_path / "Snapshot.md").write_text("snapshot")
    (tmp_path / "keep.py").write_text("print('ok')")

    files = list(
        list_files(
            tmp_path,
            max_depth=3,
            exclude_relative_paths={"snapshot.md"},
        )
    )
    rels = {f.relative_to(tmp_path).as_posix() for f in files}

    assert "keep.py" in rels
    assert "Snapshot.md" not in rels


def test_get_file_contents_respects_size_and_max_files(tmp_path: Path):
    small1 = tmp_path / "s1.py"
    small2 = tmp_path / "s2.txt"
    big = tmp_path / "big.txt"
    small1.write_text("1")
    small2.write_text("2")
    # create a big file ~2KB
    big.write_text("x" * 2048)

    # Very small max_size_kb forces skipping big
    contents = get_file_contents(tmp_path, max_size_kb=1, max_files=2)
    assert len(contents) == 2  # limited by max_files
    # keys are relative paths
    assert set(contents.keys()) <= {"s1.py", "s2.txt", "big.txt"}
    # values are formatted with file_path tag
    vals = "\n".join(contents.values())
    assert '<file_path="' in vals
    assert '</file>' in vals


def test_get_filtered_formatted_contents_fuzzy_match(tmp_path: Path):
    (tmp_path / "foo.py").write_text("foo")
    d = tmp_path / "dir"
    d.mkdir()
    (d / "bar.py").write_text("bar")

    combined = get_filtered_formatted_contents(tmp_path, ["foo.py", "bar"])  # fuzzy match "bar"
    assert "foo" in combined and "bar" in combined
    assert '<file_path="' in combined


def test_get_file_contents_respects_gitignore(tmp_path: Path):
    (tmp_path / ".gitignore").write_text("*.log\nbuild/\n")

    keep = tmp_path / "keep.py"
    keep.write_text("print('keep')")
    ignored_file = tmp_path / "skip.log"
    ignored_file.write_text("ignored")
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    (build_dir / "artifact.py").write_text("artifact")

    spec = PathSpec.from_lines(
        GitWildMatchPattern,
        (tmp_path / ".gitignore").read_text().splitlines(),
    )

    contents = get_file_contents(tmp_path, gitignore_spec=spec, max_files=10)

    assert "keep.py" in contents
    assert "skip.log" not in contents
    assert "build/artifact.py" not in contents
