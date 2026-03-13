---
id: EP-20260313-001/MS001
execplan_id: EP-20260313-001
ms: 1
title: "Project profile detection and snapshot wiring"
status: completed
domain: backend
owner: "@codex"
created: 2026-03-13
updated: 2026-03-13
tags: [phase1, profiling, snapshot]
risk: low
links:
  issue: ""
  docs: ""
  pr: ""
---

# Project profile detection and snapshot wiring

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Create a deterministic `project_profile` builder and attach it to `ProjectSnapshot`, so downstream phases can route behavior based on stable repository signals instead of implicit heuristics.

## Definition of Done

- [x] Implementation complete.
- [x] Validation complete.
- [x] Documentation and operational notes updated.

## Scope

### In Scope
- Add a new profile builder module under `src/agentrules/core/pipeline/`.
- Detect frontend/web and Python signals from dependency manifests and tree-visible files.
- Wire `project_profile` into `ProjectSnapshot` and snapshot construction.
- Add/adjust unit tests for snapshot/profile behavior.

### Out of Scope
- Running additional Phase 1 agents.
- Prompt contract updates for new specialized agents.
- Phase 2/3 behavior changes.

## Workstreams & Tasks

- [x] Workstream A: Profile schema + detector implementation.
- [x] Workstream B: Pipeline snapshot dataclass wiring and test coverage.

## Risks & Mitigations

- Risk: File-signal scanning diverges from current exclusion policy.
  Mitigation: Reuse existing exclusion/gitignore/managed-output filters from pipeline settings.
- Risk: Path normalization issues across absolute/relative manifests.
  Mitigation: Normalize profile file paths relative to target directory before storing.

## Validation / QA Plan

- `ruff check src/agentrules/core/pipeline src/agentrules/core/analysis/phase_1.py tests/unit/test_pipeline_snapshot.py`
- `pytest -q tests/unit/test_pipeline_snapshot.py`
- Add and run targeted profile detector tests (new test module in `tests/unit/`).

## Changelog

- 2026-03-13: Milestone created.
- 2026-03-13: Scope defined and moved to in-progress.
- 2026-03-13: Implemented deterministic profile detector in `core/pipeline/project_profile.py`.
- 2026-03-13: Wired `project_profile` into `ProjectSnapshot` and snapshot builder.
- 2026-03-13: Added `tests/unit/test_project_profile.py` and updated pipeline snapshot tests.
- 2026-03-13: Validation green: `ruff check ...` and `pytest -q tests/unit/test_pipeline_snapshot.py tests/unit/test_project_profile.py`.
