---
id: EP-20261101-001/MS001
execplan_id: EP-20261101-001
ms: 1
title: Add layout resolver and wire core and CLI defaults
status: completed
domain: cross-cutting
owner: '@claude'
created: 2026-11-01
updated: '2026-11-01'
tags:
- execplan
- layout
- cli
risk: med
links:
  issue: ''
  docs: ''
  pr: ''
---

# Add layout resolver and wire core and CLI defaults

This milestone is a living document under the parent ExecPlan EP-20261101-001. Keep metadata and the parent Progress current.

## Objective

Every ExecPlan command and core library function picks its workspace from one resolver. New repositories use `.exec_plans/`, legacy repositories keep using `.agent/exec_plans/` with a migrate hint, and an ambiguous repository fails with an actionable error.

## Definition of Done

- `src/agentrules/core/execplan/layout.py` exists with `ExecPlanLayout`, `CURRENT_LAYOUT`, `LEGACY_LAYOUT`, `detect_execplan_layout`, `resolve_execplan_paths`, `ResolvedExecPlanPaths`, `AmbiguousExecPlanLayoutError`, `REGISTRY_FILENAME`, `DEFAULT_EXECPLANS_DIR`, and `DEFAULT_REGISTRY_PATH`.
- `creator.py`, `milestones.py`, and `registry.py` default `execplans_dir`/`registry_path`/`output_path` to `None` and resolve through `resolve_execplan_paths`; their private `_resolve_path` helpers are removed.
- `agentrules.core.execplan` still exports `DEFAULT_EXECPLANS_DIR` and `DEFAULT_REGISTRY_PATH`, now pointing at `.exec_plans`, and also exports the layout API.
- CLI options `--execplans-dir` and `--out` default to `None`. A shared helper in `src/agentrules/cli/services/execplan_paths.py` prints the legacy hint and maps the ambiguity error to exit code 2.
- `tests/unit/test_execplan_layout.py` covers detection and resolution. CLI tests cover the new default, a legacy repository, and the ambiguous case. Existing CLI tests assert `.exec_plans/` paths.
- Full pytest, ruff, pyright, import smoke, and `git diff --check` pass.

## Scope

### In Scope
- `src/agentrules/core/execplan/{layout.py,creator.py,milestones.py,registry.py,locks.py,__init__.py}`.
- `src/agentrules/cli/commands/{execplan.py,execplan_registry.py}` and the new `src/agentrules/cli/services/execplan_paths.py`.
- `tests/unit/test_execplan_layout.py` (new), `tests/unit/test_execplan_cli.py`, `tests/unit/test_execplan_milestone_cli.py`, `tests/unit/test_execplan_registry_cli.py`.

### Out of Scope
- Scaffold, templates, rules guidance, exclusions (Milestone 2). Migration (Milestone 3).

## Workstreams & Tasks

- Write `layout.py` and its tests first, then switch the core modules to it.
- Switch both CLI modules to `None` defaults through the shared helper; update option help text to say "ExecPlans registry" instead of `.agent/exec_plans/registry.json`.
- Update CLI tests that start from an empty directory to expect `.exec_plans/`; add legacy and ambiguous CLI cases.

## Risks & Mitigations

- Risk: A custom `--execplans-dir` without `--out` now writes `registry.json` inside that directory instead of `.agent/exec_plans/`. Mitigation: documented in the parent Decision Log; this matches the directory the user chose.
- Risk: The legacy hint changes CLI output in legacy repositories. Mitigation: it is a single extra line, and tests assert with `assertIn`.

## Validation / QA Plan

- `.venv/bin/pytest -q tests/unit/test_execplan_layout.py tests/unit/test_execplan_cli.py tests/unit/test_execplan_milestone_cli.py tests/unit/test_execplan_registry_cli.py tests/unit/test_execplan_creator.py tests/unit/test_execplan_milestones.py tests/unit/test_execplan_registry.py`
- Full suite, `.venv/bin/ruff check .`, `.venv/bin/pyright`, import smoke, `git diff --check`.
- Before/after: `agentrules execplan new "Demo" --root <empty tmp>` creates `.agent/exec_plans/...` before and `.exec_plans/...` after.

## Changelog

- 2026-11-01: Milestone created and scoped.
- 2026-11-01: Implemented the resolver, core/CLI wiring, and tests. Core tests that pass `.agent/exec_plans` explicitly were left unchanged, since the directory name there is incidental. CLI tests that rely on defaults now assert `.exec_plans/`. Full suite 1,164 passed with the 2 pre-existing picker failures; ruff, pyright, import smoke, diff check clean.
