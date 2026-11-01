---
id: EP-20260221-001/MS003
execplan_id: EP-20260221-001
ms: 3
title: "Integrate Phase 2 parser pipeline and add tests"
status: completed
domain: cross-cutting
owner: "@codex"
created: 2026-02-21
updated: 2026-02-21
tags: [phase2, parser, tests]
risk: med
links:
  issue: ""
  docs: "src/agentrules/core/utils/parsers/agent_parser.py"
  pr: ""
---

# Integrate Phase 2 parser pipeline and add tests

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Consume structured Phase 2 plans first (agents list/object), keep existing XML parsing as resilient fallback, and prove behavior with unit tests.

## Definition of Done

- [x] `Phase2Analysis` accepts structured plan payloads without string/XML conversion.
- [x] Agent parser handles structured dict payload safely and validates expected shape.
- [x] Existing fallback behavior still works for text/XML plans.
- [x] Unit tests cover structured success path + fallback path.

## Scope

### In Scope
- Phase 2 and parser integration changes.
- Tests for Phase 2 structured response handoff and parser behavior.

### Out of Scope
- Full replacement of all legacy parser helpers.
- Removing emergency fallback logic.

## Workstreams & Tasks

- [x] Workstream A: Add structured response normalization in architect phase methods.
- [x] Workstream B: Update Phase 2 run path to prioritize structured agents.
- [x] Workstream C: Add/adjust parser and pipeline tests.

## Risks & Mitigations

- Risk: Existing tests assume raw XML strings and may fail with dict-based contracts.
  Mitigation: Keep compatibility fields (`plan` text) while adding structured fields.

## Validation / QA Plan

- `PYTHONPATH=src .venv/bin/pytest tests/phase_2_test tests/unit/test_agent_parser_basic.py`
- `PYTHONPATH=src .venv/bin/pytest tests/unit/agents`
- `PYTHONPATH=src .venv/bin/python -m agentrules execplan milestone list EP-20260221-001`

## Changelog

- 2026-02-21: Milestone created.
- 2026-02-21: Defined integration and test deliverables for Phase 2 structured handoff.
- 2026-02-21: Updated `Phase2Analysis.run` to parse agents from full analysis-plan response payload.
- 2026-02-21: Added phase handoff and parser-focused tests (`tests/unit/test_phase_events.py`, `tests/phase_2_test/test_phase2_offline.py`); milestone completed.
