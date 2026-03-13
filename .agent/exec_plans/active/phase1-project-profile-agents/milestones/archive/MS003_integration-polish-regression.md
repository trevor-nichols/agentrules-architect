---
id: EP-20260313-001/MS003
execplan_id: EP-20260313-001
ms: 3
title: "Integration polish docs and regression coverage"
status: completed
domain: backend
owner: "@codex"
created: 2026-03-13
updated: 2026-03-13
tags: [integration, docs, tests]
risk: low
links:
  issue: ""
  docs: ""
  pr: ""
---

# Integration polish docs and regression coverage

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Finalize integration by updating schemas/docs/snapshot references and adding regression coverage so the new profile and specialized Phase 1 outputs are stable across pipeline and test harnesses.

## Definition of Done

- [x] Implementation complete.
- [x] Validation complete.
- [x] Documentation and operational notes updated.

## Scope

### In Scope
- Update structured output schema declarations where Phase 1 output contract is documented.
- Update docs that describe Phase 1 shape and behavior.
- Update/extend pipeline tests impacted by `ProjectSnapshot` additions.
- Run cross-cutting validations and keep ExecPlan/milestone status synchronized.

### Out of Scope
- New feature work beyond profile + specialized agent support.
- Additional provider/runtime behavior unrelated to Phase 1 profile routing.

## Workstreams & Tasks

- [x] Workstream A: Schema/docs updates.
- [x] Workstream B: Regression tests and final validation pass.

## Risks & Mitigations

- Risk: Contract drift between docs/schema/tests.
  Mitigation: Update these artifacts in the same milestone and validate together.

## Validation / QA Plan

- `ruff check src tests`
- `pytest -q tests/unit/test_pipeline_snapshot.py tests/phase_1_test tests/unit/utils/test_structured_outputs.py`
- Optional broader smoke if feasible: `pytest -q` (or narrowed by changed areas if suite is heavy).

## Changelog

- 2026-03-13: Milestone created.
- 2026-03-13: Scope finalized.
- 2026-03-13: Updated `docs/structured-output-contracts.md` with Phase 1 `project_profile` and specialized agent contract notes.
- 2026-03-13: Added orchestrator regression coverage (`tests/unit/test_pipeline_orchestrator.py`) and Phase 1 schema assertion in structured-output tests.
- 2026-03-13: Synced `SNAPSHOT.md` after file additions/milestone archival moves.
- 2026-03-13: Validation green: `ruff check src tests` and `pytest -q tests/unit/test_pipeline_snapshot.py tests/unit/test_project_profile.py tests/unit/test_pipeline_orchestrator.py tests/phase_1_test tests/unit/utils/test_structured_outputs.py tests/unit/test_pipeline_output_writer.py`.
