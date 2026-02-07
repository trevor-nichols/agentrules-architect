import tempfile
import unittest
from pathlib import Path

from agentrules.core.utils.file_creation.agent_scaffold import create_agent_scaffold


class AgentScaffoldTests(unittest.TestCase):
    def test_create_agent_scaffold_materializes_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            success, messages = create_agent_scaffold(project_root)

            self.assertTrue(success)
            self.assertTrue(any(msg.startswith("Created .agent/PLANS.md") for msg in messages))
            self.assertTrue(
                any(msg.startswith("Created .agent/templates/MILESTONE_TEMPLATE.md") for msg in messages)
            )

            plans_path = project_root / ".agent" / "PLANS.md"
            milestone_path = project_root / ".agent" / "templates" / "MILESTONE_TEMPLATE.md"

            self.assertTrue(plans_path.is_file())
            self.assertTrue(milestone_path.is_file())
            self.assertIn("# Codex Execution Plans", plans_path.read_text(encoding="utf-8"))
            self.assertIn("# Milestone Template", milestone_path.read_text(encoding="utf-8"))

    def test_create_agent_scaffold_is_idempotent_and_non_destructive(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            plans_path = project_root / ".agent" / "PLANS.md"

            first_success, _ = create_agent_scaffold(project_root)
            self.assertTrue(first_success)

            plans_path.write_text("custom-plans-content", encoding="utf-8")
            second_success, second_messages = create_agent_scaffold(project_root)

            self.assertTrue(second_success)
            self.assertEqual("custom-plans-content", plans_path.read_text(encoding="utf-8"))
            self.assertTrue(any(msg.startswith("Skipped .agent/PLANS.md") for msg in second_messages))


if __name__ == "__main__":
    unittest.main()
