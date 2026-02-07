import json
import os
import tempfile
import unittest
from pathlib import Path

from agentrules.core.utils.execplan_registry import (
    build_execplan_registry,
    collect_execplan_registry,
)


def _write_execplan(path: Path, *, plan_id: str, title: str, depends_on: str = "[]") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


class ExecPlanRegistryTests(unittest.TestCase):
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
            self.assertFalse(any("under archive path" in message for message in warning_messages))

            build = build_execplan_registry(
                root=root,
                execplans_dir=execplans_dir,
                output_path=registry_path,
                fail_on_warn=True,
            )
            self.assertTrue(build.wrote_registry)
            self.assertEqual(build.warning_count, 0)


if __name__ == "__main__":
    unittest.main()
