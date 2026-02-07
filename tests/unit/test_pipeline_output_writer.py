import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from agentrules.core.pipeline import (
    EffectiveExclusions,
    GitignoreSnapshot,
    PipelineMetrics,
    PipelineOutputOptions,
    PipelineOutputWriter,
    PipelineResult,
    PipelineSettings,
    ProjectSnapshot,
)


class PipelineOutputWriterTests(unittest.TestCase):
    @patch("agentrules.core.pipeline.output.ensure_execplans_guidance")
    @patch("agentrules.core.pipeline.output.clean_agentrules")
    @patch("agentrules.core.pipeline.output.create_agent_scaffold")
    @patch("agentrules.core.pipeline.output.create_cursorignore")
    @patch("agentrules.core.pipeline.output.save_phase_outputs")
    def test_persist_writes_expected_artifacts(
        self,
        mock_save_phase_outputs,
        mock_create_cursorignore,
        mock_create_agent_scaffold,
        mock_clean_agentrules,
        mock_ensure_execplans_guidance,
    ) -> None:
        mock_create_cursorignore.return_value = (True, ".cursorignore created")
        mock_create_agent_scaffold.return_value = (
            True,
            [
                "Created .agent/PLANS.md",
                "Created .agent/templates/MILESTONE_TEMPLATE.md",
            ],
        )
        mock_clean_agentrules.return_value = (True, "cleaned")
        mock_ensure_execplans_guidance.return_value = (True, "Added ExecPlans guidance under Development Principles.")

        settings = PipelineSettings(
            target_directory=Path("/tmp/project"),
            tree_max_depth=4,
            respect_gitignore=True,
            effective_exclusions=EffectiveExclusions(
                directories=frozenset({"build"}),
                files=frozenset(),
                extensions=frozenset(),
            ),
            exclusion_overrides=MagicMock(is_empty=lambda: False),
        )

        snapshot = ProjectSnapshot(
            tree_with_delimiters=("<project_structure>", "src/", "</project_structure>"),
            tree=("src/",),
            dependency_info={"manifests": []},
            gitignore=GitignoreSnapshot(spec=None, path=Path("/tmp/project/.gitignore")),
        )
        result = PipelineResult(
            snapshot=snapshot,
            phase1={"phase": 1},
            phase2={"plan": {"agents": []}},
            phase3={"phase": 3},
            phase4={"analysis": "ok"},
            consolidated_report={"report": "all good"},
            final_analysis={"analysis": "done"},
            metrics=PipelineMetrics(elapsed_seconds=2.5),
        )
        options = PipelineOutputOptions(
            rules_filename="AGENTS.md",
            generate_phase_outputs=True,
            generate_cursorignore=True,
            generate_agent_scaffold=True,
        )

        writer = PipelineOutputWriter()
        summary = writer.persist(result, settings, options)

        mock_save_phase_outputs.assert_called_once()
        save_kwargs = mock_save_phase_outputs.call_args.kwargs
        self.assertEqual(save_kwargs["tree_max_depth"], 4)
        self.assertTrue(save_kwargs["include_phase_files"])
        self.assertEqual(save_kwargs["gitignore_info"]["path"], str(snapshot.gitignore.path))

        mock_create_cursorignore.assert_called_once_with(str(settings.target_directory))
        mock_create_agent_scaffold.assert_called_once_with(settings.target_directory)
        mock_clean_agentrules.assert_called_once_with(
            str(settings.target_directory),
            filename="AGENTS.md",
        )
        mock_ensure_execplans_guidance.assert_called_once_with(
            str(settings.target_directory),
            filename="AGENTS.md",
        )

        self.assertIn("Individual phase outputs saved to:", " ".join(summary.messages))
        self.assertIn("Cursor ignore created at:", " ".join(summary.messages))
        self.assertIn("Created .agent/PLANS.md", " ".join(summary.messages))
        self.assertIn("Added ExecPlans guidance under Development Principles.", " ".join(summary.messages))
        self.assertIn("Cleaned Agent rules file", " ".join(summary.messages))
        self.assertIn("Execution metrics saved to:", " ".join(summary.messages))

    @patch("agentrules.core.pipeline.output.ensure_execplans_guidance")
    @patch("agentrules.core.pipeline.output.clean_agentrules")
    @patch("agentrules.core.pipeline.output.create_agent_scaffold")
    @patch("agentrules.core.pipeline.output.create_cursorignore")
    @patch("agentrules.core.pipeline.output.save_phase_outputs")
    def test_persist_handles_disabled_options(
        self,
        mock_save_phase_outputs,
        mock_create_cursorignore,
        mock_create_agent_scaffold,
        mock_clean_agentrules,
        mock_ensure_execplans_guidance,
    ) -> None:
        mock_clean_agentrules.return_value = (False, "not found")
        mock_ensure_execplans_guidance.return_value = (True, "ExecPlans guidance already present.")

        settings = PipelineSettings(
            target_directory=Path("/workspace/project"),
            tree_max_depth=2,
            respect_gitignore=False,
            effective_exclusions=EffectiveExclusions(
                directories=frozenset(),
                files=frozenset(),
                extensions=frozenset(),
            ),
            exclusion_overrides=None,
        )
        snapshot = ProjectSnapshot(
            tree_with_delimiters=("src/",),
            tree=("src/",),
            dependency_info={},
            gitignore=GitignoreSnapshot(spec=None, path=None),
        )
        result = PipelineResult(
            snapshot=snapshot,
            phase1={},
            phase2={},
            phase3={},
            phase4={},
            consolidated_report={},
            final_analysis={},
            metrics=PipelineMetrics(elapsed_seconds=1.0),
        )
        options = PipelineOutputOptions(
            rules_filename="AGENTS.md",
            generate_phase_outputs=False,
            generate_cursorignore=False,
            generate_agent_scaffold=False,
        )

        writer = PipelineOutputWriter()
        summary = writer.persist(result, settings, options)

        mock_save_phase_outputs.assert_called_once()
        save_kwargs = mock_save_phase_outputs.call_args.kwargs
        self.assertFalse(save_kwargs["include_phase_files"])

        mock_create_cursorignore.assert_not_called()
        mock_create_agent_scaffold.assert_not_called()
        mock_clean_agentrules.assert_called_once()
        mock_ensure_execplans_guidance.assert_called_once()

        joined = " ".join(summary.messages)
        self.assertIn("Skipped phase report archive", joined)
        self.assertIn("Skipped .cursorignore generation", joined)
        self.assertIn("Skipped .agent scaffold generation", joined)
        self.assertIn("ExecPlans guidance already present.", joined)
        self.assertIn("not found", joined)


if __name__ == "__main__":
    unittest.main()
