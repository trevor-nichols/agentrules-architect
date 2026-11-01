---
id: EP-20261101-001
title: "Move ExecPlan workspace from .agent to .exec_plans"
status: active
kind: migration
domain: cross-cutting
owner: "@claude"
created: 2026-11-01
updated: 2026-11-01
tags: [execplan, layout, migration, scaffold]
touches: [cli, docs, tests]
risk: med
breaking: false
migration: true
links:
  issue: ""
  pr: ""
  docs: ""
depends_on: []
supersedes: []
---

# EP-20261101-001 - Move ExecPlan workspace from .agent to .exec_plans

This ExecPlan is a living document. Keep `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` up to date as work proceeds.

Maintain this plan in accordance with the repository ExecPlan guide. At the start of this plan that guide lives at `.agent/PLANS.md`; after Milestone 4 it lives at `.exec_plans/PLANS.md`. This plan intentionally discusses both paths, so do not rewrite the legacy paths in this file.

## Purpose / Big Picture

AgentRules stores its planning workspace in a hidden `.agent/` directory: the ExecPlan guide `.agent/PLANS.md`, the milestone guide `.agent/templates/MILESTONE_TEMPLATE.md`, and all plans under `.agent/exec_plans/`. Coding harnesses have since standardized on a different directory, `.agents/` (plural), for skills and agent assets. The two names are one letter apart, which confuses people and tools. After this change, new repositories get a single, self-describing `.exec_plans/` directory that holds the guides, the registry, and the plans together. Existing repositories that still use `.agent/` keep working without changes, and a single command, `agentrules execplan migrate`, moves them to the new layout and updates their rules file.

To see it working: in an empty directory, `agentrules execplan new "Demo"` creates `.exec_plans/active/demo/EP-YYYYMMDD-001_demo.md` and `.exec_plans/registry.json`. In a repository that still has `.agent/exec_plans/`, the same command writes into `.agent/exec_plans/` and prints a one-line hint to migrate. Running `agentrules execplan migrate` in that repository moves everything into `.exec_plans/`, rewrites the two guide files and the rules file to reference the new paths, rebuilds the registry, and removes `.agent/` when nothing else is left in it.

## Scope

In scope: a layout resolver that decides which workspace a repository uses; making every ExecPlan command, the core ExecPlan library functions, the optional scaffold generator, the packaged templates, and the AGENTS.md guidance injector use that resolver; a migration command; tests; migrating this repository itself; and updating `README.md`, `AGENTS.md`, `SNAPSHOT.md`, and `.gitignore`.

Out of scope: rewriting the text of existing ExecPlans and milestones (they are user-authored records and may legitimately mention the old paths, as this plan does); renaming the persisted configuration key `generate_agent_scaffold`; renaming the Python module `agent_scaffold.py`; reading plans from both directories at the same time; excluding `.agents/` from analysis (noted as a follow-up).

## Progress

- [x] (2026-11-01 15:00Z) Investigated all `.agent` touchpoints and verified with real data that a flattened `.exec_plans/` (guides next to `active/` and `complete/`) yields the same registry: 15 plans, 0 errors, 0 warnings.
- [x] (2026-11-01 15:10Z) User chose detection plus explicit migrate, migrate updates the rules file, and ExecPlan-first delivery. Plan and milestones created via CLI on branch `feat/exec-plans-directory`.
- [x] (2026-11-01 15:45Z) Milestone 1: added `core/execplan/layout.py` and `cli/services/execplan_paths.py`; core and CLI defaults now resolve through `resolve_execplan_paths`; five private `_resolve_path` copies removed. Full suite 1,164 passed (6 new), with only the 2 pre-existing picker failures; ruff, pyright, import smoke, diff check clean. The two new CLI tests fail on the pre-change source and pass after.
- [x] (2026-11-01 16:20Z) Milestone 2: scaffold writes only `.exec_plans/` and refuses legacy repositories with a migrate hint; packaged guides and the ExecPlan body template follow the layout; rules guidance is built from the detected layout and written atomically; `.exec_plans` excluded from analysis; labels say "ExecPlan scaffold". Full suite 1,167 passed (3 new), plus the 2 pre-existing failures; new-layout assertions fail on the pre-change source.
- [x] (2026-11-01 17:05Z) Milestone 3: added `core/execplan/migration.py` and `agentrules execplan migrate [--root] [--dry-run]`. Full suite 1,176 passed (9 new), plus the 2 pre-existing failures. Disabling the registry staleness check, conflict check, empty-directory cleanup, or guide rewrite at runtime each fails at least one migration test. The end-to-end transcript in Concrete Steps matches.
- [ ] Milestone 4: migrate this repository, update documentation, full validation, complete this plan.

## Surprises & Discoveries

- Observation: Plan discovery is glob-based (`EP-*.md`), so guide files, `registry.json`, and scaffold `.bak.*` backups can share the plans directory without being misread as plans.
  Evidence: copying `.agent/exec_plans/*`, `.agent/PLANS.md`, `.agent/templates/`, and a `PLANS.md.bak.*` file into one `.exec_plans/` directory and calling `collect_execplan_registry` printed `plans: 15 errors: 0 warnings: 0`, identical to the original tree.
- Observation: The CLI options `--execplans-dir` and `--out` have static defaults (`DEFAULT_EXECPLANS_DIR`, `DEFAULT_REGISTRY_PATH`), and no CLI test passes `--execplans-dir`, so all CLI tests exercise the defaults.
  Evidence: `rg -- --execplans-dir tests` returns no matches.
- Observation: With a custom `--execplans-dir` and no `--out`, the registry is still written to `.agent/exec_plans/registry.json`, which is outside the chosen directory.
  Evidence: `src/agentrules/cli/commands/execplan.py` passes the static `DEFAULT_REGISTRY_PATH` default regardless of `--execplans-dir`.
- Observation: The base branch already has 2 failing tests in `tests/unit/test_cli_model_picker_ui.py`. Rich wraps the console message at 80 columns, so the asserted substring "Saved replacement" spans a line break. They are unrelated to this plan and fail identically before and after each milestone. New CLI tests here normalize whitespace before asserting to avoid the same trap.
  Evidence: `2 failed, 1158 passed` on the untouched base; the same two failures after Milestone 1 with `1164 passed`.
- Observation: `migration.py` cannot be re-exported from `agentrules.core.execplan`. `clean_agentrules.py` imports `agentrules.core.execplan.layout`, which initializes the package `__init__`; if `__init__` imported `migration`, that would import `clean_agentrules` while it is still half-initialized.
  Evidence: Import graph: `formatters/clean_agentrules -> core/execplan/__init__ -> migration -> formatters/clean_agentrules`. The CLI imports `agentrules.core.execplan.migration` directly, as it already does for `creator` and `milestones`.
- Observation: `.agent/exec_plans/.locks/` in `.gitignore` is stale. `src/agentrules/core/execplan/locks.py` now locks the ExecPlan file itself and never creates a `.locks` directory.

## Decision Log

- Decision: Flatten the workspace so `.exec_plans/` holds `PLANS.md`, `templates/`, `registry.json`, `active/`, and `complete/` directly.
  Rationale: Matches the user's request ("make .exec_plans the top level directory") and avoids a redundant `.exec_plans/exec_plans/`. Verified safe because discovery only matches `EP-*.md`.
  Date/Author: 2026-11-01 / @claude
- Decision: Detect the layout per repository and keep legacy repositories fully operational for ExecPlan commands, instead of a hard cut or reading both directories.
  Rationale: A hard cut would let `execplan new` create `.exec_plans/` beside an existing `.agent/exec_plans/` and allocate IDs without seeing old plans, which can duplicate IDs. Reading both roots needs cross-root ID allocation, completion, and registry merging, which is too much for a transitional feature. The user selected this option.
  Date/Author: 2026-11-01 / @claude
- Decision: When both `.exec_plans/` and legacy markers exist, fail with an error that names `agentrules execplan migrate` and `--execplans-dir`, unless `--execplans-dir` is passed explicitly.
  Rationale: Fail fast on ambiguity rather than guess which directory owns ID allocation.
  Date/Author: 2026-11-01 / @claude
- Decision: Legacy markers are the specific entries migration moves (`.agent/exec_plans`, `.agent/PLANS.md`, `.agent/templates/MILESTONE_TEMPLATE.md`), not the bare `.agent/` directory.
  Rationale: A leftover `.agent/` with unrelated files (for example `.DS_Store`) must not keep a migrated repository in legacy mode or trigger the ambiguity error.
  Date/Author: 2026-11-01 / @claude
- Decision: The default registry path is always `<execplans dir>/registry.json`, including when `--execplans-dir` is custom.
  Rationale: Both layouts already store the registry there, so one rule replaces a second constant and fixes the custom-directory quirk noted above.
  Date/Author: 2026-11-01 / @claude
- Decision: The scaffold generator writes only the new layout. In a legacy repository, `analyze` skips it with a migrate hint and `agentrules scaffold sync` exits with an error.
  Rationale: Creating `.exec_plans/` next to `.agent/exec_plans/` would trigger the ambiguity error on every later command. Rendering the guides for both layouts is unnecessary when migration is one command.
  Date/Author: 2026-11-01 / @claude
- Decision: `agentrules execplan migrate` rewrites legacy paths only in the two guide files and updates the rules file's ExecPlans block via the existing `ensure_execplans_guidance`. It never edits ExecPlan or milestone bodies.
  Rationale: Guides are tool-owned and must match the layout. Plan bodies are user-authored records; a blind rewrite would corrupt plans that discuss the old paths, such as this one. The user chose rules-file updates over report-only.
  Date/Author: 2026-11-01 / @claude
- Decision: Keep the config key `generate_agent_scaffold` and the module name `agent_scaffold.py`; update only user-facing labels.
  Rationale: The key is persisted in user `config.toml` files. Renaming the module adds churn without behavior.
  Date/Author: 2026-11-01 / @claude
- Decision: Stack the branch on `codex/provider-model-api-audit-2026-10` (open PR #42) instead of `main`.
  Rationale: PR #42 adds a completed ExecPlan under `.agent/exec_plans/` and edits `README.md`, `AGENTS.md`, and `agent_scaffold.py`; branching from `main` would conflict with the directory move once #42 merges.
  Date/Author: 2026-11-01 / @claude
- Decision: Migration also refuses when `.agent`, `.agent/exec_plans`, `.agent/templates`, `.exec_plans`, or `.exec_plans/templates` is a symlink.
  Rationale: `os.replace` through a symlinked directory would move plans outside the repository, or fail partway across devices. This matches the scaffold's existing symlink refusal.
  Date/Author: 2026-11-01 / @claude
- Decision: Rebuild the registry when entries moved or when any registry plan `path` still starts with `.agent/exec_plans/` (an unparsable registry counts as stale).
  Rationale: `build_execplan_registry` always rewrites the file, so rebuilding unconditionally would make every run report work and break the "nothing to migrate" no-op. Checking the plan paths rather than the raw text avoids false positives from titles that mention the old directory.
  Date/Author: 2026-11-01 / @claude
- Decision: Migrated ExecPlan bodies keep their generated sentence "If `.agent/PLANS.md` exists in this repository...".
  Rationale: Plan bodies stay untouched by design. The rules file, which agents read first, is updated. The README migration notes tell users to adjust active plans if they want.
  Date/Author: 2026-11-01 / @claude
- Decision: Rules-file guidance follows the detected layout and keeps its exact wording, including the existing "your writing" typo.
  Rationale: Changing any required line rewrites the block in every rules file on the next analysis. Keeping the legacy text byte-identical means unmigrated repositories see no churn; only the path changes once a repository is on `.exec_plans/`.
  Date/Author: 2026-11-01 / @claude

## Outcomes & Retrospective

Not started.

## Context and Orientation

The Python package lives in `src/agentrules`. The term "ExecPlan" means a Markdown design document with YAML front matter (a `---`-delimited metadata header) whose filename starts with a canonical ID `EP-YYYYMMDD-NNN`. A "milestone" is a smaller Markdown document owned by one ExecPlan, stored under that plan's `milestones/active/` or `milestones/complete/` directory. The "registry" is a generated `registry.json` that lists every ExecPlan's metadata and path. The "scaffold" is the optional pair of guide files (`PLANS.md` and `templates/MILESTONE_TEMPLATE.md`) that AgentRules copies from package data into a repository after an analysis run when the user enables it. The "rules file" is the generated agent instructions file, `AGENTS.md` by default (configurable, for example `CLAUDE.md`).

The current (legacy) workspace, which this repository itself uses, looks like this:

    .agent/
      PLANS.md
      templates/MILESTONE_TEMPLATE.md
      exec_plans/
        registry.json
        active/<slug>/EP-..._<slug>.md
        active/<slug>/milestones/(active|complete)/MS###_<slug>.md
        complete/YYYY/MM/DD/EP-..._<slug>/...

The new workspace is:

    .exec_plans/
      PLANS.md
      templates/MILESTONE_TEMPLATE.md
      registry.json
      active/<slug>/...
      complete/YYYY/MM/DD/EP-..._<slug>/...

The ExecPlan domain code lives in `src/agentrules/core/execplan/`. `paths.py` classifies a file path relative to an "execplans root" (the directory that contains `active/` and `complete/`) and already supports older shapes such as `archive/` and top-level `<slug>/` directories; it needs no change. `registry.py` defines `DEFAULT_EXECPLANS_DIR = Path(".agent/exec_plans")` and `DEFAULT_REGISTRY_PATH = Path(".agent/exec_plans/registry.json")`, plus `collect_execplan_registry`, `build_execplan_registry`, `list_active_execplan_summaries`, and `summarize_registry_activity`. `creator.py` has `create_execplan` and `complete_execplan`; `milestones.py` has `create_execplan_milestone`, `list_execplan_milestones`, and `complete_execplan_milestone`. Each of these takes `execplans_dir` (and some take `registry_path`) with the static defaults above, and each module has its own private `_resolve_path(root, value)` helper. `__init__.py` re-exports the two default constants as public API. `creator.py` fills `src/agentrules/core/execplan/templates/EXECPLAN_TEMPLATE.md` with `string.Template.substitute`; line 27 of that template hard-codes `.agent/PLANS.md`.

The CLI lives in `src/agentrules/cli/`. `cli/app.py` registers command groups. `cli/commands/execplan.py` implements `execplan new|complete|list` and `execplan milestone new|list|complete|remaining`; `cli/commands/execplan_registry.py` implements `execplan-registry check|build|update`. Both declare `--execplans-dir` and `--out` with the static defaults. `cli/commands/scaffold.py` implements `scaffold sync [--check|--force]`. Every command calls `bootstrap_runtime()` from `cli/bootstrap.py` to get a Rich console.

The scaffold generator is `src/agentrules/core/utils/file_creation/agent_scaffold.py` (`create_agent_scaffold`, `sync_agent_scaffold`, constant `AGENT_DIRNAME = ".agent"`). Its packaged sources are `src/agentrules/core/utils/file_creation/templates/PLANS.md` and `MILESTONE_TEMPLATE.md`, whose text contains `.agent/...` paths. `src/agentrules/core/pipeline/output.py` calls `create_agent_scaffold` and `ensure_execplans_guidance` after each analysis. `ensure_execplans_guidance` in `src/agentrules/core/utils/formatters/clean_agentrules.py` injects a fixed "## ExecPlans" block under "Development Principles" in the rules file; the block's lines are module constants that reference `.agent/PLANS.md` and `.agent/templates/MILESTONE_TEMPLATE.md`. When existing lines do not match exactly, it replaces the whole block, so changing the lines automatically upgrades rules files on the next run. `src/agentrules/config/exclusions.py` excludes `.agent` from analysis and snapshots. UI labels mention `.agent` in `src/agentrules/cli/ui/settings/outputs.py`. The configured rules filename comes from `get_config_manager().resolve_rules_filename()` (see `src/agentrules/cli/commands/snapshot.py`). The shared atomic writer is `atomic_write_text` in `src/agentrules/core/utils/file_creation/atomic_write.py`.

## Plan of Work

Milestone 1 adds `src/agentrules/core/execplan/layout.py`. It defines the frozen dataclass `ExecPlanLayout` with `workspace_dir`, `execplans_dir`, and `is_legacy`, plus derived `registry_path`, `plans_guide_path`, `milestone_guide_path`, and `legacy_markers`. Two constants describe the layouts: `CURRENT_LAYOUT` (`.exec_plans`, `.exec_plans`) and `LEGACY_LAYOUT` (`.agent`, `.agent/exec_plans`). `detect_execplan_layout(root)` returns the current layout when `.exec_plans/` exists or nothing exists, the legacy layout when only legacy markers exist, and raises `AmbiguousExecPlanLayoutError` (a `ValueError`) when both exist. `resolve_execplan_paths(root, *, execplans_dir=None, registry_path=None)` returns a frozen `ResolvedExecPlanPaths(layout, execplans_dir, registry_path)` with absolute paths. With `execplans_dir=None` it uses detection; with an explicit directory it uses it as given and reports the legacy layout only when that directory equals `<root>/.agent/exec_plans`. The registry defaults to `<execplans_dir>/registry.json`. `DEFAULT_EXECPLANS_DIR` and `DEFAULT_REGISTRY_PATH` move to `layout.py` with the new values and stay exported from `agentrules.core.execplan`. Core functions in `creator.py`, `milestones.py`, and `registry.py` change `execplans_dir` and `registry_path` defaults to `None` and resolve through `resolve_execplan_paths`; their private `_resolve_path` helpers go away. The two CLI modules change option defaults to `None` and share one helper, `resolve_cli_execplan_paths` in the new `src/agentrules/cli/services/execplan_paths.py`. It turns the ambiguity error into a red message and exit code 2, and prints `Using legacy .agent/exec_plans layout. Run \`agentrules execplan migrate\` to move it to .exec_plans/.` when the resolved layout is legacy.

Milestone 2 makes the generators follow the layout. `agent_scaffold.py` builds its file list from `CURRENT_LAYOUT`. `create_agent_scaffold` returns failure with a migrate hint in legacy repositories, and `sync_agent_scaffold` raises `ValueError` with the same hint. The packaged `PLANS.md` and `MILESTONE_TEMPLATE.md` replace `.agent/exec_plans` with `.exec_plans` and `.agent/templates/` with `.exec_plans/templates/`. `EXECPLAN_TEMPLATE.md` line 27 becomes ``If `${plans_guide_path}` exists in this repository, ...``, and `create_execplan` substitutes the resolved layout's guide path. `clean_agentrules.py` builds the guidance block from an `ExecPlanLayout`. `ensure_execplans_guidance` keeps its signature, detects the layout from the directory, and writes with `atomic_write_text`. `exclusions.py` adds `.exec_plans`, and the labels in `outputs.py`, `output.py`, `scaffold.py`, and the registry CLI help say "ExecPlan scaffold" or "ExecPlans registry" instead of `.agent`.

Milestone 3 adds `src/agentrules/core/execplan/migration.py` and the `execplan migrate [--root PATH] [--dry-run]` command. The core function `migrate_execplan_workspace(root, *, rules_filename, dry_run=False)` plans the moves:
- every child of `.agent/exec_plans/` moves to `.exec_plans/<name>`;
- `.agent/PLANS.md` moves to `.exec_plans/PLANS.md`;
- `.agent/templates/MILESTONE_TEMPLATE.md` moves to `.exec_plans/templates/MILESTONE_TEMPLATE.md`.

It refuses with a `ValueError` before moving anything if a destination already exists or two destinations overlap. It then converges to the end state, in this order:
1. Move each entry with `os.replace`.
2. Rewrite the legacy path prefixes in the two guide files.
3. Remove `.agent/templates`, `.agent/exec_plans`, and `.agent` only when empty.
4. When the rules file contains a legacy guide path, call `ensure_execplans_guidance`. The moves have already removed every legacy marker, so detection returns the current layout.
5. When `.exec_plans/registry.json` exists, rebuild it.

Each step checks current state, so rerunning after a crash finishes the job, and rerunning after success is a no-op. Dry-run reports the planned moves and writes nothing.

Milestone 4 runs the migration on this repository, removes the stale `.gitignore` lock entry, updates `README.md` (paths plus a "Migrating from `.agent/`" subsection), updates the remaining `.agent` mentions in `AGENTS.md`, regenerates `SNAPSHOT.md` with `agentrules snapshot sync`, runs the full validation suite, and completes this plan with the CLI.

## Concrete Steps

All commands run from the repository root `/Volumes/AGENAI/Coding/public-github/agentrules-architect` using the project virtual environment in `.venv/`.

Per-milestone validation (expect all to pass):

    .venv/bin/pytest -q
    .venv/bin/ruff check .
    .venv/bin/pyright
    .venv/bin/python -c 'import agentrules; print("import ok")'
    git diff --check

End-to-end check after Milestone 1 (new repository uses the new layout):

    tmp=$(mktemp -d)
    .venv/bin/agentrules execplan new "Demo" --root "$tmp" --date 20261101
    # Created ExecPlan: <tmp>/.exec_plans/active/demo/EP-20261101-001_demo.md
    # Updated registry: <tmp>/.exec_plans/registry.json

End-to-end check after Milestone 3 (legacy repository migrates):

    tmp=$(mktemp -d)
    .venv/bin/agentrules execplan new "Old" --root "$tmp" --execplans-dir .agent/exec_plans --date 20261101
    .venv/bin/agentrules execplan list --root "$tmp"
    # Using legacy .agent/exec_plans layout. Run `agentrules execplan migrate` ...
    .venv/bin/agentrules execplan migrate --root "$tmp" --dry-run
    .venv/bin/agentrules execplan migrate --root "$tmp"
    .venv/bin/agentrules execplan list --root "$tmp" --path
    # EP-20261101-001 [planned] Old (milestones none) -> .exec_plans/active/old/EP-20261101-001_old.md

Milestone 4 on this repository:

    .venv/bin/agentrules execplan migrate --dry-run
    .venv/bin/agentrules execplan migrate
    .venv/bin/agentrules execplan-registry check
    .venv/bin/agentrules snapshot sync

## Validation and Acceptance

Acceptance is behavioral. In an empty directory, `execplan new` writes under `.exec_plans/`. In a repository that has only `.agent/exec_plans/`, every `execplan`, `execplan milestone`, and `execplan-registry` command operates on `.agent/exec_plans/` and prints the migrate hint. When both exist, those commands exit with code 2 and name `agentrules execplan migrate`. `agentrules execplan migrate` turns a legacy repository into one where `execplan list --path` shows `.exec_plans/...` paths, `registry.json` paths start with `.exec_plans/`, the rules file references `.exec_plans/PLANS.md`, and unrelated files in `.agent/` remain. A second run prints that there is nothing to migrate. `analyze` with the scaffold enabled in a legacy repository does not create `.exec_plans/`. New tests in `tests/unit/test_execplan_layout.py` and `tests/unit/test_execplan_migration.py`, plus updated CLI, scaffold, creator, and guidance tests, must pass along with the full suite, ruff, pyright, and the import smoke check.

## Idempotence and Recovery

ExecPlan commands are unchanged in their own idempotence. Migration checks every destination before moving anything, so a refused migration leaves the repository untouched. If the process stops partway, rerunning moves only the remaining entries and reapplies the guide rewrite, empty-directory cleanup, rules update, and registry rebuild, all of which are no-ops once done. Migration never deletes files; it only moves them and removes empty directories. In a Git repository, `git status` shows the moves as renames after `git add -A`, and `git checkout -- . && git clean -fd .exec_plans` restores the previous state if needed.

## Artifacts and Notes

Probe used to validate the flattened layout (abridged):

    plans: 15 errors: 0 warnings: 0
    sample path: .exec_plans/complete/2026/02/21/EP-20260221-001_structured-output-contracts/EP-20260221-001_structured-output-contracts.md
    original plans: 15 errors: 0 warnings: 0

## Interfaces and Dependencies

No new third-party dependencies. In `src/agentrules/core/execplan/layout.py`, define:

    REGISTRY_FILENAME = "registry.json"

    class AmbiguousExecPlanLayoutError(ValueError): ...

    @dataclass(frozen=True, slots=True)
    class ExecPlanLayout:
        workspace_dir: Path
        execplans_dir: Path
        is_legacy: bool
        registry_path: Path        # property: execplans_dir / REGISTRY_FILENAME
        plans_guide_path: Path     # property: workspace_dir / "PLANS.md"
        milestone_guide_path: Path # property: workspace_dir / "templates" / "MILESTONE_TEMPLATE.md"
        markers: tuple[Path, ...]  # property: (execplans_dir, plans_guide_path, milestone_guide_path)
        def is_present(self, root: Path) -> bool: ...  # any marker exists under root

    CURRENT_LAYOUT: ExecPlanLayout
    LEGACY_LAYOUT: ExecPlanLayout
    DEFAULT_EXECPLANS_DIR = CURRENT_LAYOUT.execplans_dir
    DEFAULT_REGISTRY_PATH = CURRENT_LAYOUT.registry_path

    def detect_execplan_layout(root: Path) -> ExecPlanLayout: ...

    @dataclass(frozen=True, slots=True)
    class ResolvedExecPlanPaths:
        layout: ExecPlanLayout
        execplans_dir: Path
        registry_path: Path

    def resolve_execplan_paths(root: Path, *, execplans_dir: Path | None = None, registry_path: Path | None = None) -> ResolvedExecPlanPaths: ...

In `src/agentrules/core/execplan/migration.py`, define:

    @dataclass(frozen=True, slots=True)
    class WorkspaceMove:
        source: Path
        destination: Path

    @dataclass(frozen=True, slots=True)
    class ExecPlanMigrationResult:
        moves: tuple[WorkspaceMove, ...]
        rewritten_guides: tuple[Path, ...]
        removed_directories: tuple[Path, ...]
        rules_message: str | None
        registry_result: RegistryBuildResult | None
        dry_run: bool
        is_noop: bool  # property: no moves, rewrites, removals, rules update, or registry rebuild

    def migrate_execplan_workspace(root: Path, *, rules_filename: str | None, dry_run: bool = False) -> ExecPlanMigrationResult: ...

`migration.py` is imported directly (`agentrules.core.execplan.migration`), not re-exported from the package, because of the import cycle recorded in Surprises & Discoveries.

In `src/agentrules/cli/services/execplan_paths.py`, define `resolve_cli_execplan_paths(context: CliContext, *, root: Path, execplans_dir: Path | None, registry_path: Path | None = None) -> ResolvedExecPlanPaths`. It takes the `CliContext` like other CLI services and raises `typer.Exit(2)` on ambiguity, so each command stays a single call.

---

Revision note (2026-11-01): Initial plan written after investigation and user decisions.

Revision note (2026-11-01): Milestone 3 complete. Added symlink refusal and path-based registry staleness, and recorded why `migration.py` is not re-exported and why plan bodies keep their old guide sentence.

Revision note (2026-11-01): Milestone 2 complete. Dropped the planned `layout` keyword on `ensure_execplans_guidance`: after migrate moves the files, detection already yields the current layout, so the override had no caller.

Revision note (2026-11-01): Milestone 1 complete. `ExecPlanLayout` uses one `markers` tuple plus `is_present` for both layouts, so detection is symmetric. The CLI helper takes `CliContext`, matching `cli/services/pipeline_runner.py`.
