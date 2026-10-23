---
id: EP-20261023-001/MS004
execplan_id: EP-20261023-001
ms: 4
title: Add Anthropic 5.5 models and refusal handling
status: completed
domain: cross-cutting
owner: '@codex'
created: 2026-10-23
updated: '2026-10-23'
tags:
- anthropic
- thinking
- refusals
- lifecycle
risk: high
links:
  issue: ''
  docs: docs/provider-model-audit-2026-10.md
  pr: https://github.com/trevor-nichols/agentrules-architect/pull/42
---

# Add Anthropic 5.5 models and refusal handling

This milestone is a living document under `.agent/PLANS.md`. Start after plan approval; keep parent Progress accurate.

## Objective

Users can choose reviewed Claude 5.5/Fable 5.1 direct API profiles, with thinking and retention made explicit, while a refusal is handled as a refusal even when HTTP status is 200.

## Definition of Done

- Revalidate exact Anthropic model IDs, thinking modes, refusal stop reason, retention, and Sonnet 4.5 retirement.
- Opus/Sonnet/Haiku 5.5 and Fable 5.1 profiles send accepted model-specific thinking and structured-output payloads; unsupported combinations fail before dispatch.
- A 200 refusal and partial streamed refusal cannot be returned as successful analysis.
- Fable's 30-day retention is visible in picker/docs; Sonnet 4.5 compatibility keys preserve the live wire model until retirement and then use an explicit one-hop 5.5 replacement.
- Retired Claude 3.5 Sonnet prompt reference is removed; synchronous direct SDK call is off the event loop; focused and shared gates pass.

## Scope

### In Scope
- `src/agentrules/core/agents/anthropic/{capabilities,request_builder,response_parser,architect,client}.py`, direct presets and lifecycle metadata, `src/agentrules/config/prompts/final_analysis_prompt.py`, picker labels, and docs.
- Opus 5.5/Fable 5.1 adaptive thinking; Sonnet 5.5 without disabled thinking; Haiku 5.5 disabled only at low/medium/high. Respect current verified SDK semantics.

### Out of Scope
- Restricted Mythos 5.1, silent Sonnet 4.5 redirect before retirement, and the Anthropic SDK 2.x/API version migration evaluated in MS007.

## Workstreams & Tasks

- Extend one capability registry with exact per-model thinking, tool, structured-output, and refusal metadata.
- Validate request shape before SDK dispatch and preserve current working structured output behavior.
- Extend typed parser/stream buffer so refusal stop reason is visible and a partial stream cannot pass as final success.
- Add retention/lifecycle labels, prompt cleanup, and off-loop SDK call with failure tests.
- Add fake-client contracts for each family and forbidden combination, plus saved-key behavior.

## Risks & Mitigations

- Risk: Fable is selected under a zero-data-retention assumption. Mitigation: make retention explicit in picker and lifecycle docs, and test its label.
- Risk: A refusal returns HTTP 200 and partial text. Mitigation: assert stop reason and reject partial success at both stream and final parse.
- Risk: SDK offloading changes exception handling. Mitigation: verify exceptions propagate to existing pipeline error contract.

## Dependencies

MS001 source revalidation and lifecycle conventions. MS007 separately decides Anthropic API migration; this milestone may use the current client.

## Validation / QA Plan

- From repository root run `.venv/bin/pytest -q tests/unit/agents/test_anthropic_capabilities.py tests/unit/agents/test_anthropic_request_builder.py tests/unit/agents/test_anthropic_agent_parsing.py tests/unit/agents/test_anthropic_client_compat.py`.
- Run `.venv/bin/ruff check .`, `.venv/bin/pyright`, import smoke, and `git diff --check`. Expect a fake 200 refusal to produce an explicit provider refusal error, not output text.
- Before/after check: picker shows Fable retention and old Sonnet 4.5 saved key keeps Sonnet 4.5 while live.

## Rollout / Ops Notes

Keep prior Opus/Haiku choices as explicit rollback options. If exact model or retention claims change upstream, pause this slice and update the parent plan before exposing it.

## Changelog

- 2026-10-23: Defined direct Anthropic thinking, refusal, retention, and lifecycle acceptance.
- 2026-10-23: Added four current direct profiles with exact thinking and input/output limits; buffered new-model streams until final refusal status, moved synchronous token preflight, packing, and message calls off the event loop, and scheduled one-hop Sonnet 4.5 retirement routing. Full offline suite: 1,073 passed, 11 opt-in skips, 57 subtests; ruff, pyright, import smoke, and diff checks passed. Bugbot's picker-label findings were fixed and follow-up review found no remaining actionable issues.
