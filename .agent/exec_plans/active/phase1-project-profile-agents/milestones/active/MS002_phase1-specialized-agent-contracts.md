---
id: EP-20260313-001/MS002
execplan_id: EP-20260313-001
ms: 2
title: "Phase 1 specialized agent contracts and gating"
status: planned
domain: backend
owner: "@codex"
created: 2026-03-13
updated: 2026-03-13
tags: [phase1, prompts, agents]
risk: med
links:
  issue: ""
  docs: ""
  pr: ""
---

# Phase 1 specialized agent contracts and gating

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Introduce explicit specialized Phase 1 agent contracts and execute them conditionally based on `project_profile` so frontend-design and Python-tooling repositories receive targeted discovery findings.

## Definition of Done

- [ ] Implementation complete.
- [ ] Validation complete.
- [ ] Documentation and operational notes updated.

## Scope

### In Scope
- Add prompt contracts for `Frontend Design Agent` and `Python Tooling Agent`.
- Add deterministic gating helpers using `project_profile` booleans.
- Extend `Phase1Analysis.run()` context payloads and result aggregation for specialized agents.
- Add/adjust unit tests for gating and context routing.

### Out of Scope
- Phase 2 planner behavior changes.
- Deep analysis file-assignment strategy changes in Phase 3.

## Workstreams & Tasks

- [ ] Workstream A: Prompt and gating contract implementation.
- [ ] Workstream B: Phase 1 execution and test coverage.

## Risks & Mitigations

- Risk: Added agents increase latency and token usage for all repositories.
  Mitigation: Strict conditional gating; agents run only when profile indicates relevance.
- Risk: Breaking current tests that assume fixed initial agent count.
  Mitigation: Update tests to assert presence/absence based on profile and preserve existing baseline behavior when profile is generic.

## Validation / QA Plan

- `ruff check src/agentrules/config/prompts/phase_1_prompts.py src/agentrules/core/analysis/phase_1.py tests/phase_1_test`
- `pytest -q tests/phase_1_test`
- Add targeted tests for specialized agent gating and profile-to-context wiring.

## Changelog

- 2026-03-13: Milestone created.
- 2026-03-13: Scope finalized.
