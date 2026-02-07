import json
import os
import tempfile
import unittest
from pathlib import Path

from agentrules.core.utils.execplan_creator import create_execplan


class ExecPlanCreatorTests(unittest.TestCase):
    def test_create_execplan_creates_plan_and_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"
            registry_path = execplans_dir / "registry.json"

            result = create_execplan(
                root=root,
                title="Auth Refresh Flow",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                registry_path=registry_path,
                update_registry=True,
            )

            self.assertEqual(result.plan_id, "EP-20260207-001")
            self.assertTrue(result.plan_path.exists())
            self.assertEqual(result.plan_path.name, "EP-20260207-001_auth-refresh-flow.md")
            self.assertIsNotNone(result.registry_result)
            self.assertTrue(registry_path.exists())

            payload = json.loads(registry_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(len(payload["plans"]), 1)
            self.assertEqual(payload["plans"][0]["id"], "EP-20260207-001")

    def test_create_execplan_increments_sequence_ignoring_milestones(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            first = create_execplan(
                root=root,
                title="Billing Foundation",
                slug="billing",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                update_registry=False,
            )
            self.assertEqual(first.plan_id, "EP-20260207-001")

            milestone = execplans_dir / "billing" / "milestones" / "active" / "EP-20260207-050_MS001_probe.md"
            milestone.parent.mkdir(parents=True, exist_ok=True)
            milestone.write_text("# milestone", encoding="utf-8")

            second = create_execplan(
                root=root,
                title="Billing Follow Up",
                slug="billing-follow-up",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                update_registry=False,
            )
            self.assertEqual(second.plan_id, "EP-20260207-002")

    def test_create_execplan_counts_slug_named_milestones(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            first = create_execplan(
                root=root,
                title="Milestones",
                slug="milestones",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                update_registry=False,
            )
            self.assertEqual(first.plan_id, "EP-20260207-001")

            second = create_execplan(
                root=root,
                title="Another Plan",
                slug="another-plan",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                update_registry=False,
            )
            self.assertEqual(second.plan_id, "EP-20260207-002")

    def test_create_execplan_counts_id_only_md_filename_for_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            legacy = execplans_dir / "legacy" / "EP-20260207-001.md"
            legacy.parent.mkdir(parents=True, exist_ok=True)
            legacy.write_text("# legacy plan\n", encoding="utf-8")

            created = create_execplan(
                root=root,
                title="New Plan",
                slug="new-plan",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                update_registry=False,
            )
            self.assertEqual(created.plan_id, "EP-20260207-002")

    def test_create_execplan_updates_registry_with_existing_block_list_front_matter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"
            existing = execplans_dir / "legacy" / "EP-20260207-001_legacy.md"
            existing.parent.mkdir(parents=True, exist_ok=True)
            existing.write_text(
                (
                    "---\n"
                    "id: EP-20260207-001\n"
                    'title: "Legacy Plan"\n'
                    "status: planned\n"
                    "kind: feature\n"
                    "domain: backend\n"
                    'owner: "@codex"\n'
                    "created: 2026-02-07\n"
                    "updated: 2026-02-07\n"
                    "tags:\n"
                    "  - legacy\n"
                    "touches:\n"
                    "  - cli\n"
                    "risk: low\n"
                    "breaking: false\n"
                    "migration: false\n"
                    "links:\n"
                    '  issue: ""\n'
                    '  pr: ""\n'
                    '  docs: ""\n'
                    "depends_on: []\n"
                    "supersedes: []\n"
                    "---\n\n"
                    "# Legacy\n"
                ),
                encoding="utf-8",
            )

            created = create_execplan(
                root=root,
                title="New Plan",
                slug="new-plan",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                update_registry=True,
            )
            self.assertEqual(created.plan_id, "EP-20260207-002")
            self.assertIsNotNone(created.registry_result)
            self.assertEqual(created.registry_result.error_count, 0)

    def test_create_execplan_requires_valid_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            with self.assertRaisesRegex(ValueError, "derive a valid slug"):
                create_execplan(
                    root=root,
                    title="!!!",
                    execplans_dir=execplans_dir,
                    update_registry=False,
                )

    def test_create_execplan_validates_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            with self.assertRaisesRegex(ValueError, "YYYYMMDD"):
                create_execplan(
                    root=root,
                    title="Invalid Date",
                    date_yyyymmdd="2026-02-07",
                    execplans_dir=execplans_dir,
                    update_registry=False,
                )

    def test_create_execplan_rejects_non_eight_digit_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            with self.assertRaisesRegex(ValueError, "YYYYMMDD"):
                create_execplan(
                    root=root,
                    title="Short Date Token",
                    date_yyyymmdd="2026027",
                    execplans_dir=execplans_dir,
                    update_registry=False,
                )

    def test_create_execplan_rejects_multiline_title_without_writing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            with self.assertRaisesRegex(ValueError, "single-line"):
                create_execplan(
                    root=root,
                    title="Line 1\nLine 2",
                    execplans_dir=execplans_dir,
                    update_registry=True,
                )

            self.assertFalse(any(execplans_dir.rglob("EP-*.md")))

    def test_create_execplan_rejects_multiline_owner_without_writing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            with self.assertRaisesRegex(ValueError, "single-line"):
                create_execplan(
                    root=root,
                    title="Valid Title",
                    owner="@owner\nextra",
                    execplans_dir=execplans_dir,
                    update_registry=True,
                )

            self.assertFalse(any(execplans_dir.rglob("EP-*.md")))

    def test_create_execplan_resolves_default_paths_from_root(self) -> None:
        with tempfile.TemporaryDirectory() as root_tmp, tempfile.TemporaryDirectory() as cwd_tmp:
            root = Path(root_tmp).resolve()
            cwd = Path(cwd_tmp).resolve()
            original_cwd = Path.cwd()
            try:
                os.chdir(cwd)
                result = create_execplan(
                    root=root,
                    title="Root Relative Defaults",
                    date_yyyymmdd="20260207",
                    update_registry=True,
                )
            finally:
                os.chdir(original_cwd)

            self.assertTrue(result.plan_path.resolve().is_relative_to(root))
            self.assertTrue((root / ".agent" / "exec_plans" / "registry.json").exists())
            self.assertFalse((cwd / ".agent" / "exec_plans" / "registry.json").exists())


if __name__ == "__main__":
    unittest.main()
