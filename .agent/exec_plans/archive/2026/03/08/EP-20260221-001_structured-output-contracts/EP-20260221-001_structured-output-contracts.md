---
id: EP-20260221-001
title: Structured outputs contracts across analysis phases
status: archived
kind: refactor
domain: cross-cutting
owner: '@codex'
created: 2026-02-21
updated: '2026-03-08'
tags:
- structured-outputs
- schemas
- providers
touches:
- agents
- cli
- tests
- docs
risk: med
breaking: false
migration: false
links:
  issue: ''
  pr: ''
  docs: internal-docs/integrations
depends_on: []
supersedes: []
---

# EP-20260221-001 - Structured outputs contracts across analysis phases

This ExecPlan is a living document. Keep `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` up to date as work proceeds. This plan follows `.agent/PLANS.md`.

## Purpose / Big Picture

The current pipeline mostly relies on plain text outputs, especially in Phase 2 where a free-form XML plan must be repaired and parsed with fallbacks. This introduces fragility and provider-specific behavior drift. After this change, every analysis phase will have a concrete JSON schema contract, and provider adapters will know exactly how to request structured outputs (or fallback safely when a provider cannot guarantee schema conformance).

A user should be able to run the existing analysis workflow and get the same outputs, but with more deterministic phase handoffs. For Phase 2 specifically, when structured output is enabled, agent allocations should arrive as schema-valid JSON and bypass brittle XML recovery paths.

## Scope

In scope:
1. Define concrete schema contracts for Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, and Final Analysis.
2. Define provider mapping rules for OpenAI, Anthropic, Gemini, DeepSeek, and xAI using docs in `internal-docs/integrations/*/structured-outputs.md`.
3. Implement provider request plumbing that can inject structured-output settings.
4. Integrate Phase 2 to consume structured outputs first, with existing parsing as fallback.
5. Add focused tests for schema helpers and Phase 2 structured plan extraction.

Out of scope:
1. Rewriting all Phase 1 agent prompts to fully machine-only payloads in this pass.
2. Removing legacy parsing code paths entirely.
3. Large UI/CLI redesigns.

## Progress

- [x] (2026-02-21 12:08Z) Created ExecPlan and milestone scaffolding via CLI (`execplan new`, `milestone new`).
- [x] (2026-02-21 12:13Z) Completed plan detailing with scope, milestones, risks, and validation strategy.
- [x] (2026-02-21 16:20Z) Implemented shared schema contract + provider mapping module at `src/agentrules/core/utils/structured_outputs.py`.
- [x] (2026-02-21 16:50Z) Wired structured output request plumbing for OpenAI, Anthropic, Gemini, DeepSeek, and xAI architect/request paths.
- [x] (2026-02-21 17:05Z) Integrated Phase 2 to parse from full response payload first and preserve legacy text/XML fallback.
- [x] (2026-02-21 17:10Z) Added/updated tests for schema helpers, request builders, and Phase 2 payload handoff.
- [x] (2026-02-21 17:11Z) Ran targeted pytest, ruff, and pyright validation for changed scope.
- [x] (2026-02-21 17:11Z) Added human-readable contract doc at `docs/structured-output-contracts.md`.
- [x] (2026-02-21 17:28Z) Addressed review hardening: OpenAI strict-schema normalization + Phase 2 pre-parsed agent validation/fallback.
- [x] (2026-02-21 17:43Z) Addressed review hardening: Anthropic `output_config.format` now capability-gated with plain-text fallback for unsupported model families (e.g. Opus 4.1).
- [x] (2026-02-21 17:54Z) Addressed review hardening: Gemini phase 5 consolidation now disables tools to prevent function-call-only responses from degrading consolidated report output.
- [x] (2026-02-21 18:06Z) Addressed review hardening: Phase 2 parser now normalizes non-string `plan` payloads and accepts schema-valid pre-parsed agents with empty `file_assignments`.
- [x] (2026-02-21 18:13Z) Addressed review hardening: Gemini phase-schema requests now gate schema+tools combinations by model capability (non-Gemini-3 disables tools for phase request).

## Milestones

### MS001 - Define phase schemas and provider mapping design

Deliver a versioned schema contract module for all phases and provider mapping metadata that describes request knobs and reliability level per provider.

### MS002 - Implement provider request plumbing for structured outputs

Thread structured-output configuration through provider request builders (OpenAI Responses, Anthropic output_config.format, Gemini response_json_schema, DeepSeek json_object mode, xAI fallback mode).

### MS003 - Integrate Phase 2 parser pipeline and add tests

Make Phase 2 consume structured plan payloads first, preserve fallback parsing, and add tests to lock behavior.

## Surprises & Discoveries

- Observation: The repository already has robust ExecPlan + milestone CLI support and registry automation, so we can follow the process without custom scripting.
  Evidence: `python -m agentrules execplan --help` and successful creation of `EP-20260221-001`.
- Observation: Provider adapters currently normalize response keys (`plan`, `analysis`, `report`) but do not pass schema parameters in request builders.
  Evidence: `src/agentrules/core/agents/*/request_builder.py` lacks structured output config fields.
- Observation: DeepSeek JSON output reliability depends strongly on prompt instructions in addition to `response_format={"type":"json_object"}`.
  Evidence: `internal-docs/integrations/deepseek/structured-outputs.md` explicitly requires including the word "json" and example format guidance.
- Observation: Phase 2 parser already supports dict inputs with pre-parsed `agents`, so integration only required handing the full response object through.
  Evidence: `parse_agents_from_phase2(input_data)` checks `if isinstance(input_data, dict)` and returns `input_data["agents"]` when present.
- Observation: OpenAI strict mode rejects schemas unless object properties are fully required and `additionalProperties` is false.
  Evidence: `internal-docs/integrations/openai/structured-outputs.md` sections “All fields must be required” and “additionalProperties: false must always be set in objects”.
- Observation: Anthropic structured JSON outputs are only supported on newer Claude 4.5/4.6/Haiku 4.5 families, not legacy Opus 4.1.
  Evidence: `internal-docs/integrations/anthropic/structured-outputs.md` model support statement.
- Observation: Gemini consolidation is especially sensitive to tool-enabled runs because tool calls can legitimately arrive without user-facing text payload.
  Evidence: provider parser behavior in `src/agentrules/core/agents/gemini/response_parser.py` plus regression test `test_consolidation_disables_tools_even_when_configured`.
- Observation: Non-strict provider `json_object` payloads may deliver `plan` as an object rather than string, which must be normalized before markdown/XML parser stages.
  Evidence: parser pipeline previously expected `str` in `extract_from_markdown_block` and regex/XML helpers.
- Observation: Gemini supports structured-output-plus-tools only on Gemini 3 preview family; combining both on 2.5 models can fail request validation.
  Evidence: `internal-docs/integrations/gemini/structured-outputs.md` preview support note plus regression tests in `tests/unit/agents/test_gemini_agent_parsing.py`.

## Decision Log

- Decision: Implement structured output as additive opt-in plumbing with fallbacks, not hard cutover.
  Rationale: Avoid regressions across providers with differing structured-output guarantees.
  Date/Author: 2026-02-21 / @codex
- Decision: Prioritize Phase 2 operational integration first because it is the highest-value handoff and currently uses brittle XML parsing.
  Rationale: Phase 2 output directly controls Phase 3 agent/file assignment.
  Date/Author: 2026-02-21 / @codex
- Decision: Keep logical phase contracts provider-agnostic, then compile to strict schema specifically for OpenAI request payloads.
  Rationale: Preserves shared contracts across providers while meeting OpenAI strict subset requirements.
  Date/Author: 2026-02-21 / @codex

## Outcomes & Retrospective

Implemented a concrete schema contract module for every phase, introduced provider-specific structured-output request mapping, and wired all provider adapters to request structured output for phase calls where schema enforcement is enabled (`phase2`, `phase4`, `phase5`, `final`). The pipeline now uses structured Phase 2 agent payloads directly when present and falls back to XML/text recovery without breaking legacy behavior.

Validation passed across targeted suites:

- `PYTHONPATH=src .venv/bin/pytest tests/unit/agents/test_openai_helpers.py tests/unit/agents/test_anthropic_request_builder.py tests/unit/agents/test_deepseek_helpers.py tests/unit/agents/test_xai_helpers.py tests/unit/utils/test_structured_outputs.py tests/unit/test_phase_events.py`
- `PYTHONPATH=src .venv/bin/pytest tests/unit/agents tests/unit/test_phases_edges.py tests/phase_2_test/test_phase2_offline.py`
- `PYTHONPATH=src .venv/bin/ruff check <changed files>`
- `PYTHONPATH=src .venv/bin/pyright src/agentrules/core/agents/deepseek/architect.py src/agentrules/core/agents/xai/architect.py src/agentrules/core/agents/xai/request_builder.py src/agentrules/core/analysis/phase_2.py src/agentrules/core/utils/structured_outputs.py`
