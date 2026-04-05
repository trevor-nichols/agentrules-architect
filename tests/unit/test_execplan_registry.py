import json
import os
import tempfile
import unittest
from pathlib import Path

from agentrules.core.execplan.registry import (
    build_execplan_registry,
    collect_execplan_registry,
    list_active_execplan_summaries,
    summarize_registry_activity,
)


def _write_execplan(
    path: Path,
    *,
    plan_id: str,
    title: str,
    depends_on: str = "[]",
    status: str = "planned",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            "---\n"
            f"id: {plan_id}\n"
            f'title: "{title}"\n'
            f"status: {status}\n"
            "kind: feature\n"
            "domain: backend\n"
            'owner: "@codex"\n'
            "created: 2026-02-07\n"
            "updated: 2026-02-07\n"
            "tags: [execplan]\n"
            "touches: [cli]\n"
            "risk: low\n"
            "breaking: false\n"
            "migration: false\n"
            "links:\n"
            '  issue: ""\n'
            '  pr: ""\n'
            '  docs: ""\n'
            f"depends_on: {depends_on}\n"
            "supersedes: []\n"
            "---\n\n"
            "# Example\n"
        ),
        encoding="utf-8",
    )


def _write_execplan_block_lists(
    path: Path,
    *,
    plan_id: str,
    title: str,
    depends_on_ids: tuple[str, ...] = (),
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if depends_on_ids:
        depends_on_section = "depends_on:\n" + "\n".join(f"  - {plan_ref}" for plan_ref in depends_on_ids) + "\n"
    else:
        depends_on_section = "depends_on: []\n"
    path.write_text(
        (
            "---\n"
            f"id: {plan_id}\n"
            f'title: "{title}"\n'
            "status: planned\n"
            "kind: feature\n"
            "domain: backend\n"
            'owner: "@codex"\n'
            "created: 2026-02-07\n"
            "updated: 2026-02-07\n"
            "tags:\n"
            "  - execplan\n"
            "  - auth\n"
            "touches:\n"
            "  - cli\n"
            "risk: low\n"
            "breaking: false\n"
            "migration: false\n"
            "links:\n"
            '  issue: ""\n'
            '  pr: ""\n'
            '  docs: ""\n'
            f"{depends_on_section}"
            "supersedes: []\n"
            "---\n\n"
            "# Example\n"
        ),
        encoding="utf-8",
    )


def _write_milestone(path: Path, *, milestone_id: str, execplan_id: str, title: str = "Milestone") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            "---\n"
            f"id: {milestone_id}\n"
            f"execplan_id: {execplan_id}\n"
            f'title: "{title}"\n'
            "status: planned\n"
            'owner: "@codex"\n'
            "domain: backend\n"
            "created: 2026-02-07\n"
            "updated: 2026-02-07\n"
            "---\n\n"
            "# Milestone\n"
        ),
        encoding="utf-8",
    )


class ExecPlanRegistryTests(unittest.TestCase):
    def test_list_active_execplan_summaries_returns_per_plan_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            _write_execplan(
                execplans_dir / "active" / "checkout" / "EP-20260207-001_checkout.md",
                plan_id="EP-20260207-001",
                title="Checkout",
                status="active",
            )
            _write_execplan(
                execplans_dir / "active" / "search" / "EP-20260207-002_search.md",
                plan_id="EP-20260207-002",
                title="Search",
                status="planned",
            )
            _write_execplan(
                execplans_dir
                / "complete"
                / "2026"
                / "02"
                / "12"
                / "EP-20260207-003_legacy-cleanup"
                / "EP-20260207-003_legacy-cleanup.md",
                plan_id="EP-20260207-003",
                title="Legacy Cleanup",
                status="done",
            )

            _write_milestone(
                execplans_dir
                / "active"
                / "checkout"
                / "milestones"
                / "active"
                / "MS001_wire-checkout-api.md",
                milestone_id="EP-20260207-001/MS001",
                execplan_id="EP-20260207-001",
            )
            _write_milestone(
                execplans_dir
                / "active"
                / "checkout"
                / "milestones"
                / "complete"
                / "MS002_add-coupon-validation.md",
                milestone_id="EP-20260207-001/MS002",
                execplan_id="EP-20260207-001",
            )
            _write_milestone(
                execplans_dir
                / "complete"
                / "2026"
                / "02"
                / "12"
                / "EP-20260207-003_legacy-cleanup"
                / "milestones"
                / "active"
                / "MS001_deprecate-v1-endpoint.md",
                milestone_id="EP-20260207-003/MS001",
                execplan_id="EP-20260207-003",
            )

            collected = collect_execplan_registry(root=root, execplans_dir=execplans_dir)
            summaries = list_active_execplan_summaries(
                registry=collected.registry,
                root=root,
                execplans_dir=execplans_dir,
            )

            self.assertEqual([summary.id for summary in summaries], ["EP-20260207-001", "EP-20260207-002"])
            self.assertEqual([summary.title for summary in summaries], ["Checkout", "Search"])
            self.assertEqual(
                [(summary.active_milestones, summary.total_milestones) for summary in summaries],
                [(1, 2), (0, 0)],
            )

    def test_list_active_execplan_summaries_ignores_mismatched_milestone_id_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            _write_execplan(
                execplans_dir / "active" / "checkout" / "EP-20260207-001_checkout.md",
                plan_id="EP-20260207-001",
                title="Checkout",
                status="active",
            )
            _write_milestone(
                execplans_dir
                / "active"
                / "checkout"
                / "milestones"
                / "active"
                / "MS001_mismatched-id-prefix.md",
                milestone_id="EP-20260207-002/MS001",
                execplan_id="EP-20260207-001",
            )

            collected = collect_execplan_registry(root=root, execplans_dir=execplans_dir)
            summaries = list_active_execplan_summaries(
                registry=collected.registry,
                root=root,
                execplans_dir=execplans_dir,
            )

            self.assertEqual(len(summaries), 1)
            self.assertEqual(summaries[0].id, "EP-20260207-001")
            self.assertEqual((summaries[0].active_milestones, summaries[0].total_milestones), (0, 0))

    def test_summarize_counts_active_plans_and_active_over_total_milestones(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            _write_execplan(
                execplans_dir / "active" / "checkout" / "EP-20260207-001_checkout.md",
                plan_id="EP-20260207-001",
                title="Checkout",
                status="active",
            )
            _write_execplan(
                execplans_dir
                / "complete"
                / "2026"
                / "02"
                / "12"
                / "EP-20260207-002_legacy-cleanup"
                / "EP-20260207-002_legacy-cleanup.md",
                plan_id="EP-20260207-002",
                title="Legacy Cleanup",
                status="done",
            )

            _write_milestone(
                execplans_dir
                / "active"
                / "checkout"
                / "milestones"
                / "active"
                / "MS001_wire-checkout-api.md",
                milestone_id="EP-20260207-001/MS001",
                execplan_id="EP-20260207-001",
            )
            _write_milestone(
                execplans_dir
                / "active"
                / "checkout"
                / "milestones"
                / "complete"
                / "MS002_add-coupon-validation.md",
                milestone_id="EP-20260207-001/MS002",
                execplan_id="EP-20260207-001",
            )
            _write_milestone(
                execplans_dir
                / "complete"
                / "2026"
                / "02"
                / "12"
                / "EP-20260207-002_legacy-cleanup"
                / "milestones"
                / "active"
                / "MS001_deprecate-v1-endpoint.md",
                milestone_id="EP-20260207-002/MS001",
                execplan_id="EP-20260207-002",
            )

            collected = collect_execplan_registry(root=root, execplans_dir=execplans_dir)
            summary = summarize_registry_activity(
                registry=collected.registry,
                root=root,
                execplans_dir=execplans_dir,
            )

            self.assertEqual(summary.active_execplans, 1)
            self.assertEqual(summary.active_milestones, 1)
            self.assertEqual(summary.total_milestones, 2)

    def test_build_writes_sorted_registry_and_excludes_milestones(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"
            registry_path = execplans_dir / "registry.json"

            _write_execplan(
                execplans_dir / "auth" / "EP-20260207-002_auth.md",
                plan_id="EP-20260207-002",
                title="Auth Plan",
            )
            _write_execplan(
                execplans_dir / "billing" / "EP-20260207-001_billing.md",
                plan_id="EP-20260207-001",
                title="Billing Plan",
            )
            _write_execplan(
                execplans_dir / "auth" / "milestones" / "active" / "EP-20260207-002_MS001_probe.md",
                plan_id="EP-20260207-002",
                title="Milestone should be ignored",
            )

            result = build_execplan_registry(
                root=root,
                execplans_dir=execplans_dir,
                output_path=registry_path,
            )

            self.assertTrue(result.wrote_registry)
            self.assertEqual(result.error_count, 0)
            self.assertEqual(result.warning_count, 0)
            self.assertTrue(registry_path.exists())

            payload = json.loads(registry_path.read_text(encoding="utf-8"))
            ids = [entry["id"] for entry in payload["plans"]]
            self.assertEqual(ids, ["EP-20260207-001", "EP-20260207-002"])
            self.assertTrue(all("milestones" not in entry["path"] for entry in payload["plans"]))

    def test_collect_reports_duplicate_execplan_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"
            registry_path = execplans_dir / "registry.json"

            _write_execplan(
                execplans_dir / "a" / "EP-20260207-010_a.md",
                plan_id="EP-20260207-010",
                title="Plan A",
            )
            _write_execplan(
                execplans_dir / "b" / "EP-20260207-010_b.md",
                plan_id="EP-20260207-010",
                title="Plan B",
            )

            check = collect_execplan_registry(root=root, execplans_dir=execplans_dir)
            self.assertGreater(check.error_count, 0)
            self.assertTrue(any("Duplicate ExecPlan id" in issue.message for issue in check.issues))

            build = build_execplan_registry(
                root=root,
                execplans_dir=execplans_dir,
                output_path=registry_path,
            )
            self.assertFalse(build.wrote_registry)
            self.assertFalse(registry_path.exists())

    def test_collect_rejects_front_matter_id_filename_id_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"
            registry_path = execplans_dir / "registry.json"

            _write_execplan(
                execplans_dir / "mismatch" / "EP-20260207-001_mismatch.md",
                plan_id="EP-20260207-999",
                title="Mismatch Plan",
            )

            result = collect_execplan_registry(root=root, execplans_dir=execplans_dir)
            self.assertGreater(result.error_count, 0)
            self.assertTrue(any("must match filename id" in issue.message for issue in result.issues))

            build = build_execplan_registry(
                root=root,
                execplans_dir=execplans_dir,
                output_path=registry_path,
            )
            self.assertFalse(build.wrote_registry)
            self.assertFalse(registry_path.exists())

    def test_collect_accepts_id_only_md_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            _write_execplan(
                execplans_dir / "plain" / "EP-20260207-001.md",
                plan_id="EP-20260207-001",
                title="Plain Filename Plan",
            )

            result = collect_execplan_registry(root=root, execplans_dir=execplans_dir)
            self.assertEqual(result.error_count, 0)
            self.assertEqual(len(result.registry["plans"]), 1)
            self.assertEqual(result.registry["plans"][0]["id"], "EP-20260207-001")

    def test_collect_accepts_block_style_yaml_lists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            _write_execplan(
                execplans_dir / "base" / "EP-20260207-001_base.md",
                plan_id="EP-20260207-001",
                title="Base Plan",
            )
            _write_execplan_block_lists(
                execplans_dir / "feature" / "EP-20260207-002_feature.md",
                plan_id="EP-20260207-002",
                title="Feature Plan",
                depends_on_ids=("EP-20260207-001",),
            )

            result = collect_execplan_registry(root=root, execplans_dir=execplans_dir)
            self.assertEqual(result.error_count, 0)
            self.assertEqual(result.warning_count, 0)

            by_id = {plan["id"]: plan for plan in result.registry["plans"]}
            self.assertEqual(by_id["EP-20260207-002"]["tags"], ["execplan", "auth"])
            self.assertEqual(by_id["EP-20260207-002"]["touches"], ["cli"])
            self.assertEqual(by_id["EP-20260207-002"]["depends_on"], ["EP-20260207-001"])

    def test_collect_reports_unknown_dependency_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            _write_execplan(
                execplans_dir / "docs" / "EP-20260207-020_docs.md",
                plan_id="EP-20260207-020",
                title="Docs Plan",
                depends_on="[EP-20260207-999]",
            )

            result = collect_execplan_registry(root=root, execplans_dir=execplans_dir)
            self.assertGreater(result.error_count, 0)
            self.assertTrue(any("Unknown depends_on id" in issue.message for issue in result.issues))

    def test_collect_supports_execplans_outside_root(self) -> None:
        with tempfile.TemporaryDirectory() as root_tmp, tempfile.TemporaryDirectory() as execplans_tmp:
            root = Path(root_tmp)
            execplans_dir = Path(execplans_tmp)

            _write_execplan(
                execplans_dir / "api" / "EP-20260207-001_api.md",
                plan_id="EP-20260207-001",
                title="API Plan",
            )

            result = collect_execplan_registry(root=root, execplans_dir=execplans_dir)
            self.assertEqual(result.error_count, 0)
            self.assertEqual(len(result.registry["plans"]), 1)
            self.assertEqual(result.registry["plans"][0]["path"], (execplans_dir / "api" / "EP-20260207-001_api.md").resolve().as_posix())

    def test_collect_resolves_default_execplans_dir_from_root(self) -> None:
        with tempfile.TemporaryDirectory() as root_tmp, tempfile.TemporaryDirectory() as cwd_tmp:
            root = Path(root_tmp).resolve()
            cwd = Path(cwd_tmp).resolve()
            execplans_dir = root / ".agent" / "exec_plans"

            _write_execplan(
                execplans_dir / "rooted" / "EP-20260207-001_rooted.md",
                plan_id="EP-20260207-001",
                title="Rooted Plan",
            )

            original_cwd = Path.cwd()
            try:
                os.chdir(cwd)
                result = collect_execplan_registry(root=root)
            finally:
                os.chdir(original_cwd)

            self.assertEqual(result.error_count, 0)
            self.assertEqual(len(result.registry["plans"]), 1)
            self.assertEqual(result.registry["plans"][0]["id"], "EP-20260207-001")

    def test_build_resolves_default_output_path_from_root(self) -> None:
        with tempfile.TemporaryDirectory() as root_tmp, tempfile.TemporaryDirectory() as cwd_tmp:
            root = Path(root_tmp).resolve()
            cwd = Path(cwd_tmp).resolve()
            execplans_dir = root / ".agent" / "exec_plans"

            _write_execplan(
                execplans_dir / "rooted" / "EP-20260207-001_rooted.md",
                plan_id="EP-20260207-001",
                title="Rooted Plan",
            )

            original_cwd = Path.cwd()
            try:
                os.chdir(cwd)
                result = build_execplan_registry(root=root, execplans_dir=execplans_dir)
            finally:
                os.chdir(original_cwd)

            self.assertTrue(result.wrote_registry)
            self.assertEqual(result.output_path, (root / ".agent" / "exec_plans" / "registry.json").resolve())
            self.assertTrue((root / ".agent" / "exec_plans" / "registry.json").exists())
            self.assertFalse((cwd / ".agent" / "exec_plans" / "registry.json").exists())

    def test_collect_includes_execplans_under_slug_named_milestones(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            _write_execplan(
                execplans_dir / "milestones" / "EP-20260207-001_milestones.md",
                plan_id="EP-20260207-001",
                title="Milestones Plan",
            )
            _write_execplan(
                execplans_dir / "normal" / "EP-20260207-002_normal.md",
                plan_id="EP-20260207-002",
                title="Normal Plan",
                depends_on="[EP-20260207-001]",
            )

            result = collect_execplan_registry(root=root, execplans_dir=execplans_dir)
            self.assertEqual(result.error_count, 0)
            ids = [entry["id"] for entry in result.registry["plans"]]
            self.assertEqual(ids, ["EP-20260207-001", "EP-20260207-002"])
            self.assertTrue(any("milestones/EP-20260207-001_milestones.md" in entry["path"] for entry in result.registry["plans"]))

    def test_collect_does_not_treat_slug_named_archive_as_archived_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"
            registry_path = execplans_dir / "registry.json"

            _write_execplan(
                execplans_dir / "archive" / "EP-20260207-001_archive.md",
                plan_id="EP-20260207-001",
                title="Archive Slug Plan",
            )

            result = collect_execplan_registry(root=root, execplans_dir=execplans_dir)
            warning_messages = [issue.message for issue in result.issues if issue.severity == "warning"]
            self.assertFalse(any("under a complete path" in message for message in warning_messages))

            build = build_execplan_registry(
                root=root,
                execplans_dir=execplans_dir,
                output_path=registry_path,
                fail_on_warn=True,
            )
            self.assertTrue(build.wrote_registry)
            self.assertEqual(build.warning_count, 0)

    def test_collect_does_not_treat_slug_named_complete_as_archived_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"
            registry_path = execplans_dir / "registry.json"

            _write_execplan(
                execplans_dir / "complete" / "EP-20260207-001_complete.md",
                plan_id="EP-20260207-001",
                title="Complete Slug Plan",
            )

            result = collect_execplan_registry(root=root, execplans_dir=execplans_dir)
            warning_messages = [issue.message for issue in result.issues if issue.severity == "warning"]
            self.assertFalse(any("under a complete path" in message for message in warning_messages))

            build = build_execplan_registry(
                root=root,
                execplans_dir=execplans_dir,
                output_path=registry_path,
                fail_on_warn=True,
            )
            self.assertTrue(build.wrote_registry)
            self.assertEqual(build.warning_count, 0)

    def test_collect_does_not_treat_slug_named_completed_as_archived_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"
            registry_path = execplans_dir / "registry.json"

            _write_execplan(
                execplans_dir / "completed" / "EP-20260207-001_completed.md",
                plan_id="EP-20260207-001",
                title="Completed Slug Plan",
            )

            result = collect_execplan_registry(root=root, execplans_dir=execplans_dir)
            warning_messages = [issue.message for issue in result.issues if issue.severity == "warning"]
            self.assertFalse(any("under a complete path" in message for message in warning_messages))

            build = build_execplan_registry(
                root=root,
                execplans_dir=execplans_dir,
                output_path=registry_path,
                fail_on_warn=True,
            )
            self.assertTrue(build.wrote_registry)
            self.assertEqual(build.warning_count, 0)

    def test_collect_does_not_treat_active_root_archive_slug_as_archived_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"
            registry_path = execplans_dir / "registry.json"

            _write_execplan(
                execplans_dir / "active" / "archive" / "EP-20260207-001_archive.md",
                plan_id="EP-20260207-001",
                title="Archive Slug Plan Under Active Root",
            )

            result = collect_execplan_registry(root=root, execplans_dir=execplans_dir)
            warning_messages = [issue.message for issue in result.issues if issue.severity == "warning"]
            self.assertFalse(any("under a complete path" in message for message in warning_messages))

            build = build_execplan_registry(
                root=root,
                execplans_dir=execplans_dir,
                output_path=registry_path,
                fail_on_warn=True,
            )
            self.assertTrue(build.wrote_registry)
            self.assertEqual(build.warning_count, 0)

    def test_collect_does_not_treat_active_root_complete_slug_as_archived_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"
            registry_path = execplans_dir / "registry.json"

            _write_execplan(
                execplans_dir / "active" / "complete" / "EP-20260207-001_complete.md",
                plan_id="EP-20260207-001",
                title="Complete Slug Plan Under Active Root",
            )

            result = collect_execplan_registry(root=root, execplans_dir=execplans_dir)
            warning_messages = [issue.message for issue in result.issues if issue.severity == "warning"]
            self.assertFalse(any("under a complete path" in message for message in warning_messages))

            build = build_execplan_registry(
                root=root,
                execplans_dir=execplans_dir,
                output_path=registry_path,
                fail_on_warn=True,
            )
            self.assertTrue(build.wrote_registry)
            self.assertEqual(build.warning_count, 0)

    def test_collect_does_not_treat_active_root_completed_slug_as_archived_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"
            registry_path = execplans_dir / "registry.json"

            _write_execplan(
                execplans_dir / "active" / "completed" / "EP-20260207-001_completed.md",
                plan_id="EP-20260207-001",
                title="Completed Slug Plan Under Active Root",
            )

            result = collect_execplan_registry(root=root, execplans_dir=execplans_dir)
            warning_messages = [issue.message for issue in result.issues if issue.severity == "warning"]
            self.assertFalse(any("under a complete path" in message for message in warning_messages))

            build = build_execplan_registry(
                root=root,
                execplans_dir=execplans_dir,
                output_path=registry_path,
                fail_on_warn=True,
            )
            self.assertTrue(build.wrote_registry)
            self.assertEqual(build.warning_count, 0)

    def test_collect_includes_legacy_archived_plan_under_milestones_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"

            _write_execplan(
                execplans_dir / "milestones" / "archive" / "EP-20260207-001_milestones.md",
                plan_id="EP-20260207-001",
                title="Milestones Slug Legacy Archive",
                status="archived",
            )

            result = collect_execplan_registry(root=root, execplans_dir=execplans_dir)
            self.assertEqual(result.error_count, 0)
            self.assertEqual(len(result.registry["plans"]), 1)
            self.assertEqual(result.registry["plans"][0]["id"], "EP-20260207-001")
            self.assertEqual(result.registry["plans"][0]["status"], "archived")

    def test_collect_allows_done_status_under_archive_path_without_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"
            registry_path = execplans_dir / "registry.json"

            _write_execplan(
                execplans_dir / "archive" / "2026" / "02" / "14" / "EP-20260214-003_agent-home-workspace" / "EP-20260214-003_agent-home-workspace.md",
                plan_id="EP-20260214-003",
                title="Agent Home Workspace",
                status="done",
            )

            result = collect_execplan_registry(root=root, execplans_dir=execplans_dir)
            warning_messages = [issue.message for issue in result.issues if issue.severity == "warning"]
            self.assertFalse(any("under a complete path" in message for message in warning_messages))
            self.assertEqual(result.error_count, 0)

            build = build_execplan_registry(
                root=root,
                execplans_dir=execplans_dir,
                output_path=registry_path,
                fail_on_warn=True,
            )
            self.assertTrue(build.wrote_registry)
            self.assertEqual(build.warning_count, 0)

    def test_collect_warns_when_archive_path_plan_is_not_done_or_archived(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execplans_dir = root / ".agent" / "exec_plans"
            registry_path = execplans_dir / "registry.json"

            _write_execplan(
                execplans_dir
                / "archive"
                / "2026"
                / "02"
                / "14"
                / "EP-20260214-004_agent-home-workspace"
                / "EP-20260214-004_agent-home-workspace.md",
                plan_id="EP-20260214-004",
                title="Agent Home Workspace",
                status="active",
            )

            result = collect_execplan_registry(root=root, execplans_dir=execplans_dir)
            warning_messages = [issue.message for issue in result.issues if issue.severity == "warning"]
            self.assertTrue(any("under a complete path" in message for message in warning_messages))
            self.assertEqual(result.error_count, 0)

            build = build_execplan_registry(
                root=root,
                execplans_dir=execplans_dir,
                output_path=registry_path,
                fail_on_warn=True,
            )
            self.assertFalse(build.wrote_registry)
            self.assertEqual(build.warning_count, 1)
            self.assertFalse(registry_path.exists())


if __name__ == "__main__":
    unittest.main()
