---
id: EP-20261101-001/MS004
execplan_id: EP-20261101-001
ms: 4
title: Migrate this repository and update documentation
status: completed
domain: cross-cutting
owner: '@claude'
created: 2026-11-01
updated: '2026-11-01'
tags:
- execplan
- migration
- docs
risk: low
links:
  issue: ''
  docs: ''
  pr: ''
---

# Migrate this repository and update documentation

This milestone is a living document under the parent ExecPlan EP-20261101-001. Keep metadata and the parent Progress current.

## Objective

This repository uses `.exec_plans/` itself, which proves the migration on real data: 15+ plans, completed milestones, a customized `PLANS.md`, and this active plan. Documentation then describes the new layout and the migration path.

## Definition of Done

- `agentrules execplan migrate` has been run on this repository. `.agent/` is gone, `agentrules execplan-registry check` passes, `agentrules execplan list --path` shows this plan under `.exec_plans/active/`, and the `AGENTS.md` ExecPlans block references `.exec_plans/PLANS.md`.
- `README.md` describes `.exec_plans/` everywhere and has a "Migrating from `.agent/`" subsection.
- The remaining `.agent` mentions in `AGENTS.md` (output artifacts, scaffolding rules, validation checklist) describe `.exec_plans/`.
- `.gitignore` no longer lists the stale `.agent/exec_plans/.locks/` entry.
- `SNAPSHOT.md` is regenerated with `agentrules snapshot sync`.
- Full validation passes, and the parent plan is completed with `agentrules execplan complete EP-20261101-001`.

## Scope

### In Scope
- Running the migration; `README.md`, `AGENTS.md`, `.gitignore`, `SNAPSHOT.md`; the parent plan's living sections.

### Out of Scope
- Rewriting historical completed plans. `CHANGELOG.md` (owned by Release Please).

## Workstreams & Tasks

- Dry-run, then run the migration; verify the registry and listing.
- Update the docs and `.gitignore`; regenerate the snapshot.
- Run full validation; complete milestones and the plan through the CLI.

## Risks & Mitigations

- Risk: PR #42 (base branch) gains new files under `.agent/exec_plans/` before merge. Mitigation: after rebasing onto `main`, rerun `agentrules execplan migrate`; it moves only the remaining entries.

## Validation / QA Plan

- `.venv/bin/agentrules execplan-registry check` reports all plans with 0 errors.
- `rg -n '\.agent/' README.md AGENTS.md` shows only intentional legacy/migration mentions.
- Full suite, ruff, pyright, import smoke, `git diff --check`.

## Changelog

- 2026-11-01: Milestone created and scoped.
- 2026-11-01: Migrated this repository (dry run first, then the real run; 65 renames; registry check passed with 16 plans; rerun reported nothing to migrate). Fixed the rules-block blank-line bug the run exposed, with a failing-first assertion. Removed the stale `.gitignore` lock entry, fixed two stale `links.docs` pointers, updated README, AGENTS.md, and SNAPSHOT.md (with comments on new entries). Full suite 1,176 passed with the 2 pre-existing failures; ruff, pyright, import smoke, diff check clean.
