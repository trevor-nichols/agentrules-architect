import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rich.console import Console
from typer.testing import CliRunner

from agentrules.cli.context import CliContext
from agentrules.core.utils.execplan_registry import RegistryBuildResult, RegistryIssue


class ExecPlanRegistryCLITests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.runner = CliRunner()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_check_subcommand_invokes_check_runner(self) -> None:
        from agentrules import cli

        output_buffer = io.StringIO()
        context = CliContext(console=Console(file=output_buffer, width=120))
        result_payload = RegistryBuildResult(registry={"schema_version": 1, "plans": []}, issues=tuple())

        with patch("agentrules.cli.app.bootstrap_runtime", return_value=context), patch(
            "agentrules.cli.commands.execplan_registry.bootstrap_runtime", return_value=context
        ), patch(
            "agentrules.cli.commands.execplan_registry._run_check",
            return_value=(result_payload, 0),
        ) as mock_run_check:
            result = self.runner.invoke(
                cli.app,
                ["execplan-registry", "check", "--root", str(Path(self.temp_dir.name))],
            )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        mock_run_check.assert_called_once()

    def test_build_subcommand_returns_non_zero_on_errors(self) -> None:
        from agentrules import cli

        output_buffer = io.StringIO()
        context = CliContext(console=Console(file=output_buffer, width=120))
        result_payload = RegistryBuildResult(
            registry={"schema_version": 1, "plans": []},
            issues=(RegistryIssue("error", "Broken plan"),),
        )

        with patch("agentrules.cli.app.bootstrap_runtime", return_value=context), patch(
            "agentrules.cli.commands.execplan_registry.bootstrap_runtime", return_value=context
        ), patch(
            "agentrules.cli.commands.execplan_registry._run_build",
            return_value=(result_payload, 2),
        ):
            result = self.runner.invoke(
                cli.app,
                ["execplan-registry", "build", "--root", str(Path(self.temp_dir.name))],
            )

        self.assertEqual(result.exit_code, 2, msg=result.output)
        self.assertIn("Registry build failed.", output_buffer.getvalue())

    def test_build_subcommand_handles_filesystem_oserror(self) -> None:
        from agentrules import cli

        output_buffer = io.StringIO()
        context = CliContext(console=Console(file=output_buffer, width=120))

        with patch("agentrules.cli.app.bootstrap_runtime", return_value=context), patch(
            "agentrules.cli.commands.execplan_registry.bootstrap_runtime", return_value=context
        ), patch(
            "agentrules.cli.commands.execplan_registry._run_build",
            side_effect=PermissionError("permission denied"),
        ):
            result = self.runner.invoke(
                cli.app,
                ["execplan-registry", "build", "--root", str(Path(self.temp_dir.name))],
            )

        self.assertEqual(result.exit_code, 2, msg=result.output)
        self.assertIn("filesystem error", output_buffer.getvalue().lower())

    def test_update_subcommand_handles_filesystem_oserror(self) -> None:
        from agentrules import cli

        output_buffer = io.StringIO()
        context = CliContext(console=Console(file=output_buffer, width=120))

        with patch("agentrules.cli.app.bootstrap_runtime", return_value=context), patch(
            "agentrules.cli.commands.execplan_registry.bootstrap_runtime", return_value=context
        ), patch(
            "agentrules.cli.commands.execplan_registry._run_build",
            side_effect=PermissionError("permission denied"),
        ):
            result = self.runner.invoke(
                cli.app,
                ["execplan-registry", "update", "--root", str(Path(self.temp_dir.name))],
            )

        self.assertEqual(result.exit_code, 2, msg=result.output)
        self.assertIn("filesystem error", output_buffer.getvalue().lower())


if __name__ == "__main__":
    unittest.main()
