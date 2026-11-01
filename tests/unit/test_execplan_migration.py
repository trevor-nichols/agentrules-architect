import json
import os
import tempfile
import unittest
from pathlib import Path

from agentrules.core.execplan import CURRENT_LAYOUT, detect_execplan_layout
from agentrules.core.execplan.creator import complete_execplan, create_execplan
from agentrules.core.execplan.migration import migrate_execplan_workspace
from agentrules.core.execplan.milestones import create_execplan_milestone
from agentrules.core.utils.formatters.clean_agentrules import ensure_execplans_guidance

LEGACY_PLANS_GUIDE = (
    "Create plans under `.agent/exec_plans/active/<short-slug>/`.\n"
    "Base milestones on `.agent/templates/MILESTONE_TEMPLATE.md`.\n"
)
LEGACY_MILESTONE_GUIDE = "Create milestones in `.agent/exec_plans/active/<short-slug>/milestones/active/`.\n"


def _seed_legacy_repository(root: Path) -> Path:
    """Create a legacy `.agent/` repository and return the active plan path."""
    (root / ".agent" / "exec_plans").mkdir(parents=True)
    active = create_execplan(root=root, title="Active Work", date_yyyymmdd="20261001")
    create_execplan_milestone(root=root, execplan_id=active.plan_id, title="First Step")
    finished = create_execplan(root=root, title="Finished Work", date_yyyymmdd="20261002")
    complete_execplan(root=root, execplan_id=finished.plan_id, completion_date_yyyymmdd="20261003")

    (root / ".agent" / "PLANS.md").write_text(LEGACY_PLANS_GUIDE, encoding="utf-8")
    (root / ".agent" / "templates").mkdir()
    (root / ".agent" / "templates" / "MILESTONE_TEMPLATE.md").write_text(LEGACY_MILESTONE_GUIDE, encoding="utf-8")
    (root / ".agent" / "notes.md").write_text("unrelated tool notes\n", encoding="utf-8")
    (root / "AGENTS.md").write_text(
        "You are a coding agent.\n\n# Development Principles\n- Keep it simple.\n",
        encoding="utf-8",
    )
    success, message = ensure_execplans_guidance(str(root), filename="AGENTS.md")
    assert success, message
    return active.plan_path


def _tree_snapshot(root: Path) -> dict[str, bytes | None]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes() if path.is_file() else None
        for path in sorted(root.rglob("*"))
    }


class ExecPlanMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def assert_fully_migrated(self) -> None:
        root = self.root
        self.assertEqual(detect_execplan_layout(root), CURRENT_LAYOUT)
        self.assertFalse((root / ".agent" / "exec_plans").exists())
        self.assertFalse((root / ".agent" / "templates").exists())
        self.assertEqual("unrelated tool notes\n", (root / ".agent" / "notes.md").read_text(encoding="utf-8"))

        self.assertEqual(
            "Create plans under `.exec_plans/active/<short-slug>/`.\n"
            "Base milestones on `.exec_plans/templates/MILESTONE_TEMPLATE.md`.\n",
            (root / ".exec_plans" / "PLANS.md").read_text(encoding="utf-8"),
        )
        self.assertEqual(
            "Create milestones in `.exec_plans/active/<short-slug>/milestones/active/`.\n",
            (root / ".exec_plans" / "templates" / "MILESTONE_TEMPLATE.md").read_text(encoding="utf-8"),
        )

        rules = (root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("(as described in `.exec_plans/PLANS.md`)", rules)
        self.assertIn("(as described in `.exec_plans/templates/MILESTONE_TEMPLATE.md`)", rules)
        self.assertNotIn(".agent/", rules)

        registry_text = (root / ".exec_plans" / "registry.json").read_text(encoding="utf-8")
        self.assertNotIn(".agent/", registry_text)
        plan_paths = [plan["path"] for plan in json.loads(registry_text)["plans"]]
        self.assertEqual(2, len(plan_paths))
        for plan_path in plan_paths:
            self.assertTrue(plan_path.startswith(".exec_plans/"), plan_path)
            self.assertTrue((root / plan_path).is_file(), plan_path)
        self.assertTrue(
            (
                root / ".exec_plans" / "active" / "active-work" / "milestones" / "active" / "MS001_first-step.md"
            ).is_file()
        )

    def test_migrates_legacy_repository_without_touching_plan_bodies(self) -> None:
        legacy_plan_path = _seed_legacy_repository(self.root)
        plan_body = legacy_plan_path.read_bytes()

        result = migrate_execplan_workspace(self.root, rules_filename="AGENTS.md")

        self.assertFalse(result.dry_run)
        self.assertIsNotNone(result.registry_result)
        self.assert_fully_migrated()
        migrated_plan_path = self.root / ".exec_plans" / legacy_plan_path.relative_to(
            self.root / ".agent" / "exec_plans"
        )
        self.assertEqual(plan_body, migrated_plan_path.read_bytes())

    def test_second_run_reports_nothing_to_migrate(self) -> None:
        _seed_legacy_repository(self.root)
        migrate_execplan_workspace(self.root, rules_filename="AGENTS.md")
        migrated = _tree_snapshot(self.root)

        result = migrate_execplan_workspace(self.root, rules_filename="AGENTS.md")

        self.assertTrue(result.is_noop)
        self.assertEqual(migrated, _tree_snapshot(self.root))

    def test_dry_run_lists_moves_without_writing(self) -> None:
        _seed_legacy_repository(self.root)
        before = _tree_snapshot(self.root)

        result = migrate_execplan_workspace(self.root, rules_filename="AGENTS.md", dry_run=True)

        self.assertTrue(result.dry_run)
        self.assertEqual(
            [
                (".agent/exec_plans/active", ".exec_plans/active"),
                (".agent/exec_plans/complete", ".exec_plans/complete"),
                (".agent/exec_plans/registry.json", ".exec_plans/registry.json"),
                (".agent/PLANS.md", ".exec_plans/PLANS.md"),
                (".agent/templates/MILESTONE_TEMPLATE.md", ".exec_plans/templates/MILESTONE_TEMPLATE.md"),
            ],
            [
                (move.source.relative_to(self.root).as_posix(), move.destination.relative_to(self.root).as_posix())
                for move in result.moves
            ],
        )
        self.assertEqual(before, _tree_snapshot(self.root))

    def test_finishes_a_partially_migrated_repository(self) -> None:
        _seed_legacy_repository(self.root)
        (self.root / ".exec_plans").mkdir()
        os.replace(self.root / ".agent" / "exec_plans" / "active", self.root / ".exec_plans" / "active")
        os.replace(self.root / ".agent" / "PLANS.md", self.root / ".exec_plans" / "PLANS.md")

        migrate_execplan_workspace(self.root, rules_filename="AGENTS.md")

        self.assert_fully_migrated()

    def test_rebuilds_a_stale_registry_after_all_entries_moved(self) -> None:
        _seed_legacy_repository(self.root)
        os.replace(self.root / ".agent" / "exec_plans", self.root / ".exec_plans")
        os.replace(self.root / ".agent" / "PLANS.md", self.root / ".exec_plans" / "PLANS.md")
        (self.root / ".exec_plans" / "templates").mkdir()
        os.replace(
            self.root / ".agent" / "templates" / "MILESTONE_TEMPLATE.md",
            self.root / ".exec_plans" / "templates" / "MILESTONE_TEMPLATE.md",
        )

        result = migrate_execplan_workspace(self.root, rules_filename="AGENTS.md")

        self.assertEqual((), result.moves)
        self.assert_fully_migrated()

    def test_refuses_without_changing_files(self) -> None:
        def existing_destination(root: Path) -> None:
            (root / ".exec_plans").mkdir()
            (root / ".exec_plans" / "PLANS.md").write_text("current guide\n", encoding="utf-8")

        def overlapping_destinations(root: Path) -> None:
            (root / ".agent" / "exec_plans" / "templates").mkdir()

        def symlinked_workspace(root: Path) -> None:
            outside = root / "outside"
            outside.mkdir()
            (root / ".exec_plans").symlink_to(outside, target_is_directory=True)

        cases = (
            ("existing destination", existing_destination, ".exec_plans/PLANS.md already exists"),
            ("overlapping destinations", overlapping_destinations, "overlap"),
            ("symlinked workspace", symlinked_workspace, ".exec_plans is a symlink"),
        )
        for label, arrange, expected_reason in cases:
            with self.subTest(label), tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir).resolve()
                _seed_legacy_repository(root)
                arrange(root)
                before = _tree_snapshot(root)

                with self.assertRaisesRegex(ValueError, expected_reason):
                    migrate_execplan_workspace(root, rules_filename="AGENTS.md")

                self.assertEqual(before, _tree_snapshot(root))

    def test_repository_without_legacy_workspace_has_nothing_to_migrate(self) -> None:
        create_execplan(root=self.root, title="Current Work", date_yyyymmdd="20261001")
        before = _tree_snapshot(self.root)

        result = migrate_execplan_workspace(self.root, rules_filename="AGENTS.md")

        self.assertTrue(result.is_noop)
        self.assertEqual(before, _tree_snapshot(self.root))


if __name__ == "__main__":
    unittest.main()
