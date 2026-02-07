import io
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from rich.console import Console

from agentrules.cli.context import CliContext, format_secret_status, mask_secret
from agentrules.cli.services import pipeline_runner


class MaskSecretTests(unittest.TestCase):
    def test_mask_secret_handles_common_cases(self) -> None:
        self.assertEqual(mask_secret(None), "Not set")
        self.assertEqual(mask_secret("abc"), "***")
        self.assertEqual(mask_secret("abcdef"), "******")
        self.assertEqual(mask_secret("abcdefgh"), "abc…fgh")


class SecretStatusTests(unittest.TestCase):
    def test_format_secret_status_uses_color_tokens(self) -> None:
        self.assertEqual(format_secret_status(None), "[red]Not set[/]")
        self.assertEqual(format_secret_status("value"), "[green]Configured[/]")


class PipelineRunnerTests(unittest.TestCase):
    @patch("agentrules.cli.services.pipeline_runner.PipelineOutputWriter")
    @patch("agentrules.cli.services.pipeline_runner.asyncio.run")
    @patch("agentrules.cli.services.pipeline_runner.build_project_snapshot")
    @patch("agentrules.cli.services.pipeline_runner.create_default_pipeline")
    @patch("agentrules.cli.services.pipeline_runner.get_config_manager")
    def test_run_pipeline_executes_analysis(
        self,
        mock_get_config_manager,
        mock_create_pipeline,
        mock_build_snapshot,
        mock_asyncio_run,
        mock_output_writer_cls,
    ) -> None:
        buffer = io.StringIO()
        context = CliContext(console=Console(file=buffer, width=80))

        target = Path.cwd()

        mock_config = MagicMock()
        mock_config.get_exclusion_overrides.return_value = MagicMock(is_empty=lambda: True)
        mock_config.get_effective_exclusions.return_value = (set(), set(), set())
        mock_config.get_tree_max_depth.return_value = 5
        mock_config.should_respect_gitignore.return_value = True
        mock_config.is_researcher_enabled.return_value = False
        mock_config.get_rules_filename.return_value = "AGENTS.md"
        mock_config.should_generate_phase_outputs.return_value = True
        mock_config.should_generate_cursorignore.return_value = True
        mock_config.should_generate_agent_scaffold.return_value = True
        mock_get_config_manager.return_value = mock_config

        mock_snapshot = MagicMock()
        mock_build_snapshot.return_value = mock_snapshot

        mock_pipeline = MagicMock()
        mock_create_pipeline.return_value = mock_pipeline

        mock_result = MagicMock()
        mock_asyncio_run.return_value = mock_result

        mock_summary = MagicMock(messages=["summary message"])
        mock_writer_instance = mock_output_writer_cls.return_value
        mock_writer_instance.persist.return_value = mock_summary

        pipeline_runner.run_pipeline(target, offline=False, context=context)

        mock_create_pipeline.assert_called_once()
        mock_asyncio_run.assert_called_once()
        mock_writer_instance.persist.assert_called_once()
        output_options = mock_writer_instance.persist.call_args.args[2]
        self.assertTrue(output_options.generate_agent_scaffold)

        output = buffer.getvalue()
        self.assertIn("Analysis finished for:", output)


if __name__ == "__main__":
    unittest.main()
