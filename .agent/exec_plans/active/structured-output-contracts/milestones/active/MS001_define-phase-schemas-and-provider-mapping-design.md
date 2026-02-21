---
id: EP-20260221-001/MS001
execplan_id: EP-20260221-001
ms: 1
title: "Define phase schemas and provider mapping design"
status: completed
domain: cross-cutting
owner: "@codex"
created: 2026-02-21
updated: 2026-02-21
tags: [schemas, mapping]
risk: med
links:
  issue: ""
  docs: "internal-docs/integrations"
  pr: ""
---

# Define phase schemas and provider mapping design

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Create a single source of truth for phase output contracts and provider mapping rules so provider adapters can request structured output consistently.

## Definition of Done

- [x] New module defines concrete JSON schemas for phases 1, 2, 3, 4, 5, and final.
- [x] Provider mapping matrix is codified with provider-specific request knobs and fallback policy.
- [x] Unit tests validate schema retrieval and mapping for each provider/phase.
- [x] Milestone status updated and changelog notes added.

## Scope

### In Scope
- Add schema and mapping utility module(s) under `src/agentrules/core/utils/`.
- Include explicit per-provider guidance captured from:
  - `internal-docs/integrations/openai/structured-outputs.md`
  - `internal-docs/integrations/anthropic/structured-outputs.md`
  - `internal-docs/integrations/gemini/structured-outputs.md`
  - `internal-docs/integrations/deepseek/structured-outputs.md`
  - `internal-docs/integrations/xai/structured-outputs.md`

### Out of Scope
- Wiring providers to consume schemas at request time (MS002).
- Phase 2 parsing integration (MS003).

## Workstreams & Tasks

- [x] Workstream A: Define phase schema payloads and JSON Schema documents.
- [x] Workstream B: Define provider mapping and fallback metadata.
- [x] Workstream C: Add focused tests for schema/mapping module.

## Risks & Mitigations

- Risk: Overly strict schema may not match current prompt behavior and produce parser drift.
  Mitigation: Keep contracts additive and preserve fallback fields used by existing code.

## Validation / QA Plan

- `PYTHONPATH=src .venv/bin/pytest tests/unit -k \"schema or structured\"`
- `PYTHONPATH=src .venv/bin/python -m agentrules execplan milestone list EP-20260221-001 --active-only`

## Changelog

- 2026-02-21: Milestone created.
- 2026-02-21: Scope and objective defined; status moved to in_progress.
- 2026-02-21: Implemented `src/agentrules/core/utils/structured_outputs.py` with phase schemas and provider mapping metadata.
- 2026-02-21: Added schema/mapping unit coverage in `tests/unit/utils/test_structured_outputs.py`; milestone completed.
