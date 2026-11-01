import tempfile
import unittest
from pathlib import Path

from agentrules.core.execplan.layout import (
    CURRENT_LAYOUT,
    LEGACY_LAYOUT,
    AmbiguousExecPlanLayoutError,
    detect_execplan_layout,
    resolve_execplan_paths,
)


def _create(root: Path, relative: str) -> None:
    target = root / relative
    if relative.endswith(".md"):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# placeholder\n", encoding="utf-8")
    else:
        target.mkdir(parents=True, exist_ok=True)


class ExecPlanLayoutDetectionTests(unittest.TestCase):
    def test_detects_layout_from_workspace_entries(self) -> None:
        cases = (
            ("empty repository", (), CURRENT_LAYOUT),
            ("current workspace", (".exec_plans",), CURRENT_LAYOUT),
            ("legacy plans directory", (".agent/exec_plans",), LEGACY_LAYOUT),
            ("legacy guide only", (".agent/PLANS.md",), LEGACY_LAYOUT),
            ("legacy milestone guide only", (".agent/templates/MILESTONE_TEMPLATE.md",), LEGACY_LAYOUT),
            ("unrelated .agent content", (".agent/notes.md", ".agent/templates/OTHER.md"), CURRENT_LAYOUT),
            ("current workspace beside unrelated .agent content", (".exec_plans", ".agent/notes.md"), CURRENT_LAYOUT),
        )
        for label, entries, expected in cases:
            with self.subTest(label), tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                for entry in entries:
                    _create(root, entry)

                self.assertEqual(detect_execplan_layout(root), expected)

    def test_rejects_repository_with_both_workspaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _create(root, ".exec_plans")
            _create(root, ".agent/exec_plans")

            with self.assertRaisesRegex(AmbiguousExecPlanLayoutError, "agentrules execplan migrate"):
                detect_execplan_layout(root)


class ResolveExecPlanPathsTests(unittest.TestCase):
    def test_detected_legacy_workspace_resolves_legacy_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            _create(root, ".agent/exec_plans")

            paths = resolve_execplan_paths(root)

            self.assertTrue(paths.layout.is_legacy)
            self.assertEqual(paths.execplans_dir, root / ".agent" / "exec_plans")
            self.assertEqual(paths.registry_path, root / ".agent" / "exec_plans" / "registry.json")

    def test_explicit_directory_skips_detection_and_owns_its_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            _create(root, ".exec_plans")
            _create(root, ".agent/exec_plans")

            custom = resolve_execplan_paths(root, execplans_dir=Path("plans"))
            legacy = resolve_execplan_paths(root, execplans_dir=root / ".agent" / "exec_plans")
            explicit_out = resolve_execplan_paths(
                root,
                execplans_dir=Path("plans"),
                registry_path=Path("out/registry.json"),
            )

            self.assertEqual(custom.execplans_dir, root / "plans")
            self.assertEqual(custom.registry_path, root / "plans" / "registry.json")
            self.assertFalse(custom.layout.is_legacy)
            self.assertTrue(legacy.layout.is_legacy)
            self.assertEqual(explicit_out.registry_path, root / "out" / "registry.json")


if __name__ == "__main__":
    unittest.main()
