import io
import unittest
from pathlib import Path
from unittest.mock import patch

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
    @patch("agentrules.cli.services.pipeline_runner.ProjectAnalyzer")
    @patch("agentrules.cli.services.pipeline_runner.asyncio.run")
    def test_run_pipeline_executes_analysis(self, mock_asyncio_run, mock_analyzer_cls) -> None:
        buffer = io.StringIO()
        context = CliContext(console=Console(file=buffer, width=80))

        target = Path.cwd()
        analyzer_instance = mock_analyzer_cls.return_value

        pipeline_runner.run_pipeline(target, offline=False, context=context)

        mock_analyzer_cls.assert_called_once_with(target, context.console)
        mock_asyncio_run.assert_called_once()
        analyzer_instance.persist_outputs.assert_called_once()


if __name__ == "__main__":
    unittest.main()
