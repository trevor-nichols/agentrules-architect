import tempfile
import unittest
from pathlib import Path

from agentrules.core.utils.formatters.clean_agentrules import ensure_execplans_guidance


class EnsureExecPlansGuidanceTests(unittest.TestCase):
    def test_inserts_execplans_under_development_principles(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_path = Path(tmpdir) / "AGENTS.md"
            rules_path.write_text(
                (
                    "You are a coding agent.\n\n"
                    "# Development Principles:\n"
                    "- Keep changes maintainable.\n\n"
                    "# 2. TEMPORAL FRAMEWORK\n"
                    "It is February 2026.\n"
                ),
                encoding="utf-8",
            )

            success, message = ensure_execplans_guidance(tmpdir, filename="AGENTS.md")
            content = rules_path.read_text(encoding="utf-8")

            self.assertTrue(success)
            self.assertIn("Added ExecPlans guidance", message)
            self.assertIn("## ExecPlans", content)
            self.assertIn(
                "When writing complex features or significant refactors, use an ExecPlan",
                content,
            )
            self.assertLess(content.index("## ExecPlans"), content.index("# 2. TEMPORAL FRAMEWORK"))

    def test_is_idempotent_when_guidance_already_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_path = Path(tmpdir) / "AGENTS.md"
            original = (
                "You are a coding agent.\n\n"
                "# Development Principles:\n"
                "- Keep changes maintainable.\n\n"
                "## ExecPlans\n"
                "When writing complex features or significant refactors, "
                "use an ExecPlan (as described in .agent/PLANS.md) from design to implementation.\n\n"
                "# 2. TEMPORAL FRAMEWORK\n"
                "It is February 2026.\n"
            )
            rules_path.write_text(original, encoding="utf-8")

            success, message = ensure_execplans_guidance(tmpdir, filename="AGENTS.md")
            content = rules_path.read_text(encoding="utf-8")

            self.assertTrue(success)
            self.assertIn("already present", message.lower())
            self.assertEqual(original, content)

    def test_adds_section_when_development_principles_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_path = Path(tmpdir) / "AGENTS.md"
            rules_path.write_text(
                "You are a coding agent.\n\n# 2. TEMPORAL FRAMEWORK\nIt is February 2026.\n",
                encoding="utf-8",
            )

            success, message = ensure_execplans_guidance(tmpdir, filename="AGENTS.md")
            content = rules_path.read_text(encoding="utf-8")

            self.assertTrue(success)
            self.assertIn("missing Development Principles section", message)
            self.assertIn("# Development Principles", content)
            self.assertIn("## ExecPlans", content)


if __name__ == "__main__":
    unittest.main()
