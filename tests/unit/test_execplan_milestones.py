import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agentrules.core.execplan import milestones as milestone_module
from agentrules.core.execplan.creator import create_execplan
from agentrules.core.execplan.milestones import (
    archive_execplan_milestone,
    create_execplan_milestone,
    list_execplan_milestones,
)


def _write_execplan(path: Path, *, plan_id: str, title: str, domain: str = "backend", owner: str = "@codex") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            "---\n"
            f"id: {plan_id}\n"
            f'title: "{title}"\n'
            "status: planned\n"
            "kind: feature\n"
            f"domain: {domain}\n"
            f'owner: "{owner}"\n'
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
            "# Example\n"
        ),
        encoding="utf-8",
    )


class ExecPlanMilestonesTests(unittest.TestCase):
    def test_plan_milestone_lock_uses_windows_fallback_when_fcntl_missing(self) -> None:
        class FakeMsvcrt:
            LK_NBLCK = 1
            LK_UNLCK = 2

            def __init__(self) -> None:
                self.modes: list[int] = []

            def locking(self, _fd: int, mode: int, _nbytes: int) -> None:
                self.modes.append(mode)

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_root = Path(tmpdir) / ".agent" / "exec_plans" / "demo"
            fake_msvcrt = FakeMsvcrt()

            with (
                mock.patch.object(milestone_module, "fcntl", None),
                mock.patch.object(milestone_module, "msvcrt", fake_msvcrt),
                mock.patch.object(milestone_module, "_WINDOWS_LOCK_RETRY_DELAY_SECONDS", 0),
            ):
                with milestone_module._plan_milestone_lock(plan_root):
                    self.assertTrue((plan_root / "milestones" / ".milestones.lock").exists())

        self.assertEqual(fake_msvcrt.modes, [FakeMsvcrt.LK_NBLCK, FakeMsvcrt.LK_UNLCK])

    def test_plan_milestone_lock_fails_when_no_backend_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_root = Path(tmpdir) / ".agent" / "exec_plans" / "demo"
            with (
                mock.patch.object(milestone_module, "fcntl", None),
                mock.patch.object(milestone_module, "msvcrt", None),
            ):
                with self.assertRaisesRegex(RuntimeError, "No supported file-locking backend"):
                    with milestone_module._plan_milestone_lock(plan_root):
                        self.fail("Lock context should not succeed without a backend.")

    def test_create_milestone_uses_parent_and_title_codification(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"
            created_plan = create_execplan(
                root=root,
                title="Auth Refresh",
                slug="auth-refresh",
                owner="@backend-team",
                domain="frontend",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                update_registry=False,
            )

            created_milestone = create_execplan_milestone(
                root=root,
                execplan_id=created_plan.plan_id,
                title="Implement OAuth callback flow",
                execplans_dir=execplans_dir,
            )

            self.assertEqual(created_milestone.milestone_id, "EP-20260207-001/MS001")
            self.assertEqual(
                created_milestone.milestone_path.name,
                "EP-20260207-001_MS001_implement-oauth-callback-flow.md",
            )
            content = created_milestone.milestone_path.read_text(encoding="utf-8")
            self.assertIn("execplan_id: EP-20260207-001", content)
            self.assertIn('title: "Implement OAuth callback flow"', content)
            self.assertIn("domain: frontend", content)
            self.assertIn('owner: "@backend-team"', content)

    def test_create_milestone_respects_owner_and_domain_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"
            created_plan = create_execplan(
                root=root,
                title="Platform Upgrade",
                slug="platform-upgrade",
                owner="@platform",
                domain="infra",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                update_registry=False,
            )

            created_milestone = create_execplan_milestone(
                root=root,
                execplan_id=created_plan.plan_id,
                title="Dry run in staging",
                owner="@release-team",
                domain="backend",
                execplans_dir=execplans_dir,
            )

            content = created_milestone.milestone_path.read_text(encoding="utf-8")
            self.assertIn("domain: backend", content)
            self.assertIn('owner: "@release-team"', content)

    def test_create_milestone_sequence_stays_monotonic_after_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"
            created_plan = create_execplan(
                root=root,
                title="Search rewrite",
                slug="search-rewrite",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                update_registry=False,
            )

            first = create_execplan_milestone(
                root=root,
                execplan_id=created_plan.plan_id,
                title="Prototype indexing",
                execplans_dir=execplans_dir,
            )
            archive_execplan_milestone(
                root=root,
                execplan_id=created_plan.plan_id,
                sequence=first.sequence,
                execplans_dir=execplans_dir,
                archive_date_yyyymmdd="20260211",
            )

            second = create_execplan_milestone(
                root=root,
                execplan_id=created_plan.plan_id,
                title="Production cutover",
                execplans_dir=execplans_dir,
            )

            self.assertEqual(second.milestone_id, "EP-20260207-001/MS002")

    def test_create_milestone_rejects_duplicate_parent_execplan_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"
            _write_execplan(
                execplans_dir / "a" / "EP-20260207-001_a.md",
                plan_id="EP-20260207-001",
                title="Plan A",
            )
            _write_execplan(
                execplans_dir / "b" / "EP-20260207-001_b.md",
                plan_id="EP-20260207-001",
                title="Plan B",
            )

            with self.assertRaisesRegex(ValueError, "multiple files"):
                create_execplan_milestone(
                    root=root,
                    execplan_id="EP-20260207-001",
                    title="Cannot resolve parent",
                    execplans_dir=execplans_dir,
                )

    def test_archive_moves_active_milestone_to_dated_archive_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"
            created_plan = create_execplan(
                root=root,
                title="Telemetry cleanup",
                slug="telemetry-cleanup",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                update_registry=False,
            )
            created_milestone = create_execplan_milestone(
                root=root,
                execplan_id=created_plan.plan_id,
                title="Remove dead metrics",
                execplans_dir=execplans_dir,
            )

            archived = archive_execplan_milestone(
                root=root,
                execplan_id=created_plan.plan_id,
                sequence=1,
                execplans_dir=execplans_dir,
                archive_date_yyyymmdd="20260212",
            )

            self.assertFalse(created_milestone.milestone_path.exists())
            self.assertTrue(archived.archived_path.exists())
            self.assertIn("/milestones/archive/2026/02/12/", archived.archived_path.as_posix())

    def test_archive_missing_active_milestone_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"
            created_plan = create_execplan(
                root=root,
                title="Auth hardening",
                slug="auth-hardening",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                update_registry=False,
            )

            with self.assertRaisesRegex(FileNotFoundError, "was not found"):
                archive_execplan_milestone(
                    root=root,
                    execplan_id=created_plan.plan_id,
                    sequence=1,
                    execplans_dir=execplans_dir,
                )

    def test_list_milestones_returns_active_and_archived(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"
            created_plan = create_execplan(
                root=root,
                title="Cache rollout",
                slug="cache-rollout",
                date_yyyymmdd="20260207",
                execplans_dir=execplans_dir,
                update_registry=False,
            )
            first = create_execplan_milestone(
                root=root,
                execplan_id=created_plan.plan_id,
                title="Benchmark baseline",
                execplans_dir=execplans_dir,
            )
            archive_execplan_milestone(
                root=root,
                execplan_id=created_plan.plan_id,
                sequence=first.sequence,
                execplans_dir=execplans_dir,
                archive_date_yyyymmdd="20260212",
            )
            second = create_execplan_milestone(
                root=root,
                execplan_id=created_plan.plan_id,
                title="Enable rollout flag",
                execplans_dir=execplans_dir,
            )

            all_entries = list_execplan_milestones(
                root=root,
                execplan_id=created_plan.plan_id,
                execplans_dir=execplans_dir,
                include_archived=True,
            )
            active_only = list_execplan_milestones(
                root=root,
                execplan_id=created_plan.plan_id,
                execplans_dir=execplans_dir,
                include_archived=False,
            )

            self.assertEqual([entry.milestone_id for entry in all_entries], [first.milestone_id, second.milestone_id])
            self.assertEqual([entry.location for entry in all_entries], ["archived", "active"])
            self.assertEqual([entry.milestone_id for entry in active_only], [second.milestone_id])


if __name__ == "__main__":
    unittest.main()
