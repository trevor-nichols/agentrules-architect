import tempfile
import unittest
from pathlib import Path

from agentrules.core.utils.file_system.tree_generator import get_project_tree, save_tree_to_file

_ICON_MARKERS = (
    "📁",
    "🐍",
    "📜",
    "⚛️",
    "💠",
    "🌐",
    "🎨",
    "📋",
    "📝",
    "📄",
    "💻",
    "🔒",
    "📦",
    "📖",
    "🐳",
    "⚠️",
)


class TreeGeneratorTests(unittest.TestCase):
    def test_get_project_tree_uses_plain_tree_lines_without_icon_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")
            (root / "app.py").write_text("print('root')\n", encoding="utf-8")

            tree = get_project_tree(root, max_depth=4)

        self.assertEqual(tree[0], "<project_structure>")
        self.assertEqual(tree[-1], "</project_structure>")
        self.assertNotIn("File Type Key:", tree)
        for line in tree:
            self.assertTrue(all(marker not in line for marker in _ICON_MARKERS))

        self.assertEqual(
            tree[1:-1],
            [
                "├── src",
                "│   └── main.py",
                "└── app.py",
            ],
        )

    def test_save_tree_to_file_does_not_emit_icon_key_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_name = "tree.md"
            path = save_tree_to_file(
                [
                    "<project_structure>",
                    "└── app.py",
                    "</project_structure>",
                ],
                root,
                rules_filename=output_name,
            )
            content = (root / output_name).read_text(encoding="utf-8")

        self.assertEqual(path, str(root / output_name))
        self.assertNotIn("File Type Key:", content)
        self.assertNotIn("⚠️", content)
        self.assertIn("# Project Directory Structure", content)
        self.assertIn("└── app.py", content)

    def test_get_project_tree_omits_newly_excluded_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "keep.py").write_text("print('ok')\n", encoding="utf-8")
            (root / ".claude").mkdir()
            (root / ".claude" / "notes.md").write_text("x", encoding="utf-8")
            (root / ".custom_cache").mkdir()
            (root / ".custom_cache" / "cache.txt").write_text("x", encoding="utf-8")
            (root / "pkg.egg-info").mkdir()
            (root / "pkg.egg-info" / "PKG-INFO").write_text("x", encoding="utf-8")
            (root / "phases_output").mkdir()
            (root / "phases_output" / "phase1_discovery.md").write_text("x", encoding="utf-8")
            (root / "AGENTS.md").write_text("x", encoding="utf-8")
            (root / "SNAPSHOT.md").write_text("x", encoding="utf-8")
            (root / "diagram.svgz").write_text("x", encoding="utf-8")

            tree = get_project_tree(root, max_depth=4)
            rendered = "\n".join(tree)

        self.assertIn("keep.py", rendered)
        self.assertNotIn(".claude", rendered)
        self.assertNotIn(".custom_cache", rendered)
        self.assertNotIn("pkg.egg-info", rendered)
        self.assertNotIn("phases_output", rendered)
        self.assertNotIn("AGENTS.md", rendered)
        self.assertNotIn("SNAPSHOT.md", rendered)
        self.assertNotIn("diagram.svgz", rendered)

    def test_get_project_tree_skips_symlink_entries_when_follow_symlinks_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as external_tmpdir:
            root = Path(tmpdir)
            external = Path(external_tmpdir)
            (external / "secret.txt").write_text("secret", encoding="utf-8")
            (root / "linked").symlink_to(external, target_is_directory=True)
            (root / "app.py").write_text("print('ok')\n", encoding="utf-8")

            tree = get_project_tree(root, max_depth=4, follow_symlinks=False)
            rendered = "\n".join(tree)

        self.assertIn("app.py", rendered)
        self.assertNotIn("linked", rendered)
        self.assertNotIn("secret.txt", rendered)

    def test_get_project_tree_exclude_relative_paths_matches_case_insensitively(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "Snapshot.md").write_text("content", encoding="utf-8")
            (root / "keep.py").write_text("print('ok')\n", encoding="utf-8")

            tree = get_project_tree(
                root,
                max_depth=4,
                exclude_relative_paths={"snapshot.md"},
            )
            rendered = "\n".join(tree)

        self.assertIn("keep.py", rendered)
        self.assertNotIn("Snapshot.md", rendered)


if __name__ == "__main__":
    unittest.main()
