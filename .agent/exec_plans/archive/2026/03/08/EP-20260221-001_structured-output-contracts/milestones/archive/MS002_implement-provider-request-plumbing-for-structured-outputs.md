---
id: EP-20260221-001/MS002
execplan_id: EP-20260221-001
ms: 2
title: "Implement provider request plumbing for structured outputs"
status: completed
domain: cross-cutting
owner: "@codex"
created: 2026-02-21
updated: 2026-02-21
tags: [providers, plumbing]
risk: med
links:
  issue: ""
  docs: "internal-docs/integrations"
  pr: ""
---

# Implement provider request plumbing for structured outputs

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Thread structured output request settings through each provider adapter so phase-level contracts can be requested in a provider-appropriate way.

## Definition of Done

- [x] OpenAI request path supports `text.format` structured schema (Responses API).
- [x] Anthropic request path supports `output_config.format`.
- [x] Gemini path supports `response_mime_type=application/json` + `response_json_schema`.
- [x] DeepSeek/xAI paths support documented fallback mode (`response_format` json object when available).
- [x] Existing non-structured behavior remains backward compatible.

## Scope

### In Scope
- Update provider request builders/architect helpers to accept structured-output settings.
- Keep provider conversion centralized, phase-aware, and serializable.

### Out of Scope
- Phase 2 parser integration and behavior changes (MS003).
- Broad prompt rewrites for all phases.

## Workstreams & Tasks

- [x] Workstream A: Add provider-agnostic structured output config type.
- [x] Workstream B: Implement provider-specific request payload translation.
- [x] Workstream C: Add provider-level unit tests for payload construction.

## Risks & Mitigations

- Risk: Provider SDK incompatibility for new fields can break runtime requests.
  Mitigation: Add additive optional fields and preserve existing request body shapes.

## Validation / QA Plan

- `PYTHONPATH=src .venv/bin/pytest tests/unit/agents -k \"request_builder or structured\"`
- `PYTHONPATH=src .venv/bin/pytest tests/unit -k \"phase2 or parser\"`

## Changelog

- 2026-02-21: Milestone created.
- 2026-02-21: Defined concrete provider-plumbing outcomes.
- 2026-02-21: Wired OpenAI, Anthropic, Gemini, DeepSeek, and xAI architect/request paths to phase-aware structured output settings.
- 2026-02-21: Added request-builder coverage for OpenAI, Anthropic, DeepSeek, and xAI structured payload fields; milestone completed.
