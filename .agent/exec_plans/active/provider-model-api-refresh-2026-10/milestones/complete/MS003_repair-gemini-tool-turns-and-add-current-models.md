---
id: EP-20261023-001/MS003
execplan_id: EP-20261023-001
ms: 3
title: Repair Gemini tool turns and add current models
status: completed
domain: cross-cutting
owner: '@codex'
created: 2026-10-23
updated: '2026-10-23'
tags:
- gemini
- tools
- sdk
- capabilities
risk: high
links:
  issue: ''
  docs: docs/provider-model-audit-2026-10.md
  pr: https://github.com/trevor-nichols/agentrules-architect/pull/42
---

# Repair Gemini tool turns and add current models

This milestone is a living document under `.agent/PLANS.md`. Begin only after plan approval; update parent Progress and any changed upstream facts.

## Objective

A Gemini researcher function call completes a valid second turn, and Gemini 3.8 Flash/4 Argon choices respect their different thinking and token budgets.

## Definition of Done

- Parser preserves Gemini model content, thought signatures, function-call ID/name/args, and matched function-response ID/name in the following request.
- A deterministic two-turn researcher test passes before new Gemini models are exposed for tool use.
- Gemini 3.8 Flash and 4 Argon presets reject minimal/disabled thinking before dispatch; output/input limits reflect Flash's separate input cap and Argon's shared window.
- `google-genai` floor is at least 2.30.1, `uv.lock` is regenerated and checked, and local stubs match only used SDK APIs.
- Focused tests, ruff, pyright, import smoke, and docs pass.

## Scope

### In Scope
- `src/agentrules/core/analysis/phase_1.py`, `src/agentrules/core/agents/gemini/{response_parser,client,tooling,capabilities,architect}.py`, `src/agentrules/config/agents.py`, presets, `pyproject.toml`, `uv.lock`, and `typings/google/genai/types.pyi`.
- Both synchronous `models.generate_content` and the existing pipeline's actual tool-loop flow; use the SDK's supported continuation path for Argon.

### Out of Scope
- A migration to Interactions API, a global increase in output budgets, and non-researcher tool framework redesign.

## Workstreams & Tasks

- Capture before-state with a fake Gemini tool response; trace `phase_1.py` and parser to identify state loss.
- Preserve provider-native content and call identity through the second turn; validate matching IDs/names and error on malformed result.
- Revalidate 3.8/4 model cards, add exact profiles and picker labels, and calculate Argon input from its shared total including thinking/output.
- Upgrade SDK floor/lock and type stub, then assert the selected SDK supports continuation.
- Add behavior tests for full exchange, disallowed thinking, budgets, and alias disclosures from MS001.

## Risks & Mitigations

- Risk: Text-only tool feedback drops thought signatures and breaks a later call. Mitigation: assert the complete second request, including original model content and function response identity.
- Risk: Argon's 1M shared window is treated as 1M input. Mitigation: assert reservations for thinking/output in effective packing.
- Risk: SDK upgrade changes payload types. Mitigation: upgrade lock and stubs together, run pyright and a fake-client exchange.

## Dependencies

MS001 Gemini lifecycle/alias corrections. MS002's explicit input-budget conventions should be reused, not reimplemented.

## Validation / QA Plan

- From repository root run `.venv/bin/pytest -q tests/unit/agents/test_gemini_capabilities.py tests/unit/agents/test_gemini_agent_parsing.py tests/unit/test_agents_gemini_error.py` plus phase-1 researcher tests found with `rg -n 'function_call|researcher' tests/unit`.
- Run `uv lock --check`, `.venv/bin/ruff check .`, `.venv/bin/pyright`, import smoke, and `git diff --check`. Expect no network calls in unit tests.
- Before/after check: the fake model's tool call with ID and thought signature appears with matching structured function response on turn two; disabled thinking raises before the fake client is called.

## Rollout / Ops Notes

Expose 3.8/4 researcher choices only after continuation tests pass. If SDK upgrade fails, revert `pyproject.toml` and `uv.lock` together and keep new Argon presets unavailable.

## Changelog

- 2026-10-23: Defined two-turn Gemini and Argon dependency gates.
- 2026-10-23: Started after MS002. Revalidated official model and GenerateContent guides; Argon model card lists a 65,536 synchronous SDK generation cap with automatic continuation, while a single non-streaming API hop remains capped at 32,768. The implementation will follow the SDK contract and reserve the requested thinking/output budget within the shared window.
- 2026-10-23: Completed signed two-turn tool continuation, strict call-ID handling across Gemini 3.x/4, 3.8 Flash and 4 Argon presets and budgets, SDK 2.33.0 lock and minimal stubs, and lifecycle docs. Bugbot findings on tool-only replies, legacy 3.x IDs, and JSON-safe results were fixed. Full offline suite passed (1,046 tests, 57 subtests); ruff, pyright, import smoke, lock check, and diff check passed.
