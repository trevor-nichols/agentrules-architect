import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner


class ExecPlanCLITests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.runner = CliRunner()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_new_creates_execplan_and_registry_by_default(self) -> None:
        from agentrules import cli

        result = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "new",
                "Auth Refresh",
                "--root",
                str(self.root),
                "--date",
                "20260207",
            ],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)

        plan_path = (
            self.root
            / ".agent"
            / "exec_plans"
            / "active"
            / "auth-refresh"
            / "EP-20260207-001_auth-refresh.md"
        )
        self.assertTrue(plan_path.exists())

        registry_path = self.root / ".agent" / "exec_plans" / "registry.json"
        self.assertTrue(registry_path.exists())
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["plans"][0]["id"], "EP-20260207-001")

    def test_new_supports_no_update_registry(self) -> None:
        from agentrules import cli

        result = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "new",
                "Offline Plan",
                "--root",
                str(self.root),
                "--date",
                "20260207",
                "--no-update-registry",
            ],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        registry_path = self.root / ".agent" / "exec_plans" / "registry.json"
        self.assertFalse(registry_path.exists())

    def test_new_returns_non_zero_when_registry_update_fails(self) -> None:
        from agentrules import cli

        bad_path = self.root / ".agent" / "exec_plans" / "bad" / "EP-20260207-001_bad.md"
        bad_path.parent.mkdir(parents=True, exist_ok=True)
        bad_path.write_text("---\nid: EP-20260207-001\n---\n", encoding="utf-8")

        result = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "new",
                "Good Plan",
                "--root",
                str(self.root),
                "--date",
                "20260207",
            ],
        )

        self.assertEqual(result.exit_code, 1, msg=result.output)
        created = (
            self.root
            / ".agent"
            / "exec_plans"
            / "active"
            / "good-plan"
            / "EP-20260207-002_good-plan.md"
        )
        self.assertTrue(created.exists())

    def test_new_handles_filesystem_oserror(self) -> None:
        from agentrules import cli

        with patch(
            "agentrules.cli.commands.execplan.create_execplan",
            side_effect=PermissionError("permission denied"),
        ):
            result = self.runner.invoke(
                cli.app,
                [
                    "execplan",
                    "new",
                    "Permission Test",
                    "--root",
                    str(self.root),
                    "--date",
                    "20260207",
                ],
            )

        self.assertEqual(result.exit_code, 2, msg=result.output)
        self.assertIn("filesystem error", result.output.lower())

    def test_complete_moves_execplan_directory_and_updates_registry(self) -> None:
        from agentrules import cli

        create_result = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "new",
                "Frontend Architecture Refactor",
                "--root",
                str(self.root),
                "--date",
                "20260207",
            ],
        )
        self.assertEqual(create_result.exit_code, 0, msg=create_result.output)

        source_root = self.root / ".agent" / "exec_plans" / "active" / "frontend-architecture-refactor"
        source_plan = source_root / "EP-20260207-001_frontend-architecture-refactor.md"
        self.assertTrue(source_plan.exists())

        archive_result = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "complete",
                "EP-20260207-001",
                "--root",
                str(self.root),
                "--date",
                "20260212",
            ],
        )
        self.assertEqual(archive_result.exit_code, 0, msg=archive_result.output)
        self.assertIn("Active ExecPlans: none", archive_result.output)
        self.assertFalse(source_root.exists())

        archived_root = (
            self.root
            / ".agent"
            / "exec_plans"
            / "complete"
            / "2026"
            / "02"
            / "12"
            / "EP-20260207-001_frontend-architecture-refactor"
        )
        archived_plan = archived_root / "EP-20260207-001_frontend-architecture-refactor.md"
        self.assertTrue(archived_plan.exists())
        content = archived_plan.read_text(encoding="utf-8")
        self.assertIn("status: archived", content)
        self.assertIn("updated: '2026-02-12'", content)

        registry_path = self.root / ".agent" / "exec_plans" / "registry.json"
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["plans"][0]["id"], "EP-20260207-001")
        self.assertIn("complete/2026/02/12/", payload["plans"][0]["path"])

    def test_archive_rejects_already_archived_execplan(self) -> None:
        from agentrules import cli

        create_result = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "new",
                "Archive Once",
                "--root",
                str(self.root),
                "--date",
                "20260207",
                "--no-update-registry",
            ],
        )
        self.assertEqual(create_result.exit_code, 0, msg=create_result.output)

        first_archive = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "archive",
                "EP-20260207-001",
                "--root",
                str(self.root),
                "--date",
                "20260212",
                "--no-update-registry",
            ],
        )
        self.assertEqual(first_archive.exit_code, 0, msg=first_archive.output)

        second_archive = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "archive",
                "EP-20260207-001",
                "--root",
                str(self.root),
                "--date",
                "20260212",
                "--no-update-registry",
            ],
        )
        self.assertNotEqual(second_archive.exit_code, 0)
        self.assertIn("already completed", second_archive.output.lower())

    def test_archive_prints_remaining_active_execplan_count(self) -> None:
        from agentrules import cli

        first_create = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "new",
                "First Plan",
                "--root",
                str(self.root),
                "--date",
                "20260207",
                "--no-update-registry",
            ],
        )
        self.assertEqual(first_create.exit_code, 0, msg=first_create.output)

        second_create = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "new",
                "Second Plan",
                "--root",
                str(self.root),
                "--date",
                "20260208",
                "--no-update-registry",
            ],
        )
        self.assertEqual(second_create.exit_code, 0, msg=second_create.output)

        archive_result = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "complete",
                "EP-20260207-001",
                "--root",
                str(self.root),
                "--date",
                "20260212",
                "--no-update-registry",
            ],
        )

        self.assertEqual(archive_result.exit_code, 0, msg=archive_result.output)
        self.assertIn("Active ExecPlans: 1", archive_result.output)

    def test_list_execplans_prints_compact_progress(self) -> None:
        from agentrules import cli

        first_create = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "new",
                "Checkout Improvements",
                "--root",
                str(self.root),
                "--date",
                "20260207",
                "--no-update-registry",
            ],
        )
        self.assertEqual(first_create.exit_code, 0, msg=first_create.output)

        second_create = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "new",
                "Search Improvements",
                "--root",
                str(self.root),
                "--date",
                "20260208",
                "--no-update-registry",
            ],
        )
        self.assertEqual(second_create.exit_code, 0, msg=second_create.output)

        create_milestone = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "milestone",
                "new",
                "EP-20260207-001",
                "Wire checkout endpoint",
                "--root",
                str(self.root),
            ],
        )
        self.assertEqual(create_milestone.exit_code, 0, msg=create_milestone.output)

        archive_milestone = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "milestone",
                "complete",
                "EP-20260207-001",
                "--ms",
                "1",
                "--root",
                str(self.root),
            ],
        )
        self.assertEqual(archive_milestone.exit_code, 0, msg=archive_milestone.output)

        listed = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "list",
                "--root",
                str(self.root),
            ],
        )
        self.assertEqual(listed.exit_code, 0, msg=listed.output)
        self.assertIn("Active ExecPlans: 2 (milestones 1/1 completed)", listed.output)
        self.assertIn("EP-20260207-001 [planned] Checkout Improvements (milestones 1/1 completed)", listed.output)
        self.assertIn("EP-20260208-001 [planned] Search Improvements (milestones none)", listed.output)
        self.assertNotIn("-> .agent/exec_plans", listed.output)

    def test_list_execplans_with_path_includes_plan_path(self) -> None:
        from agentrules import cli

        created = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "new",
                "Path Visibility",
                "--root",
                str(self.root),
                "--date",
                "20260207",
                "--no-update-registry",
            ],
        )
        self.assertEqual(created.exit_code, 0, msg=created.output)

        listed = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "list",
                "--root",
                str(self.root),
                "--path",
            ],
        )
        self.assertEqual(listed.exit_code, 0, msg=listed.output)
        self.assertIn("-> .agent/exec_plans/active/path-visibility/EP-20260207-001_path-visibility.md", listed.output)

    def test_archive_rejects_when_active_milestones_exist(self) -> None:
        from agentrules import cli

        create_result = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "new",
                "Archive Guard Rail",
                "--root",
                str(self.root),
                "--date",
                "20260207",
                "--no-update-registry",
            ],
        )
        self.assertEqual(create_result.exit_code, 0, msg=create_result.output)

        active_milestone = (
            self.root
            / ".agent"
            / "exec_plans"
            / "active"
            / "archive-guard-rail"
            / "milestones"
            / "active"
            / "MS001_blocking.md"
        )
        active_milestone.parent.mkdir(parents=True, exist_ok=True)
        active_milestone.write_text(
            (
                "---\n"
                "id: EP-20260207-001/MS001\n"
                "execplan_id: EP-20260207-001\n"
                'title: "Blocking"\n'
                "status: active\n"
                "domain: backend\n"
                'owner: "@codex"\n'
                "created: 2026-02-07\n"
                "updated: 2026-02-07\n"
                "---\n\n"
                "# Blocking\n"
            ),
            encoding="utf-8",
        )

        archive_result = self.runner.invoke(
            cli.app,
            [
                "execplan",
                "complete",
                "EP-20260207-001",
                "--root",
                str(self.root),
                "--date",
                "20260212",
                "--no-update-registry",
            ],
        )

        self.assertNotEqual(archive_result.exit_code, 0)
        self.assertIn("active milestones still exist", archive_result.output.lower())
        self.assertIn("MS001_blocking.md", archive_result.output)


if __name__ == "__main__":
    unittest.main()
