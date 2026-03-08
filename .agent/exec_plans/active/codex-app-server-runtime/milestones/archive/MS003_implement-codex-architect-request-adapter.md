---
id: EP-20260308-001/MS003
execplan_id: EP-20260308-001
ms: 3
title: "Implement Codex architect request adapter"
status: done
domain: cross-cutting
owner: "@codex"
created: 2026-03-08
updated: 2026-03-08
tags: [codex, provider, structured-outputs]
risk: med
links:
  issue: ""
  docs: ".agent/exec_plans/active/codex-app-server-runtime/EP-20260308-001_codex-app-server-runtime.md"
  pr: ""
---

# Implement Codex architect request adapter

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Implement `CodexArchitect` so Codex can satisfy the same provider contract as the current Anthropic/OpenAI/Gemini/DeepSeek/xAI adapters. When this milestone is complete, the factory can create a Codex architect, structured phases can pass JSON Schema via `outputSchema`, and the adapter returns the standard AgentRules result envelopes.

## Definition of Done

- `ArchitectFactory` can create `CodexArchitect` for `ModelProvider.CODEX`.
- `CodexArchitect` supports `analyze`, `create_analysis_plan`, `synthesize_findings`, `consolidate_results`, and `final_analysis`.
- The adapter launches app-server with per-process `developer_instructions` overrides instead of mutating persistent config.
- Structured phases send `outputSchema` and parse the final result into the expected response fields.
- Error handling maps app-server failures into actionable AgentRules errors.
- Unit tests cover factory routing, request construction, final-message parsing, and schema-driven output parsing.

## Scope

### In Scope
- `CodexArchitect` and any helper modules it needs.
- Provider-factory wiring and model-config lookup updates.
- Response parsing and error normalization.
- Structured-output support for phase2/phase4/phase5/final.

### Out of Scope
- CLI settings UX beyond what is needed to instantiate the architect.
- Phase 1 researcher special cases.
- Phase 3 file-handling special cases.

## Workstreams & Tasks

- [x] Provider adapter: implemented `CodexArchitect`, `request_builder.py`, `response_parser.py`, and factory wiring for `ModelProvider.CODEX`.
- [x] Request policy: set sane defaults for ephemeral threads, read-only sandboxing, approval policy `never`, model, effort, reasoning summary, and `outputSchema`.
- [x] Response parsing: collect `item/agentMessage/*` plus `turn/completed` into the standard provider result shape with actionable turn-failure errors.
- [x] Tests: added unit coverage for factory routing, launch override construction, successful structured and unstructured runs, invalid structured output, and failure mapping.

## Risks & Mitigations

- Risk: the adapter starts depending on provider-specific response text formatting.
  Mitigation: treat `outputSchema` as the structured-output contract and keep text parsing only as a fallback path.
- Risk: system-prompt behavior accidentally persists between runs.
  Mitigation: pass `developer_instructions` at process startup, not by writing to the user's Codex config.

## Validation / QA Plan

- `PYTHONPATH=src pytest tests/unit -q -k "codex or architect"`
- `ruff check src tests`
- `pyright`

## Changelog

- 2026-03-08: Milestone created.
- 2026-03-08: Implemented `CodexArchitect`, structured `outputSchema` handling, app-server turn parsing, factory routing, and Codex architect unit coverage; validated with targeted and full unit/lint/type checks plus a live unauthenticated architect smoke.
