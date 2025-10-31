import os
from pathlib import Path

import pytest

from core.utils.file_system.file_retriever import (
    should_exclude,
    read_file_with_fallback,
    list_files,
    get_file_contents,
    get_filtered_formatted_contents,
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

