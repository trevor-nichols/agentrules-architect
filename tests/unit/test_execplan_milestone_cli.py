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
            (self.root / ".agent" / "exec_plans" / "billing-foundation" / "milestones" / "active").glob(
                "EP-20260207-001_MS001*.md"
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
            (self.root / ".agent" / "exec_plans" / "billing-foundation" / "milestones" / "archive").rglob(
                "EP-20260207-001_MS001*.md"
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


if __name__ == "__main__":
    unittest.main()
