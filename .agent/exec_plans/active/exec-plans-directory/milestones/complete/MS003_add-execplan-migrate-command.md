---
id: EP-20261101-001/MS003
execplan_id: EP-20261101-001
ms: 3
title: Add execplan migrate command
status: completed
domain: cross-cutting
owner: '@claude'
created: 2026-11-01
updated: '2026-11-01'
tags:
- execplan
- migration
- cli
risk: med
links:
  issue: ''
  docs: ''
  pr: ''
---

# Add execplan migrate command

This milestone is a living document under the parent ExecPlan EP-20261101-001. Keep metadata and the parent Progress current.

## Objective

A user with a legacy `.agent/` workspace runs `agentrules execplan migrate` once. Their plans, guides, registry, and rules file move to the `.exec_plans/` layout without losing data or unrelated files, and later commands use the new layout without hints.

## Definition of Done

- `src/agentrules/core/execplan/migration.py` provides `migrate_execplan_workspace` with the behavior in the parent plan: pre-checked moves, guide-only path rewrite, empty-directory cleanup, rules-file guidance update when legacy guide paths are present, and registry rebuild when a registry exists.
- `agentrules execplan migrate [--root PATH] [--dry-run]` prints each action. It exits 0 on success or no-op, 1 when the registry rebuild reports errors, and 2 on refusal.
- Tests cover: full migration of a seeded legacy repository (active and complete plans with milestones, registry, guides, rules file, unrelated `.agent/` file); dry-run writes nothing; refusal on a destination collision moves nothing; a second run is a no-op; a partially migrated repository converges; ExecPlan bodies are not rewritten.
- Full validation passes.

## Scope

### In Scope
- `src/agentrules/core/execplan/migration.py` (new), imported directly by the CLI (not re-exported; see the parent plan's import-cycle note).
- `migrate` command in `src/agentrules/cli/commands/execplan.py`, using `get_config_manager().resolve_rules_filename()`.
- `tests/unit/test_execplan_migration.py` (new) and a CLI case in `tests/unit/test_execplan_cli.py`.

### Out of Scope
- Rewriting ExecPlan or milestone bodies. Calling Git. Locking during migration (concurrent ExecPlan edits during migration are unsupported and documented).

## Workstreams & Tasks

- Implement move planning plus collision and overlap checks.
- Implement convergent apply steps and the dry-run report.
- Wire the CLI command and messages.
- Write the behavior tests listed above.

## Risks & Mitigations

- Risk: Data loss if a move overwrites an existing file. Mitigation: refuse before any move when a destination exists or two destinations overlap; never delete files, only empty directories.
- Risk: Customized guides are lost. Mitigation: guides are moved and path-rewritten, never regenerated from package data.
- Risk: The rules file gains a new section unexpectedly. Mitigation: only touch it when it already references a legacy guide path.

## Validation / QA Plan

- `.venv/bin/pytest -q tests/unit/test_execplan_migration.py tests/unit/test_execplan_cli.py`
- Manual end-to-end transcript from the parent plan's Concrete Steps in a temporary directory.
- Full suite, ruff, pyright, import smoke, `git diff --check`.

## Changelog

- 2026-11-01: Milestone created and scoped.
- 2026-11-01: Implemented the migration module, the `migrate` command, 7 migration tests, and 2 CLI tests (happy path plus no-op rerun; exit codes 2 and 1). Extracted `_print_registry_issues` in the command module so `new`, `complete`, and `migrate` share one issue printer. Full suite 1,176 passed with the 2 pre-existing picker failures; ruff, pyright, import smoke, diff check clean.
