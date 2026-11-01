---
id: EP-20261101-001/MS002
execplan_id: EP-20261101-001
ms: 2
title: "Make scaffold, templates, and rules guidance layout-aware"
status: planned
domain: cross-cutting
owner: "@claude"
created: 2026-11-01
updated: 2026-11-01
tags: [execplan, scaffold, templates]
risk: low
links:
  issue: ""
  docs: ""
  pr: ""
---

# Make scaffold, templates, and rules guidance layout-aware

This milestone is a living document under the parent ExecPlan EP-20261101-001. Keep metadata and the parent Progress current.

## Objective

Everything AgentRules generates points at the workspace a repository actually uses. New repositories get `.exec_plans/PLANS.md` and `.exec_plans/templates/MILESTONE_TEMPLATE.md`, and rules files and new ExecPlans reference those paths. Legacy repositories keep correct `.agent/` references and are never given a second, conflicting workspace.

## Definition of Done

- `create_agent_scaffold` and `sync_agent_scaffold` write `CURRENT_LAYOUT` paths. In a legacy repository, create returns failure with a migrate hint and sync raises `ValueError`; neither creates `.exec_plans/`.
- The packaged `PLANS.md` and `MILESTONE_TEMPLATE.md` reference `.exec_plans/...` only.
- `EXECPLAN_TEMPLATE.md` uses `${plans_guide_path}` and `create_execplan` substitutes the resolved layout's guide path.
- `ensure_execplans_guidance` accepts an optional `layout` (default: detect), builds the block from it, and writes atomically.
- `.exec_plans` is in `EXCLUDED_DIRS`; user-facing labels say "ExecPlan scaffold" or "ExecPlans registry".
- Tests cover scaffold paths and legacy refusal, guidance per layout, and the new-plan guide reference. Full validation passes.

## Scope

### In Scope
- `src/agentrules/core/utils/file_creation/agent_scaffold.py` and its packaged templates.
- `src/agentrules/core/execplan/templates/EXECPLAN_TEMPLATE.md`, `src/agentrules/core/execplan/creator.py`.
- `src/agentrules/core/utils/formatters/clean_agentrules.py`, `src/agentrules/core/pipeline/output.py`.
- `src/agentrules/config/exclusions.py`, `src/agentrules/cli/ui/settings/outputs.py`, `src/agentrules/cli/commands/scaffold.py`.
- `tests/unit/{test_agent_scaffold.py,test_clean_agentrules.py,test_execplan_creator.py,test_pipeline_output_writer.py,test_cli.py}`.

### Out of Scope
- Renaming `generate_agent_scaffold` or `agent_scaffold.py`. Excluding `.agents/`.

## Workstreams & Tasks

- Point the scaffold at `CURRENT_LAYOUT` and add the legacy guard.
- Replace legacy paths in the packaged guides; add the `${plans_guide_path}` placeholder.
- Parameterize the guidance block by layout; switch to `atomic_write_text`.
- Update exclusions and labels; update and add tests.

## Risks & Mitigations

- Risk: Every existing rules file gets its ExecPlans block rewritten on the next `analyze`. Mitigation: legacy repositories detect the legacy layout and keep their `.agent/` lines; only migrated or new repositories switch.

## Validation / QA Plan

- `.venv/bin/pytest -q tests/unit/test_agent_scaffold.py tests/unit/test_clean_agentrules.py tests/unit/test_execplan_creator.py tests/unit/test_pipeline_output_writer.py tests/unit/test_cli.py`
- `rg -n '\.agent' src/agentrules --glob '!**/__pycache__/**'` shows only `LEGACY_LAYOUT` and the exclusion entry.
- Full suite, ruff, pyright, import smoke, `git diff --check`.

## Changelog

- 2026-11-01: Milestone created and scoped.
