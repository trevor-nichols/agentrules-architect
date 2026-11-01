import tempfile
import unittest
from pathlib import Path

from agentrules.core.utils.file_creation.agent_scaffold import create_agent_scaffold, sync_agent_scaffold


class AgentScaffoldTests(unittest.TestCase):
    def test_create_agent_scaffold_materializes_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            success, messages = create_agent_scaffold(project_root)

            self.assertTrue(success)
            self.assertTrue(any(msg.startswith("Created .exec_plans/PLANS.md") for msg in messages))
            self.assertTrue(
                any(msg.startswith("Created .exec_plans/templates/MILESTONE_TEMPLATE.md") for msg in messages)
            )

            plans_path = project_root / ".exec_plans" / "PLANS.md"
            milestone_path = project_root / ".exec_plans" / "templates" / "MILESTONE_TEMPLATE.md"

            self.assertTrue(plans_path.is_file())
            self.assertTrue(milestone_path.is_file())
            self.assertIn("# Execution Plans (ExecPlans)", plans_path.read_text(encoding="utf-8"))
            self.assertIn("# Milestone Template", milestone_path.read_text(encoding="utf-8"))

    def test_create_agent_scaffold_is_idempotent_and_non_destructive(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            plans_path = project_root / ".exec_plans" / "PLANS.md"

            first_success, _ = create_agent_scaffold(project_root)
            self.assertTrue(first_success)

            plans_path.write_text("custom-plans-content", encoding="utf-8")
            second_success, second_messages = create_agent_scaffold(project_root)

            self.assertTrue(second_success)
            self.assertEqual("custom-plans-content", plans_path.read_text(encoding="utf-8"))
            self.assertTrue(any(msg.startswith("Skipped .exec_plans/PLANS.md") for msg in second_messages))

    def test_sync_agent_scaffold_check_reports_missing_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            result = sync_agent_scaffold(project_root, check=True)

            self.assertFalse(result.ok)
            self.assertFalse(result.changed)
            self.assertIn("Missing .exec_plans/PLANS.md", result.messages)
            self.assertIn("Missing .exec_plans/templates/MILESTONE_TEMPLATE.md", result.messages)
            self.assertFalse((project_root / ".exec_plans").exists())

    def test_sync_agent_scaffold_default_keeps_outdated_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            create_success, _ = create_agent_scaffold(project_root)
            self.assertTrue(create_success)

            plans_path = project_root / ".exec_plans" / "PLANS.md"
            plans_path.write_text("custom-plans-content", encoding="utf-8")

            result = sync_agent_scaffold(project_root)

            self.assertTrue(result.ok)
            self.assertFalse(result.changed)
            self.assertEqual("custom-plans-content", plans_path.read_text(encoding="utf-8"))
            self.assertTrue(any(msg.startswith("Outdated .exec_plans/PLANS.md") for msg in result.messages))

    def test_sync_agent_scaffold_force_updates_with_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            create_success, _ = create_agent_scaffold(project_root)
            self.assertTrue(create_success)

            milestone_path = project_root / ".exec_plans" / "templates" / "MILESTONE_TEMPLATE.md"
            milestone_path.write_text("custom-milestone-template", encoding="utf-8")

            result = sync_agent_scaffold(project_root, force=True)

            self.assertTrue(result.ok)
            self.assertTrue(result.changed)
            self.assertIn("# Milestone Template", milestone_path.read_text(encoding="utf-8"))
            backup_candidates = list(milestone_path.parent.glob("MILESTONE_TEMPLATE.md.bak.*"))
            self.assertTrue(backup_candidates)
            self.assertTrue(
                any(msg.startswith("Updated .exec_plans/templates/MILESTONE_TEMPLATE.md") for msg in result.messages)
            )

    def test_sync_agent_scaffold_rejects_check_and_force_combination(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            with self.assertRaisesRegex(ValueError, "Cannot combine check and force"):
                sync_agent_scaffold(project_root, check=True, force=True)

    def test_sync_agent_scaffold_rejects_symlinked_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            project_root = workspace / "repo"
            project_root.mkdir(parents=True, exist_ok=True)
            outside_path = workspace / "outside.txt"
            outside_path.write_text("outside", encoding="utf-8")

            create_success, _ = create_agent_scaffold(project_root)
            self.assertTrue(create_success)

            plans_path = project_root / ".exec_plans" / "PLANS.md"
            plans_path.unlink()
            try:
                plans_path.symlink_to(outside_path)
            except OSError as error:
                self.skipTest(f"Symlinks unavailable on this platform: {error}")

            with self.assertRaisesRegex(ValueError, "Symlinked scaffold path is not allowed"):
                sync_agent_scaffold(project_root, force=True)

            self.assertEqual("outside", outside_path.read_text(encoding="utf-8"))

    def test_sync_agent_scaffold_rejects_symlinked_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            project_root = workspace / "repo"
            project_root.mkdir(parents=True, exist_ok=True)
            external_workspace_dir = workspace / "external-exec-plans"
            external_workspace_dir.mkdir(parents=True, exist_ok=True)

            workspace_dir = project_root / ".exec_plans"
            try:
                workspace_dir.symlink_to(external_workspace_dir, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"Symlinks unavailable on this platform: {error}")

            with self.assertRaisesRegex(ValueError, "Symlinked scaffold path is not allowed"):
                sync_agent_scaffold(project_root)

    def test_create_agent_scaffold_reports_error_for_symlinked_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            project_root = workspace / "repo"
            project_root.mkdir(parents=True, exist_ok=True)
            outside_path = workspace / "outside.txt"
            outside_path.write_text("outside", encoding="utf-8")

            (project_root / ".exec_plans").mkdir(parents=True, exist_ok=True)
            plans_path = project_root / ".exec_plans" / "PLANS.md"
            try:
                plans_path.symlink_to(outside_path)
            except OSError as error:
                self.skipTest(f"Symlinks unavailable on this platform: {error}")

            success, messages = create_agent_scaffold(project_root)
            self.assertFalse(success)
            self.assertTrue(any("Symlinked scaffold path is not allowed" in message for message in messages))

    def test_create_agent_scaffold_refuses_legacy_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / ".agent" / "exec_plans").mkdir(parents=True)

            success, messages = create_agent_scaffold(project_root)

            self.assertFalse(success)
            self.assertTrue(any("Run `agentrules execplan migrate`" in message for message in messages))
            self.assertFalse((project_root / ".exec_plans").exists())

    def test_sync_agent_scaffold_refuses_legacy_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / ".agent").mkdir()
            (project_root / ".agent" / "PLANS.md").write_text("# legacy guide\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Run `agentrules execplan migrate`"):
                sync_agent_scaffold(project_root, force=True)

            self.assertFalse((project_root / ".exec_plans").exists())


if __name__ == "__main__":
    unittest.main()
