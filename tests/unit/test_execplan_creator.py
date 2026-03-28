import json
import os
import tempfile
import unittest
from pathlib import Path

from agentrules.core.execplan.creator import archive_execplan, create_execplan


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

    def test_create_execplan_writes_under_active_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            result = create_execplan(
                root=root,
                title="Frontend Architecture Refactor",
                slug="frontend-architecture-refactor",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                update_registry=False,
            )

            expected = (
                execplans_dir
                / "active"
                / "frontend-architecture-refactor"
                / "EP-20260207-001_frontend-architecture-refactor.md"
            )
            self.assertEqual(result.plan_path.resolve(), expected.resolve())
            self.assertTrue(expected.exists())

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

            milestone = (
                execplans_dir
                / "active"
                / "billing"
                / "milestones"
                / "active"
                / "EP-20260207-050_MS001_probe.md"
            )
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

            with self.assertRaisesRegex(ValueError, "reserved for internal milestone namespace paths"):
                create_execplan(
                    root=root,
                    title="Milestones",
                    slug="milestones",
                    date_yyyymmdd="20260207",
                    execplans_dir=execplans_dir,
                    update_registry=False,
                )

            first = create_execplan(
                root=root,
                title="Another Plan",
                slug="another-plan",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                update_registry=False,
            )
            self.assertEqual(first.plan_id, "EP-20260207-001")

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
            registry_result = created.registry_result
            self.assertIsNotNone(registry_result)
            if registry_result is None:
                self.fail("Expected registry result when update_registry=True.")
            self.assertEqual(registry_result.error_count, 0)

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

    def test_create_execplan_rejects_reserved_namespace_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            with self.assertRaisesRegex(ValueError, "reserved for ExecPlan directory layout roots"):
                create_execplan(
                    root=root,
                    title="Archive Root Collision",
                    slug="archive",
                    date_yyyymmdd="20260207",
                    execplans_dir=execplans_dir,
                    update_registry=False,
                )

            with self.assertRaisesRegex(ValueError, "reserved for ExecPlan directory layout roots"):
                create_execplan(
                    root=root,
                    title="Complete Root Collision",
                    slug="complete",
                    date_yyyymmdd="20260207",
                    execplans_dir=execplans_dir,
                    update_registry=False,
                )

            with self.assertRaisesRegex(ValueError, "reserved for ExecPlan directory layout roots"):
                create_execplan(
                    root=root,
                    title="Completed Root Collision",
                    slug="completed",
                    date_yyyymmdd="20260207",
                    execplans_dir=execplans_dir,
                    update_registry=False,
                )

    def test_create_execplan_rejects_reserved_milestones_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            with self.assertRaisesRegex(ValueError, "reserved for internal milestone namespace paths"):
                create_execplan(
                    root=root,
                    title="Milestones Namespace Collision",
                    slug="milestones",
                    date_yyyymmdd="20260207",
                    execplans_dir=execplans_dir,
                    update_registry=False,
                )

    def test_create_execplan_rejects_milestones_slug_in_mixed_legacy_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"
            legacy_root = execplans_dir / "active"
            legacy_root.mkdir(parents=True, exist_ok=True)
            (legacy_root / "EP-20260207-001_active.md").write_text(
                (
                    "---\n"
                    "id: EP-20260207-001\n"
                    'title: "Legacy Active Root"\n'
                    "status: planned\n"
                    "kind: feature\n"
                    "domain: backend\n"
                    'owner: "@codex"\n'
                    "created: 2026-02-07\n"
                    "updated: 2026-02-07\n"
                    "tags: []\n"
                    "touches: []\n"
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

            with self.assertRaisesRegex(ValueError, "reserved for internal milestone namespace paths"):
                create_execplan(
                    root=root,
                    title="Modern Milestones Slug",
                    slug="milestones",
                    date_yyyymmdd="20260208",
                    execplans_dir=execplans_dir,
                    update_registry=False,
                )

    def test_create_execplan_rejects_second_plan_for_existing_slug_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            first = create_execplan(
                root=root,
                title="First Auth Plan",
                slug="auth-refresh",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                update_registry=False,
            )
            self.assertTrue(first.plan_path.exists())

            with self.assertRaisesRegex(ValueError, "already contains an ExecPlan file"):
                create_execplan(
                    root=root,
                    title="Second Auth Plan",
                    slug="auth-refresh",
                    date_yyyymmdd="20260207",
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

    def test_archive_execplan_moves_active_directory_and_sets_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            created = create_execplan(
                root=root,
                title="Archive Candidate",
                slug="archive-candidate",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                update_registry=False,
            )

            source_root = execplans_dir / "active" / "archive-candidate"
            self.assertTrue(source_root.exists())

            archived = archive_execplan(
                root=root,
                execplan_id=created.plan_id,
                execplans_dir=execplans_dir,
                archive_date_yyyymmdd="20260212",
                update_registry=False,
            )

            self.assertFalse(source_root.exists())
            self.assertTrue(archived.archived_plan_root.exists())
            self.assertIn(
                "/complete/2026/02/12/EP-20260207-001_archive-candidate",
                archived.archived_plan_root.as_posix(),
            )
            content = archived.archived_plan_path.read_text(encoding="utf-8")
            self.assertIn("status: archived", content)
            self.assertRegex(content, r"updated:\s*'?2026-02-12'?")

    def test_archive_execplan_does_not_create_locks_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            created = create_execplan(
                root=root,
                title="Archive Lock Check",
                slug="archive-lock-check",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                update_registry=False,
            )

            archive_execplan(
                root=root,
                execplan_id=created.plan_id,
                execplans_dir=execplans_dir,
                archive_date_yyyymmdd="20260212",
                update_registry=False,
            )

            self.assertFalse((execplans_dir / ".locks").exists())

    def test_archive_execplan_rejects_non_utf8_active_milestone_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            created = create_execplan(
                root=root,
                title="Archive Non UTF8",
                slug="archive-non-utf8",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                update_registry=False,
            )

            non_utf8 = (
                execplans_dir
                / "active"
                / "archive-non-utf8"
                / "milestones"
                / "active"
                / "notes.md"
            )
            non_utf8.parent.mkdir(parents=True, exist_ok=True)
            non_utf8.write_bytes(b"\xff\xfe\xfa\xfb")

            with self.assertRaisesRegex(ValueError, "active milestone metadata is invalid") as error_context:
                archive_execplan(
                    root=root,
                    execplan_id=created.plan_id,
                    execplans_dir=execplans_dir,
                    archive_date_yyyymmdd="20260212",
                    update_registry=False,
                )

            self.assertIn("notes.md", str(error_context.exception))
            self.assertTrue((execplans_dir / "active" / "archive-non-utf8").exists())

    def test_archive_execplan_rejects_when_active_milestones_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            created = create_execplan(
                root=root,
                title="Archive Blocked By Milestones",
                slug="archive-blocked-by-milestones",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                update_registry=False,
            )

            active_milestone = (
                execplans_dir
                / "active"
                / "archive-blocked-by-milestones"
                / "milestones"
                / "active"
                / "MS001_blocking-milestone.md"
            )
            active_milestone.parent.mkdir(parents=True, exist_ok=True)
            active_milestone.write_text(
                (
                    "---\n"
                    f"id: {created.plan_id}/MS001\n"
                    f"execplan_id: {created.plan_id}\n"
                    'title: "Blocking Milestone"\n'
                    "status: active\n"
                    "domain: backend\n"
                    'owner: "@codex"\n'
                    "created: 2026-02-07\n"
                    "updated: 2026-02-07\n"
                    "---\n\n"
                    "# Blocking\n"
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "active milestones still exist") as error_context:
                archive_execplan(
                    root=root,
                    execplan_id=created.plan_id,
                    execplans_dir=execplans_dir,
                    archive_date_yyyymmdd="20260212",
                    update_registry=False,
                )

            self.assertIn("MS001_blocking-milestone.md", str(error_context.exception))
            self.assertTrue((execplans_dir / "active" / "archive-blocked-by-milestones").exists())
            self.assertFalse((execplans_dir / "complete" / "2026" / "02" / "12").exists())

    def test_archive_execplan_rejects_non_ms_filename_active_milestone(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            created = create_execplan(
                root=root,
                title="Archive Blocked By Non-MS Filename",
                slug="archive-blocked-by-non-ms-filename",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                update_registry=False,
            )

            non_canonical_milestone = (
                execplans_dir
                / "active"
                / "archive-blocked-by-non-ms-filename"
                / "milestones"
                / "active"
                / "blocking.md"
            )
            non_canonical_milestone.parent.mkdir(parents=True, exist_ok=True)
            non_canonical_milestone.write_text(
                (
                    "---\n"
                    f"id: {created.plan_id}/MS001\n"
                    f"execplan_id: {created.plan_id}\n"
                    'title: "Blocking Milestone"\n'
                    "status: active\n"
                    "domain: backend\n"
                    'owner: "@codex"\n'
                    "created: 2026-02-07\n"
                    "updated: 2026-02-07\n"
                    "---\n\n"
                    "# Blocking\n"
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "active milestones still exist") as error_context:
                archive_execplan(
                    root=root,
                    execplan_id=created.plan_id,
                    execplans_dir=execplans_dir,
                    archive_date_yyyymmdd="20260212",
                    update_registry=False,
                )

            self.assertIn("blocking.md", str(error_context.exception))
            self.assertTrue((execplans_dir / "active" / "archive-blocked-by-non-ms-filename").exists())
            self.assertFalse((execplans_dir / "complete" / "2026" / "02" / "12").exists())

    def test_archive_execplan_rejects_invalid_active_milestone_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            created = create_execplan(
                root=root,
                title="Archive Blocked By Invalid Active Milestone",
                slug="archive-blocked-by-invalid-active-milestone",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                update_registry=False,
            )

            malformed = (
                execplans_dir
                / "active"
                / "archive-blocked-by-invalid-active-milestone"
                / "milestones"
                / "active"
                / "MS001_broken.md"
            )
            malformed.parent.mkdir(parents=True, exist_ok=True)
            malformed.write_text(
                (
                    "---\n"
                    'title: "Broken Metadata"\n'
                    "---\n\n"
                    "# Broken\n"
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "active milestone metadata is invalid") as error_context:
                archive_execplan(
                    root=root,
                    execplan_id=created.plan_id,
                    execplans_dir=execplans_dir,
                    archive_date_yyyymmdd="20260212",
                    update_registry=False,
                )

            self.assertIn("MS001_broken.md", str(error_context.exception))
            self.assertTrue((execplans_dir / "active" / "archive-blocked-by-invalid-active-milestone").exists())
            self.assertFalse((execplans_dir / "complete" / "2026" / "02" / "12").exists())

    def test_archive_execplan_rejects_multi_execplan_plan_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"
            slug_dir = execplans_dir / "shared"
            slug_dir.mkdir(parents=True, exist_ok=True)

            first = slug_dir / "EP-20260207-001_shared.md"
            first.write_text(
                (
                    "---\n"
                    "id: EP-20260207-001\n"
                    'title: "First"\n'
                    "status: planned\n"
                    "kind: feature\n"
                    "domain: backend\n"
                    'owner: "@codex"\n'
                    "created: 2026-02-07\n"
                    "updated: 2026-02-07\n"
                    "tags: []\n"
                    "touches: []\n"
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
                    "# First\n"
                ),
                encoding="utf-8",
            )
            second = slug_dir / "EP-20260207-002_shared.md"
            second.write_text(
                first.read_text(encoding="utf-8").replace("EP-20260207-001", "EP-20260207-002"),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "multiple ExecPlan files"):
                archive_execplan(
                    root=root,
                    execplan_id="EP-20260207-001",
                    execplans_dir=execplans_dir,
                    archive_date_yyyymmdd="20260212",
                    update_registry=False,
                )

    def test_archive_execplan_allows_active_root_archive_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            source_root = execplans_dir / "active" / "archive"
            source_plan = source_root / "EP-20260207-001_archive.md"
            source_root.mkdir(parents=True, exist_ok=True)
            source_plan.write_text(
                (
                    "---\n"
                    "id: EP-20260207-001\n"
                    'title: "Active Root Archive Slug"\n'
                    "status: planned\n"
                    "kind: feature\n"
                    "domain: backend\n"
                    'owner: "@codex"\n'
                    "created: 2026-02-07\n"
                    "updated: 2026-02-07\n"
                    "tags: []\n"
                    "touches: []\n"
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
                    "# Archive\n"
                ),
                encoding="utf-8",
            )

            archived = archive_execplan(
                root=root,
                execplan_id="EP-20260207-001",
                execplans_dir=execplans_dir,
                archive_date_yyyymmdd="20260212",
                update_registry=False,
            )

            self.assertFalse(source_root.exists())
            self.assertTrue(archived.archived_plan_path.exists())
            self.assertIn("/complete/2026/02/12/EP-20260207-001_archive", archived.archived_plan_path.as_posix())

    def test_archive_execplan_allows_legacy_top_level_archive_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            source_root = execplans_dir / "archive"
            source_plan = source_root / "EP-20260207-001_archive.md"
            source_root.mkdir(parents=True, exist_ok=True)
            source_plan.write_text(
                (
                    "---\n"
                    "id: EP-20260207-001\n"
                    'title: "Legacy Archive Slug"\n'
                    "status: planned\n"
                    "kind: feature\n"
                    "domain: backend\n"
                    'owner: "@codex"\n'
                    "created: 2026-02-07\n"
                    "updated: 2026-02-07\n"
                    "tags: []\n"
                    "touches: []\n"
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
                    "# Archive\n"
                ),
                encoding="utf-8",
            )

            archived = archive_execplan(
                root=root,
                execplan_id="EP-20260207-001",
                execplans_dir=execplans_dir,
                archive_date_yyyymmdd="20260212",
                update_registry=False,
            )

            self.assertFalse(source_plan.exists())
            self.assertTrue(archived.archived_plan_path.exists())
            self.assertIn("/complete/2026/02/12/EP-20260207-001_archive", archived.archived_plan_path.as_posix())

    def test_archive_execplan_rejects_legacy_top_level_complete_slug_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            source_root = execplans_dir / "complete"
            source_plan = source_root / "EP-20260207-001_complete.md"
            source_root.mkdir(parents=True, exist_ok=True)
            source_plan.write_text(
                (
                    "---\n"
                    "id: EP-20260207-001\n"
                    'title: "Legacy Complete Slug"\n'
                    "status: planned\n"
                    "kind: feature\n"
                    "domain: backend\n"
                    'owner: "@codex"\n'
                    "created: 2026-02-07\n"
                    "updated: 2026-02-07\n"
                    "tags: []\n"
                    "touches: []\n"
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
                    "# Complete\n"
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "destination resolves inside the source plan root"):
                archive_execplan(
                    root=root,
                    execplan_id="EP-20260207-001",
                    execplans_dir=execplans_dir,
                    archive_date_yyyymmdd="20260212",
                    update_registry=False,
                )

            self.assertTrue(source_plan.exists())
            self.assertFalse((execplans_dir / "complete" / "2026" / "02" / "12").exists())

    def test_archive_execplan_allows_legacy_top_level_completed_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            source_root = execplans_dir / "completed"
            source_plan = source_root / "EP-20260207-001_completed.md"
            source_root.mkdir(parents=True, exist_ok=True)
            source_plan.write_text(
                (
                    "---\n"
                    "id: EP-20260207-001\n"
                    'title: "Legacy Completed Slug"\n'
                    "status: planned\n"
                    "kind: feature\n"
                    "domain: backend\n"
                    'owner: "@codex"\n'
                    "created: 2026-02-07\n"
                    "updated: 2026-02-07\n"
                    "tags: []\n"
                    "touches: []\n"
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
                    "# Completed\n"
                ),
                encoding="utf-8",
            )

            archived = archive_execplan(
                root=root,
                execplan_id="EP-20260207-001",
                execplans_dir=execplans_dir,
                archive_date_yyyymmdd="20260212",
                update_registry=False,
            )

            self.assertFalse(source_plan.exists())
            self.assertTrue(archived.archived_plan_path.exists())
            self.assertIn("/complete/2026/02/12/EP-20260207-001_completed", archived.archived_plan_path.as_posix())

    def test_archive_execplan_supports_legacy_active_slug_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            modern_plan = create_execplan(
                root=root,
                title="Modern Active Plan",
                slug="modern-active-plan",
                date_yyyymmdd="20260208",
                execplans_dir=execplans_dir,
                update_registry=False,
            )
            self.assertTrue(modern_plan.plan_path.exists())

            source_root = execplans_dir / "active"
            source_plan = source_root / "EP-20260207-001_active.md"
            source_root.mkdir(parents=True, exist_ok=True)
            source_plan.write_text(
                (
                    "---\n"
                    "id: EP-20260207-001\n"
                    'title: "Legacy Active Slug"\n'
                    "status: planned\n"
                    "kind: feature\n"
                    "domain: backend\n"
                    'owner: "@codex"\n'
                    "created: 2026-02-07\n"
                    "updated: 2026-02-07\n"
                    "tags: []\n"
                    "touches: []\n"
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
                    "# Active\n"
                ),
                encoding="utf-8",
            )
            source_legacy_milestone = (
                source_root / "milestones" / "archive" / "EP-20260207-001_MS001_legacy-active-smoke.md"
            )
            source_legacy_milestone.parent.mkdir(parents=True, exist_ok=True)
            source_legacy_milestone.write_text("# legacy milestone\n", encoding="utf-8")

            archived = archive_execplan(
                root=root,
                execplan_id="EP-20260207-001",
                execplans_dir=execplans_dir,
                archive_date_yyyymmdd="20260212",
                update_registry=False,
            )

            self.assertFalse(source_plan.exists())
            self.assertTrue(source_root.exists())
            self.assertTrue(modern_plan.plan_path.exists())
            self.assertTrue(archived.archived_plan_path.exists())
            self.assertIn("/complete/2026/02/12/EP-20260207-001_active", archived.archived_plan_path.as_posix())
            self.assertTrue((archived.archived_plan_root / "milestones" / "archive").exists())
            self.assertFalse((source_root / "milestones").exists())

    def test_archive_execplan_supports_legacy_active_root_with_complete_milestones(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            source_root = execplans_dir / "active"
            source_plan = source_root / "EP-20260207-001_active.md"
            source_root.mkdir(parents=True, exist_ok=True)
            source_plan.write_text(
                (
                    "---\n"
                    "id: EP-20260207-001\n"
                    'title: "Legacy Active Slug"\n'
                    "status: planned\n"
                    "kind: feature\n"
                    "domain: backend\n"
                    'owner: "@codex"\n'
                    "created: 2026-02-07\n"
                    "updated: 2026-02-07\n"
                    "tags: []\n"
                    "touches: []\n"
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
                    "# Active\n"
                ),
                encoding="utf-8",
            )
            source_completed_milestone = (
                source_root / "milestones" / "complete" / "EP-20260207-001_MS001_legacy-active-complete.md"
            )
            source_completed_milestone.parent.mkdir(parents=True, exist_ok=True)
            source_completed_milestone.write_text("# completed milestone\n", encoding="utf-8")

            archived = archive_execplan(
                root=root,
                execplan_id="EP-20260207-001",
                execplans_dir=execplans_dir,
                archive_date_yyyymmdd="20260212",
                update_registry=False,
            )

            self.assertFalse(source_plan.exists())
            self.assertTrue(archived.archived_plan_path.exists())
            self.assertTrue((archived.archived_plan_root / "milestones" / "complete").exists())
            self.assertFalse((source_root / "milestones").exists())

    def test_archive_execplan_allows_same_slug_archived_on_same_day(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            first = create_execplan(
                root=root,
                title="Shared Slug First",
                slug="shared-slug",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                update_registry=False,
            )
            first_archive = archive_execplan(
                root=root,
                execplan_id=first.plan_id,
                execplans_dir=execplans_dir,
                archive_date_yyyymmdd="20260212",
                update_registry=False,
            )
            self.assertTrue(first_archive.archived_plan_path.exists())

            second = create_execplan(
                root=root,
                title="Shared Slug Second",
                slug="shared-slug",
                date_yyyymmdd="20260208",
                execplans_dir=execplans_dir,
                update_registry=False,
            )
            second_archive = archive_execplan(
                root=root,
                execplan_id=second.plan_id,
                execplans_dir=execplans_dir,
                archive_date_yyyymmdd="20260212",
                update_registry=False,
            )
            self.assertTrue(second_archive.archived_plan_path.exists())
            self.assertNotEqual(first_archive.archived_plan_root, second_archive.archived_plan_root)

    def test_archive_execplan_rejects_foreign_milestones_in_modern_plan_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            legacy_root = execplans_dir / "active"
            legacy_plan = legacy_root / "EP-20260207-001_active.md"
            legacy_root.mkdir(parents=True, exist_ok=True)
            legacy_plan.write_text(
                (
                    "---\n"
                    "id: EP-20260207-001\n"
                    'title: "Legacy Active Root"\n'
                    "status: planned\n"
                    "kind: feature\n"
                    "domain: backend\n"
                    'owner: "@codex"\n'
                    "created: 2026-02-07\n"
                    "updated: 2026-02-07\n"
                    "tags: []\n"
                    "touches: []\n"
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
            legacy_milestone = (
                legacy_root / "milestones" / "active" / "EP-20260207-001_MS001_legacy-active-shared.md"
            )
            legacy_milestone.parent.mkdir(parents=True, exist_ok=True)
            legacy_milestone.write_text("# legacy milestone\n", encoding="utf-8")

            modern = execplans_dir / "active" / "milestones" / "EP-20260208-001_milestones.md"
            modern.parent.mkdir(parents=True, exist_ok=True)
            modern.write_text(
                (
                    "---\n"
                    "id: EP-20260208-001\n"
                    'title: "Modern Milestones Slug"\n'
                    "status: planned\n"
                    "kind: feature\n"
                    "domain: backend\n"
                    'owner: "@codex"\n'
                    "created: 2026-02-08\n"
                    "updated: 2026-02-08\n"
                    "tags: []\n"
                    "touches: []\n"
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
                    "# Modern\n"
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "contains milestone files for other ExecPlan IDs"):
                archive_execplan(
                    root=root,
                    execplan_id="EP-20260208-001",
                    execplans_dir=execplans_dir,
                    archive_date_yyyymmdd="20260212",
                    update_registry=False,
                )

            self.assertTrue(modern.exists())
            self.assertTrue(legacy_milestone.exists())
            self.assertFalse((execplans_dir / "complete" / "2026" / "02" / "12" / "EP-20260208-001_milestones").exists())

    def test_archive_execplan_rejects_foreign_completed_milestones_in_modern_plan_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            modern = create_execplan(
                root=root,
                title="Modern Plan",
                slug="modern-plan",
                date_yyyymmdd="20260208",
                execplans_dir=execplans_dir,
                update_registry=False,
            )
            foreign_milestone = (
                modern.plan_path.parent / "milestones" / "complete" / "EP-20260207-001_MS001_foreign.md"
            )
            foreign_milestone.parent.mkdir(parents=True, exist_ok=True)
            foreign_milestone.write_text(
                (
                    "---\n"
                    "milestone_id: EP-20260207-001/MS001\n"
                    "execplan_id: EP-20260207-001\n"
                    'title: "Foreign milestone"\n'
                    "status: completed\n"
                    "domain: backend\n"
                    'owner: "@codex"\n'
                    "created: 2026-02-07\n"
                    "updated: 2026-02-12\n"
                    "---\n\n"
                    "# Foreign\n"
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "contains milestone files for other ExecPlan IDs"):
                archive_execplan(
                    root=root,
                    execplan_id=modern.plan_id,
                    execplans_dir=execplans_dir,
                    archive_date_yyyymmdd="20260212",
                    update_registry=False,
                )

            self.assertTrue(modern.plan_path.exists())
            self.assertTrue(foreign_milestone.exists())
            self.assertFalse((execplans_dir / "complete" / "2026" / "02" / "12" / "EP-20260208-001_modern-plan").exists())

    def test_archive_legacy_active_root_rejects_mixed_namespace_collision(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            legacy_root = execplans_dir / "active"
            legacy_plan = legacy_root / "EP-20260207-001_active.md"
            legacy_root.mkdir(parents=True, exist_ok=True)
            legacy_plan.write_text(
                (
                    "---\n"
                    "id: EP-20260207-001\n"
                    'title: "Legacy Active Root"\n'
                    "status: planned\n"
                    "kind: feature\n"
                    "domain: backend\n"
                    'owner: "@codex"\n'
                    "created: 2026-02-07\n"
                    "updated: 2026-02-07\n"
                    "tags: []\n"
                    "touches: []\n"
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

            modern = execplans_dir / "active" / "milestones" / "EP-20260208-001_milestones.md"
            modern.parent.mkdir(parents=True, exist_ok=True)
            modern.write_text(
                (
                    "---\n"
                    "id: EP-20260208-001\n"
                    'title: "Modern Milestones Slug"\n'
                    "status: planned\n"
                    "kind: feature\n"
                    "domain: backend\n"
                    'owner: "@codex"\n'
                    "created: 2026-02-08\n"
                    "updated: 2026-02-08\n"
                    "tags: []\n"
                    "touches: []\n"
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
                    "# Modern\n"
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "mixed ownership artifacts were found"):
                archive_execplan(
                    root=root,
                    execplan_id="EP-20260207-001",
                    execplans_dir=execplans_dir,
                    archive_date_yyyymmdd="20260212",
                    update_registry=False,
                )

            self.assertTrue(legacy_plan.exists())
            self.assertTrue(modern.exists())
            self.assertFalse((execplans_dir / "complete" / "2026" / "02" / "12" / "EP-20260207-001_active").exists())


if __name__ == "__main__":
    unittest.main()
