---
id: EP-20261023-001/MS007
execplan_id: EP-20261023-001
ms: 7
title: "Evaluate optional provider API migrations"
status: planned
domain: cross-cutting
owner: "@codex"
created: 2026-10-23
updated: 2026-10-23
tags: [api, spike, migration, decision]
risk: med
links:
  issue: ""
  docs: "docs/provider-model-audit-2026-10.md"
  pr: "https://github.com/trevor-nichols/agentrules-architect/pull/42"
---

# Evaluate optional provider API migrations

This milestone is a living document under `.agent/PLANS.md`. This is a bounded design and contract investigation, not permission to migrate production transports.

## Objective

The team has an evidence-backed go/no-go for each optional API migration and knows its exact implementation and rollback scope before changing transports.

## Definition of Done

- xAI Chat versus Responses, Anthropic current SDK versus 2.x/API 2026-10-21, and Gemini GenerateContent versus Interactions each have a dated official-source comparison.
- Small isolated offline probes cover request, tool response, streaming, structured output, auth/gateway, and parser effects where applicable; no production transport switches are made by this milestone.
- Parent Decision Log records go/no-go, user-visible gain, required dependency/version, risk, rollback, and follow-up for each.
- Any go decision requiring production migration becomes a separately reviewable ExecPlan amendment/milestone before implementation; a supported no-go with tests is a valid completion.

## Scope

### In Scope
- Read-only source review and disposable or test-only probes around `src/agentrules/core/agents/{xai,anthropic,gemini}`, plus a migration decision record in the parent plan and lifecycle docs if operator guidance changes.
- Confirm OpenAI Responses and DeepSeek Chat remain documented for their current text pipeline.

### Out of Scope
- Production xAI Responses, Anthropic 2.x, or Gemini Interactions adoption without a separate scope, test matrix, rollback, and review.

## Workstreams & Tasks

- Recheck official migration guides and installed SDK capabilities; capture date and minimum versions.
- Exercise representative fake request and stream/tool/structured-output paths, distinguishing documentation claims from tested current code.
- Record a decision per provider: required now, beneficial later, or no current benefit; state exact trigger to revisit.
- If required now, amend parent scope and create a reviewable implementation milestone before code migration.

## Risks & Mitigations

- Risk: A model addition is coupled to a transport rewrite unnecessarily. Mitigation: keep currently documented endpoint contract green and require a demonstrated missing capability for migration.
- Risk: Anthropic SDK 2.x changes auth header or `output_config` behavior through a gateway. Mitigation: include gateway/header and structured-output probe in decision record.

## Dependencies

MS003–MS005 provider contract tests establish the current baseline. This milestone does not block their model exposure when current endpoints are documented and pass.

## Validation / QA Plan

- From repository root run focused existing request/parser tests for xAI, Anthropic, and Gemini and any small probe tests added here. Run `.venv/bin/ruff check .`, `.venv/bin/pyright`, and `git diff --check` for retained probes.
- Before/after check: a reviewer can read three dated decisions with evidence and can tell exactly why the current transport stays or what separate migration must be reviewed. No production request builder changes should appear in this milestone diff.

## Rollout / Ops Notes

No deployment effect. Dispose of throwaway probes or retain only meaningful contract tests. If an upstream endpoint becomes mandatory during execution, pause that provider slice and amend the parent plan before adopting it.

## Changelog

- 2026-10-23: Defined optional API migration decision gates and scope boundary.
