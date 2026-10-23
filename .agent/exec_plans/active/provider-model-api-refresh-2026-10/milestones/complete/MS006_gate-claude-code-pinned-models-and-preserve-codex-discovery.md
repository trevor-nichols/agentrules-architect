---
id: EP-20261023-001/MS006
execplan_id: EP-20261023-001
ms: 6
title: Gate Claude Code pinned models and preserve Codex discovery
status: completed
domain: cross-cutting
owner: '@codex'
created: 2026-10-23
updated: '2026-10-23'
tags:
- claude-code
- codex
- runtime
- sdk
risk: high
links:
  issue: ''
  docs: docs/provider-model-audit-2026-10.md
  pr: https://github.com/trevor-nichols/agentrules-architect/pull/42
---

# Gate Claude Code pinned models and preserve Codex discovery

This milestone is a living document under `.agent/PLANS.md`. Begin after approval and keep parent Progress current.

## Objective

Pinned Claude Code models run only on a sufficiently new, exactly resolved executable, while Codex continues to use its live app-server catalog.

## Definition of Done

- Pinned Fable 5.1, Opus 5.5, Sonnet 5.5, and Haiku 5.5 select only with exact executable versions ≥2.1.257, ≥2.1.280, ≥2.1.284, and ≥2.1.293 respectively; old or unversionable executable fails before launch.
- Longer specific IDs are matched before older `*-5` prefixes; moving `best`/`opus`/`sonnet`/`fable` aliases remain runtime-owned, with `haiku` added only if supported.
- Claude Agent SDK floor and `uv.lock` bundle a compatible Claude Code runtime; runtime version is taken from the executable actually used, not a global binary.
- Codex fake app-server discovery still accepts runtime model/effort output, uses `outputSchema`, and has no static GPT-6 Codex preset.
- Focused tests, lock check, ruff, pyright, import smoke, and docs pass.

## Scope

### In Scope
- `src/agentrules/core/configuration/services/claude_code.py`, `src/agentrules/core/agents/claude_code/`, presets/picker, `pyproject.toml`, `uv.lock`, and Codex boundary regression tests for `codex/{client,model_selection,request_builder}.py`.
- Current direct API and runtime catalogs remain distinct. Update `docs/codex-runtime.md` only if a real runtime workflow changes.

### Out of Scope
- Static GPT-6 Codex entries, inferred availability from direct API deprecations, and replacement of moving Claude Code aliases by pinned IDs.

## Workstreams & Tasks

- Recheck Claude Code official model/version documentation and SDK release bundled executable version.
- Fix prefix order, add exact gates and picker choices, and test both bundled and configured executable resolution.
- Upgrade Claude Agent SDK and lockfile together; validate startup and schema request with fake runtime.
- Add negative Codex registry test and dynamic fake `model/list` round trip.

## Risks & Mitigations

- Risk: A newer global `claude` masks an older SDK-bundled binary. Mitigation: query the exact resolved executable and fail closed if it cannot be versioned.
- Risk: Broad prefix matcher classifies 5.5 as older 5. Mitigation: longest/specific match first and tests for every pinned ID.
- Risk: SDK upgrade changes process options. Mitigation: fake runtime request and launch tests plus lockfile check.

## Dependencies

MS001 source revalidation. Direct Anthropic model contracts in MS004 inform labels but do not prove Claude Code availability.

## Validation / QA Plan

- From repository root run `.venv/bin/pytest -q tests/unit/agents/test_claude_code_client.py tests/unit/agents/test_claude_code_request_builder.py tests/unit/agents/test_codex_client.py tests/unit/agents/test_codex_request_builder.py tests/unit/test_codex_runtime_service.py`.
- Run `uv lock --check`, `.venv/bin/ruff check .`, `.venv/bin/pyright`, import smoke, and `git diff --check`.
- Before/after check: a 2.1.280 exact executable accepts pinned Opus 5.5 but rejects pinned Haiku 5.5; an unversionable executable rejects both; Codex displays a fake future model from `model/list` without a source-code preset.

## Rollout / Ops Notes

Keep runtime aliases for recovery. If the new SDK cannot bundle a suitable runtime, do not expose pinned choices; record the blocker and update the plan. Revert SDK constraint and lockfile as one unit if needed.

## Changelog

- 2026-10-23: Defined exact-runtime gates and Codex dynamic-catalog acceptance.
- 2026-10-23: Revalidated Claude Code model/version guidance and Claude Agent SDK 0.2.165 bundle; implementation started.
- 2026-10-23: Added exact-version gates and picker choices for four pinned models, preserved moving aliases, and upgraded Claude Agent SDK to 0.2.173 (bundled Claude Code 2.1.309). Pinned requests pass the same resolved executable to the SDK that the gate probes; on Windows, default resolution prefers a native executable over an npm cmd shim. Codex fake app-server tests cover a future discovered model, extreme effort, and structured output without a static preset. Full offline suite: 1,095 passed, 12 opt-in skips, 57 subtests; lock check, ruff, pyright, import smoke, and diff checks passed. Bugbot's Windows resolver finding was fixed and follow-up review found no remaining actionable issues.
