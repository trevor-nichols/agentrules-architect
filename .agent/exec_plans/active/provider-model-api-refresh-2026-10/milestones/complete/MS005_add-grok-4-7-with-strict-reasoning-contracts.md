---
id: EP-20261023-001/MS005
execplan_id: EP-20261023-001
ms: 5
title: Add Grok 4.7 with strict reasoning contracts
status: completed
domain: cross-cutting
owner: '@codex'
created: 2026-10-23
updated: '2026-10-23'
tags:
- xai
- grok
- capabilities
risk: med
links:
  issue: ''
  docs: docs/provider-model-audit-2026-10.md
  pr: https://github.com/trevor-nichols/agentrules-architect/pull/42
---

# Add Grok 4.7 with strict reasoning contracts

This milestone is a living document under `.agent/PLANS.md`. Start after plan approval and revalidate the official xAI contract.

## Objective

Grok 4.7 becomes a usable direct API choice with explicit effort profiles; existing Grok choices stay available as fallbacks.

## Definition of Done

- Four Grok 4.7 presets select low/medium/high/xhigh effort and the 500K context profile; none/minimal fail before network dispatch.
- Tool and structured-output request contracts pass on current Chat Completions transport, including default high effort.
- 4.6 is labeled fallback, while 4.20 pinned variants, 4.3, and Build remain unless official retirement evidence says otherwise. Unavailable 4.7 Fast is absent.
- Focused tests, ruff, pyright, import smoke, and docs pass.

## Scope

### In Scope
- `src/agentrules/core/agents/xai/{config,request_builder,architect}.py`, `src/agentrules/config/agents.py`, presets/picker labels, lifecycle docs, and xAI tests.

### Out of Scope
- xAI Responses transport and server-side tools. MS007 evaluates those separately.

## Workstreams & Tasks

- Recheck the Grok 4.7 model card and reasoning guide for exact ID, context, effort, tools, and output contract.
- Add one strict capability profile and effort-specific presets; reject invalid requests before the fake client is called.
- Keep Chat payload and parser behavior covered by offline tool/structured-output tests.
- Update picker/default-label language and optional live-smoke model parameter without silently changing phase defaults.

## Risks & Mitigations

- Risk: Chat Completions is labeled legacy but still documented for Grok 4.7. Mitigation: contract-test the current path and reserve migration for MS007.
- Risk: Provider default effort is silently treated as disabled. Mitigation: assert high as the documented default and reject explicit none/minimal.

## Dependencies

MS001 source matrix convention. Does not depend on MS007's transport decision.

## Validation / QA Plan

- From repository root run `.venv/bin/pytest -q tests/unit/agents/test_xai_helpers.py` and existing xAI agent tests found by `rg --files tests/unit | rg 'xai'`.
- Run `.venv/bin/ruff check .`, `.venv/bin/pyright`, import smoke, and `git diff --check`.
- Before/after check: selecting Grok 4.7 xhigh sends the exact xhigh wire effort; selecting disabled fails with no fake-client call; 4.6 remains selectable.

## Rollout / Ops Notes

Keep old Grok profiles for rollback. Live smoke is optional and entitlement-dependent, so absence of access does not change offline contract results.

## Changelog

- 2026-10-23: Defined Grok 4.7 request and fallback acceptance.
- 2026-10-23: Revalidated xAI's Grok 4.7 model card, reasoning guide, and Chat Completions structured-output contract; implementation started.
- 2026-10-23: Added four Grok 4.7 presets with an immutable 500K/effort profile, preserved the direct-constructor 4.6 default pending MS008 evaluation, and set the optional live smoke to 4.7. Fake-client tests cover actual Chat tools/structured-output dispatch and unsupported-effort rejection before dispatch. Full offline suite: 1,083 passed, 12 opt-in skips, 57 subtests; ruff, pyright, import smoke, and diff checks passed. Bugbot found no actionable issues.
