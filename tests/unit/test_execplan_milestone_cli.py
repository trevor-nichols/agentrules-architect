import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner


class ExecPlanMilestoneCLITests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.runner = CliRunner()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_milestone_new_and_list_commands(self) -> None:
        from agentrules import cli

        create_plan = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "new",
                "Auth Refresh",
                "--root",
                str(self.root),
                "--date",
                "20260207",
                "--no-update-registry",
            ],
        )
        self.assertEqual(create_plan.exit_code, 0, msg=create_plan.output)

        create_milestone = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "milestone",
                "new",
                "EP-20260207-001",
                "Implement callback flow",
                "--root",
                str(self.root),
            ],
        )
        self.assertEqual(create_milestone.exit_code, 0, msg=create_milestone.output)
        self.assertIn("Milestone ID", create_milestone.output)

        listed = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "milestone",
                "list",
                "EP-20260207-001",
                "--root",
                str(self.root),
            ],
        )
        self.assertEqual(listed.exit_code, 0, msg=listed.output)
        self.assertIn("EP-20260207-001/MS001", listed.output)

    def test_milestone_new_accepts_explicit_ms(self) -> None:
        from agentrules import cli

        create_plan = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "new",
                "Pinned Milestone",
                "--root",
                str(self.root),
                "--date",
                "20260207",
                "--no-update-registry",
            ],
        )
        self.assertEqual(create_plan.exit_code, 0, msg=create_plan.output)

        create_milestone = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "milestone",
                "new",
                "EP-20260207-001",
                "Pinned sequence",
                "--ms",
                "5",
                "--root",
                str(self.root),
            ],
        )
        self.assertEqual(create_milestone.exit_code, 0, msg=create_milestone.output)
        self.assertIn("EP-20260207-001/MS005", create_milestone.output)

    def test_milestone_new_rejects_duplicate_explicit_ms(self) -> None:
        from agentrules import cli

        create_plan = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "new",
                "Duplicate Milestone",
                "--root",
                str(self.root),
                "--date",
                "20260207",
                "--no-update-registry",
            ],
        )
        self.assertEqual(create_plan.exit_code, 0, msg=create_plan.output)

        first = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "milestone",
                "new",
                "EP-20260207-001",
                "First",
                "--ms",
                "2",
                "--root",
                str(self.root),
            ],
        )
        self.assertEqual(first.exit_code, 0, msg=first.output)

        second = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "milestone",
                "new",
                "EP-20260207-001",
                "Second",
                "--ms",
                "2",
                "--root",
                str(self.root),
            ],
        )
        self.assertEqual(second.exit_code, 2, msg=second.output)
        self.assertIn("already exists", second.output.lower())

    def test_milestone_archive_moves_file(self) -> None:
        from agentrules import cli

        create_plan = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "new",
                "Billing Foundation",
                "--root",
                str(self.root),
                "--date",
                "20260207",
                "--no-update-registry",
            ],
        )
        self.assertEqual(create_plan.exit_code, 0, msg=create_plan.output)

        create_milestone = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "milestone",
                "new",
                "EP-20260207-001",
                "Introduce idempotency keys",
                "--root",
                str(self.root),
            ],
        )
        self.assertEqual(create_milestone.exit_code, 0, msg=create_milestone.output)

        active_glob = list(
            (self.root / ".agent" / "exec_plans" / "active" / "billing-foundation" / "milestones" / "active").glob(
                "MS001*.md"
            )
        )
        self.assertEqual(len(active_glob), 1)
        self.assertTrue(active_glob[0].exists())

        archive_result = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "milestone",
                "archive",
                "EP-20260207-001",
                "--ms",
                "1",
                "--root",
                str(self.root),
            ],
        )
        self.assertEqual(archive_result.exit_code, 0, msg=archive_result.output)

        self.assertFalse(active_glob[0].exists())
        archived_glob = list(
            (
                self.root
                / ".agent"
                / "exec_plans"
                / "active"
                / "billing-foundation"
                / "milestones"
                / "archive"
            ).rglob(
                "MS001*.md"
            )
        )
        self.assertEqual(len(archived_glob), 1)
        self.assertTrue(archived_glob[0].exists())

        list_active_only = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "milestone",
                "list",
                "EP-20260207-001",
                "--root",
                str(self.root),
                "--active-only",
            ],
        )
        self.assertEqual(list_active_only.exit_code, 0, msg=list_active_only.output)
        self.assertIn("No milestones found", list_active_only.output)

    def test_milestone_remaining_lists_active_only_in_compact_mode(self) -> None:
        from agentrules import cli

        create_plan = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "new",
                "Milestone Remaining",
                "--root",
                str(self.root),
                "--date",
                "20260207",
                "--no-update-registry",
            ],
        )
        self.assertEqual(create_plan.exit_code, 0, msg=create_plan.output)

        create_first = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "milestone",
                "new",
                "EP-20260207-001",
                "First",
                "--root",
                str(self.root),
            ],
        )
        self.assertEqual(create_first.exit_code, 0, msg=create_first.output)

        create_second = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "milestone",
                "new",
                "EP-20260207-001",
                "Second",
                "--root",
                str(self.root),
            ],
        )
        self.assertEqual(create_second.exit_code, 0, msg=create_second.output)

        archive_first = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "milestone",
                "archive",
                "EP-20260207-001",
                "--ms",
                "1",
                "--root",
                str(self.root),
            ],
        )
        self.assertEqual(archive_first.exit_code, 0, msg=archive_first.output)

        remaining = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "milestone",
                "remaining",
                "EP-20260207-001",
                "--root",
                str(self.root),
            ],
        )
        self.assertEqual(remaining.exit_code, 0, msg=remaining.output)
        self.assertIn("Remaining milestones for EP-20260207-001: 1", remaining.output)
        self.assertIn("EP-20260207-001/MS002", remaining.output)
        self.assertNotIn("EP-20260207-001/MS001", remaining.output)

        remaining_with_path = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "milestone",
                "remaining",
                "EP-20260207-001",
                "--root",
                str(self.root),
                "--path",
            ],
        )
        self.assertEqual(remaining_with_path.exit_code, 0, msg=remaining_with_path.output)
        self.assertIn("->", remaining_with_path.output)


if __name__ == "__main__":
    unittest.main()
