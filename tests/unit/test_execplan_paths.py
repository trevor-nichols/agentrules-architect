import tempfile
import unittest
from pathlib import Path

from agentrules.core.execplan.paths import (
    get_execplan_plan_root,
    is_execplan_archive_path,
    is_execplan_milestone_path,
)


class ExecPlanPathsTests(unittest.TestCase):
    def test_legacy_active_slug_root_is_not_archived(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            execplans_dir = Path(tmpdir) / ".agent" / "exec_plans"
            plan_path = execplans_dir / "active" / "EP-20260207-001_active.md"
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text("# placeholder\n", encoding="utf-8")

            self.assertFalse(is_execplan_archive_path(plan_path, execplans_root=execplans_dir))
            self.assertEqual(
                get_execplan_plan_root(plan_path, execplans_root=execplans_dir),
                (execplans_dir / "active").resolve(),
            )

    def test_active_root_archive_slug_is_not_archived(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            execplans_dir = Path(tmpdir) / ".agent" / "exec_plans"
            plan_path = execplans_dir / "active" / "archive" / "EP-20260207-001_archive.md"
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text("# placeholder\n", encoding="utf-8")

            self.assertFalse(is_execplan_archive_path(plan_path, execplans_root=execplans_dir))
            self.assertEqual(
                get_execplan_plan_root(plan_path, execplans_root=execplans_dir),
                (execplans_dir / "active" / "archive").resolve(),
            )

    def test_active_root_complete_slug_is_not_archived(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            execplans_dir = Path(tmpdir) / ".agent" / "exec_plans"
            plan_path = execplans_dir / "active" / "complete" / "EP-20260207-001_complete.md"
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text("# placeholder\n", encoding="utf-8")

            self.assertFalse(is_execplan_archive_path(plan_path, execplans_root=execplans_dir))
            self.assertEqual(
                get_execplan_plan_root(plan_path, execplans_root=execplans_dir),
                (execplans_dir / "active" / "complete").resolve(),
            )

    def test_active_root_completed_slug_is_not_archived(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            execplans_dir = Path(tmpdir) / ".agent" / "exec_plans"
            plan_path = execplans_dir / "active" / "completed" / "EP-20260207-001_completed.md"
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text("# placeholder\n", encoding="utf-8")

            self.assertFalse(is_execplan_archive_path(plan_path, execplans_root=execplans_dir))
            self.assertEqual(
                get_execplan_plan_root(plan_path, execplans_root=execplans_dir),
                (execplans_dir / "active" / "completed").resolve(),
            )

    def test_legacy_top_level_archive_slug_is_not_archived(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            execplans_dir = Path(tmpdir) / ".agent" / "exec_plans"
            plan_path = execplans_dir / "archive" / "EP-20260207-001_archive.md"
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text("# placeholder\n", encoding="utf-8")

            self.assertFalse(is_execplan_archive_path(plan_path, execplans_root=execplans_dir))
            self.assertEqual(
                get_execplan_plan_root(plan_path, execplans_root=execplans_dir),
                (execplans_dir / "archive").resolve(),
            )

    def test_legacy_top_level_complete_slug_is_not_archived(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            execplans_dir = Path(tmpdir) / ".agent" / "exec_plans"
            plan_path = execplans_dir / "complete" / "EP-20260207-001_complete.md"
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text("# placeholder\n", encoding="utf-8")

            self.assertFalse(is_execplan_archive_path(plan_path, execplans_root=execplans_dir))
            self.assertEqual(
                get_execplan_plan_root(plan_path, execplans_root=execplans_dir),
                (execplans_dir / "complete").resolve(),
            )

    def test_legacy_top_level_completed_slug_is_not_archived(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            execplans_dir = Path(tmpdir) / ".agent" / "exec_plans"
            plan_path = execplans_dir / "completed" / "EP-20260207-001_completed.md"
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text("# placeholder\n", encoding="utf-8")

            self.assertFalse(is_execplan_archive_path(plan_path, execplans_root=execplans_dir))
            self.assertEqual(
                get_execplan_plan_root(plan_path, execplans_root=execplans_dir),
                (execplans_dir / "completed").resolve(),
            )

    def test_complete_root_dated_path_is_archived(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            execplans_dir = Path(tmpdir) / ".agent" / "exec_plans"
            plan_path = (
                execplans_dir
                / "complete"
                / "2026"
                / "02"
                / "12"
                / "EP-20260207-001_frontend-architecture-refactor"
                / "EP-20260207-001_frontend-architecture-refactor.md"
            )
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text("# placeholder\n", encoding="utf-8")

            self.assertTrue(is_execplan_archive_path(plan_path, execplans_root=execplans_dir))
            self.assertEqual(
                get_execplan_plan_root(plan_path, execplans_root=execplans_dir),
                (
                    execplans_dir
                    / "complete"
                    / "2026"
                    / "02"
                    / "12"
                    / "EP-20260207-001_frontend-architecture-refactor"
                ).resolve(),
            )

    def test_top_level_completed_slug_dated_path_is_not_archived(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            execplans_dir = Path(tmpdir) / ".agent" / "exec_plans"
            plan_path = (
                execplans_dir
                / "completed"
                / "2026"
                / "02"
                / "12"
                / "EP-20260207-001_frontend-architecture-refactor"
                / "EP-20260207-001_frontend-architecture-refactor.md"
            )
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text("# placeholder\n", encoding="utf-8")

            self.assertFalse(is_execplan_archive_path(plan_path, execplans_root=execplans_dir))
            self.assertEqual(
                get_execplan_plan_root(plan_path, execplans_root=execplans_dir),
                (execplans_dir / "completed").resolve(),
            )

    def test_legacy_archive_root_dated_path_is_archived(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            execplans_dir = Path(tmpdir) / ".agent" / "exec_plans"
            plan_path = (
                execplans_dir
                / "archive"
                / "2026"
                / "02"
                / "12"
                / "EP-20260207-001_frontend-architecture-refactor"
                / "EP-20260207-001_frontend-architecture-refactor.md"
            )
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text("# placeholder\n", encoding="utf-8")

            self.assertTrue(is_execplan_archive_path(plan_path, execplans_root=execplans_dir))
            self.assertEqual(
                get_execplan_plan_root(plan_path, execplans_root=execplans_dir),
                (
                    execplans_dir
                    / "archive"
                    / "2026"
                    / "02"
                    / "12"
                    / "EP-20260207-001_frontend-architecture-refactor"
                ).resolve(),
            )

    def test_legacy_archive_slug_named_milestones_is_not_milestone_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            execplans_dir = Path(tmpdir) / ".agent" / "exec_plans"
            plan_path = execplans_dir / "milestones" / "archive" / "EP-20260207-001_milestones.md"
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text("# placeholder\n", encoding="utf-8")

            self.assertFalse(is_execplan_milestone_path(plan_path, execplans_root=execplans_dir))
            self.assertTrue(is_execplan_archive_path(plan_path, execplans_root=execplans_dir))


if __name__ == "__main__":
    unittest.main()
