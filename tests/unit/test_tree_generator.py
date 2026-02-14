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


if __name__ == "__main__":
    unittest.main()
