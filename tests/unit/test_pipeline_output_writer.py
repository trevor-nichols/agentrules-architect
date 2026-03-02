import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
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
    @patch("agentrules.core.pipeline.output.sync_snapshot_artifact")
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
        mock_sync_snapshot,
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
        mock_sync_snapshot.return_value = MagicMock(
            changed=True,
            output_path=Path("/tmp/project/SNAPSHOT.md"),
            added_paths=("src/new.py",),
            removed_paths=("src/old.py",),
            preserved_comments=2,
            tree_entries=3,
            file_entries=1,
        )

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
            rules_tree_max_depth=3,
            snapshot_filename="SNAPSHOT.md",
            generate_phase_outputs=True,
            generate_cursorignore=True,
            generate_agent_scaffold=True,
            generate_snapshot=True,
        )

        writer = PipelineOutputWriter()
        summary = writer.persist(result, settings, options)

        mock_save_phase_outputs.assert_called_once()
        save_kwargs = mock_save_phase_outputs.call_args.kwargs
        self.assertEqual(save_kwargs["tree_max_depth"], 4)
        self.assertEqual(save_kwargs["rules_tree_max_depth"], 3)
        self.assertEqual(save_kwargs["snapshot_reference_filename"], "SNAPSHOT.md")
        self.assertTrue(save_kwargs["include_phase_files"])
        self.assertEqual(save_kwargs["gitignore_info"]["path"], str(snapshot.gitignore.path))

        mock_create_cursorignore.assert_called_once_with(str(settings.target_directory))
        mock_create_agent_scaffold.assert_called_once_with(settings.target_directory)
        mock_sync_snapshot.assert_called_once()
        snapshot_kwargs = mock_sync_snapshot.call_args.kwargs
        self.assertEqual(
            snapshot_kwargs["additional_exclude_relative_paths"],
            {"phases_output", "AGENTS.md"},
        )
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
        self.assertIn("Snapshot artifact written to:", " ".join(summary.messages))
        self.assertIn("Execution metrics saved to:", " ".join(summary.messages))

    @patch("agentrules.core.pipeline.output.sync_snapshot_artifact")
    @patch("agentrules.core.pipeline.output.ensure_execplans_guidance")
    @patch("agentrules.core.pipeline.output.clean_agentrules")
    @patch("agentrules.core.pipeline.output.create_agent_scaffold")
    @patch("agentrules.core.pipeline.output.create_cursorignore")
    @patch("agentrules.core.pipeline.output.save_phase_outputs")
    def test_persist_materializes_optional_outputs_before_snapshot_sync(
        self,
        mock_save_phase_outputs,
        mock_create_cursorignore,
        mock_create_agent_scaffold,
        mock_clean_agentrules,
        mock_ensure_execplans_guidance,
        mock_sync_snapshot,
    ) -> None:
        mock_clean_agentrules.return_value = (True, "cleaned")
        mock_ensure_execplans_guidance.return_value = (True, "ExecPlans guidance already present.")

        with TemporaryDirectory() as tmpdir:
            target_directory = Path(tmpdir)
            snapshot_path = target_directory / "SNAPSHOT.md"

            def _create_cursorignore(_path: str) -> tuple[bool, str]:
                (target_directory / ".cursorignore").write_text("*.tmp\n", encoding="utf-8")
                return True, ".cursorignore created"

            def _create_agent_scaffold(_path: Path) -> tuple[bool, list[str]]:
                scaffold_dir = target_directory / ".agent"
                scaffold_dir.mkdir(parents=True, exist_ok=True)
                (scaffold_dir / "PLANS.md").write_text("# plans\n", encoding="utf-8")
                return True, ["Created .agent/PLANS.md"]

            def _sync_snapshot(*_args, **_kwargs):
                self.assertTrue((target_directory / ".cursorignore").exists())
                self.assertTrue((target_directory / ".agent" / "PLANS.md").exists())
                snapshot_path.write_text("<project_structure>\n</project_structure>\n", encoding="utf-8")
                return MagicMock(
                    changed=True,
                    output_path=snapshot_path,
                    added_paths=(),
                    removed_paths=(),
                    preserved_comments=0,
                    tree_entries=0,
                    file_entries=0,
                )

            mock_create_cursorignore.side_effect = _create_cursorignore
            mock_create_agent_scaffold.side_effect = _create_agent_scaffold
            mock_sync_snapshot.side_effect = _sync_snapshot

            settings = PipelineSettings(
                target_directory=target_directory,
                tree_max_depth=4,
                respect_gitignore=True,
                effective_exclusions=EffectiveExclusions(
                    directories=frozenset(),
                    files=frozenset(),
                    extensions=frozenset(),
                ),
                exclusion_overrides=None,
            )
            snapshot = ProjectSnapshot(
                tree_with_delimiters=("<project_structure>", "src/", "</project_structure>"),
                tree=("src/",),
                dependency_info={"manifests": []},
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
                rules_tree_max_depth=3,
                snapshot_filename="SNAPSHOT.md",
                generate_phase_outputs=False,
                generate_cursorignore=True,
                generate_agent_scaffold=True,
                generate_snapshot=True,
            )

            writer = PipelineOutputWriter()
            summary = writer.persist(result, settings, options)

        mock_sync_snapshot.assert_called_once()
        mock_save_phase_outputs.assert_called_once()
        save_kwargs = mock_save_phase_outputs.call_args.kwargs
        self.assertEqual(save_kwargs["snapshot_reference_filename"], "SNAPSHOT.md")
        self.assertIn("Snapshot artifact written to:", " ".join(summary.messages))

    @patch("agentrules.core.pipeline.output.sync_snapshot_artifact")
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
        mock_sync_snapshot,
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
            rules_tree_max_depth=3,
            snapshot_filename="SNAPSHOT.md",
            generate_phase_outputs=False,
            generate_cursorignore=False,
            generate_agent_scaffold=False,
            generate_snapshot=False,
        )

        writer = PipelineOutputWriter()
        summary = writer.persist(result, settings, options)

        mock_save_phase_outputs.assert_called_once()
        save_kwargs = mock_save_phase_outputs.call_args.kwargs
        self.assertFalse(save_kwargs["include_phase_files"])
        self.assertEqual(save_kwargs["rules_tree_max_depth"], 3)
        self.assertIsNone(save_kwargs["snapshot_reference_filename"])

        mock_create_cursorignore.assert_not_called()
        mock_create_agent_scaffold.assert_not_called()
        mock_sync_snapshot.assert_not_called()
        mock_clean_agentrules.assert_called_once()
        mock_ensure_execplans_guidance.assert_called_once()

        joined = " ".join(summary.messages)
        self.assertIn("Skipped phase report archive", joined)
        self.assertIn("Skipped .cursorignore generation", joined)
        self.assertIn("Skipped .agent scaffold generation", joined)
        self.assertIn("Skipped snapshot artifact generation", joined)
        self.assertIn("ExecPlans guidance already present.", joined)
        self.assertIn("not found", joined)

    @patch("agentrules.core.pipeline.output.sync_snapshot_artifact")
    @patch("agentrules.core.pipeline.output.ensure_execplans_guidance")
    @patch("agentrules.core.pipeline.output.clean_agentrules")
    @patch("agentrules.core.pipeline.output.create_agent_scaffold")
    @patch("agentrules.core.pipeline.output.create_cursorignore")
    @patch("agentrules.core.pipeline.output.save_phase_outputs")
    def test_persist_reports_snapshot_failures_without_crashing(
        self,
        mock_save_phase_outputs,
        mock_create_cursorignore,
        mock_create_agent_scaffold,
        mock_clean_agentrules,
        mock_ensure_execplans_guidance,
        mock_sync_snapshot,
    ) -> None:
        mock_clean_agentrules.return_value = (True, "cleaned")
        mock_ensure_execplans_guidance.return_value = (True, "ExecPlans guidance already present.")
        mock_sync_snapshot.side_effect = PermissionError("permission denied")

        settings = PipelineSettings(
            target_directory=Path("/workspace/project"),
            tree_max_depth=2,
            respect_gitignore=True,
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
            gitignore=GitignoreSnapshot(spec=None, path=Path("/workspace/project/.gitignore")),
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
            rules_tree_max_depth=3,
            snapshot_filename="SNAPSHOT.md",
            generate_phase_outputs=False,
            generate_cursorignore=False,
            generate_agent_scaffold=False,
            generate_snapshot=True,
        )

        writer = PipelineOutputWriter()
        summary = writer.persist(result, settings, options)

        mock_save_phase_outputs.assert_called_once()
        save_kwargs = mock_save_phase_outputs.call_args.kwargs
        self.assertIsNone(save_kwargs["snapshot_reference_filename"])
        mock_create_cursorignore.assert_not_called()
        mock_create_agent_scaffold.assert_not_called()
        mock_sync_snapshot.assert_called_once()

        joined = " ".join(summary.messages)
        self.assertIn("Snapshot artifact generation failed:", joined)
        self.assertIn("permission denied", joined)
        self.assertIn("Cleaned Agent rules file", joined)

    @patch("agentrules.core.pipeline.output.sync_snapshot_artifact")
    @patch("agentrules.core.pipeline.output.ensure_execplans_guidance")
    @patch("agentrules.core.pipeline.output.clean_agentrules")
    @patch("agentrules.core.pipeline.output.create_agent_scaffold")
    @patch("agentrules.core.pipeline.output.create_cursorignore")
    @patch("agentrules.core.pipeline.output.save_phase_outputs")
    def test_persist_does_not_set_snapshot_reference_for_directory_target_on_failure(
        self,
        mock_save_phase_outputs,
        mock_create_cursorignore,
        mock_create_agent_scaffold,
        mock_clean_agentrules,
        mock_ensure_execplans_guidance,
        mock_sync_snapshot,
    ) -> None:
        mock_clean_agentrules.return_value = (True, "cleaned")
        mock_ensure_execplans_guidance.return_value = (True, "ExecPlans guidance already present.")
        mock_sync_snapshot.side_effect = PermissionError("permission denied")

        with TemporaryDirectory() as tmpdir:
            target_directory = Path(tmpdir)
            (target_directory / "snapshot").mkdir()

            settings = PipelineSettings(
                target_directory=target_directory,
                tree_max_depth=2,
                respect_gitignore=True,
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
                gitignore=GitignoreSnapshot(spec=None, path=target_directory / ".gitignore"),
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
                rules_tree_max_depth=3,
                snapshot_filename="snapshot",
                generate_phase_outputs=False,
                generate_cursorignore=False,
                generate_agent_scaffold=False,
                generate_snapshot=True,
            )

            writer = PipelineOutputWriter()
            summary = writer.persist(result, settings, options)

        mock_save_phase_outputs.assert_called_once()
        save_kwargs = mock_save_phase_outputs.call_args.kwargs
        self.assertIsNone(save_kwargs["snapshot_reference_filename"])
        self.assertIn("Snapshot artifact generation failed:", " ".join(summary.messages))

    @patch("agentrules.core.pipeline.output.sync_snapshot_artifact")
    @patch("agentrules.core.pipeline.output.ensure_execplans_guidance")
    @patch("agentrules.core.pipeline.output.clean_agentrules")
    @patch("agentrules.core.pipeline.output.create_agent_scaffold")
    @patch("agentrules.core.pipeline.output.create_cursorignore")
    @patch("agentrules.core.pipeline.output.save_phase_outputs")
    def test_persist_handles_cursorignore_exception_without_blocking_rules_output(
        self,
        mock_save_phase_outputs,
        mock_create_cursorignore,
        mock_create_agent_scaffold,
        mock_clean_agentrules,
        mock_ensure_execplans_guidance,
        mock_sync_snapshot,
    ) -> None:
        mock_create_cursorignore.side_effect = PermissionError("permission denied")
        mock_clean_agentrules.return_value = (True, "cleaned")
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
            rules_tree_max_depth=3,
            snapshot_filename="SNAPSHOT.md",
            generate_phase_outputs=False,
            generate_cursorignore=True,
            generate_agent_scaffold=False,
            generate_snapshot=False,
        )

        writer = PipelineOutputWriter()
        summary = writer.persist(result, settings, options)

        mock_save_phase_outputs.assert_called_once()
        save_kwargs = mock_save_phase_outputs.call_args.kwargs
        self.assertIsNone(save_kwargs["snapshot_reference_filename"])
        mock_create_agent_scaffold.assert_not_called()
        mock_sync_snapshot.assert_not_called()
        joined = " ".join(summary.messages)
        self.assertIn("Cursor ignore generation failed:", joined)
        self.assertIn("permission denied", joined)
        self.assertIn("Agent rules created at:", joined)


if __name__ == "__main__":
    unittest.main()
