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

        plan_path = self.root / ".agent" / "exec_plans" / "auth-refresh" / "EP-20260207-001_auth-refresh.md"
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
        created = self.root / ".agent" / "exec_plans" / "good-plan" / "EP-20260207-002_good-plan.md"
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


if __name__ == "__main__":
    unittest.main()
