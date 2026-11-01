---
id: EP-20261023-001/MS008
execplan_id: EP-20261023-001
ms: 8
title: Validate integration and release readiness
status: completed
domain: cross-cutting
owner: '@codex'
created: 2026-10-23
updated: '2026-10-31'
tags:
- integration
- qa
- rollout
- defaults
risk: med
links:
  issue: ''
  docs: docs/provider-model-audit-2026-10.md
  pr: https://github.com/trevor-nichols/agentrules-architect/pull/42
---

# Validate integration and release readiness

This milestone is a living document under `.agent/PLANS.md`. Close only after all mandatory provider slices and the API decision record are complete.

## Objective

The full provider refresh is auditable and release-ready: saved configurations, picker, requests, pipeline, docs, dependency lock, and CI agree.

## Definition of Done

- Cross-provider matrix exercises each new preset, unsupported mode, old saved key, one-hop retired/alias redirect, and default; offline pipeline smoke passes with fake providers.
- Picker/lifecycle docs/README accurately disclose effective models, deprecation dates, Fable retention, and local runtime gates; significant architecture changes are reflected in `AGENTS.md`.
- Representative project evaluation records task quality, latency, cost, and entitlement for any proposed default switch; no switch is made without evidence.
- Ruff, pyright, full offline pytest, import smoke, lock check, snapshot/registry validation, `git diff --check`, and relevant PR CI pass.
- Optional provider live smokes are run only under explicit operator environment flags; results state account/region/quota limitations, and failures are triaged.

## Scope

### In Scope
- `tests/unit/`, offline pipeline smoke, `docs/provider-model-lifecycle.md`, `README.md`, optional `AGENTS.md`, `SNAPSHOT.md` sync, ExecPlan registry, and PR review evidence.

### Out of Scope
- Raising application output caps, new modalities, forced live calls, and a default switch based only on a newer model ID.

## Workstreams & Tasks

- Audit complete preset matrix against provider capability table and lifecycle map; compare picker, config, payload, and docs.
- Run a DummyArchitect/offline pipeline smoke that covers phase output and parser paths without credentials.
- Evaluate default candidates on representative repository projects if credentials/budget are available, recording model, prompt, outcome, cost, latency, and availability.
- Run all quality/CI gates; update plan Progress, Decision Log, Outcomes, and milestone status; use CLI to complete the ExecPlan only when green.

## Risks & Mitigations

- Risk: A provider's account entitlement differs from public documentation. Mitigation: separate static contract tests from opt-in live availability results and gate unavailable choices.
- Risk: New default worsens quality or cost. Mitigation: retain existing defaults unless representative evaluation supports a change.
- Risk: Docs and registry drift after staged commits. Mitigation: inspect final diff, refresh registry/snapshots, and rerun full gates.

## Dependencies

MS001–MS007 complete, including an explicit decision for each optional API migration. Any approved production migration adds its own milestone before this one closes.

## Validation / QA Plan

- From repository root run `.venv/bin/ruff check .`, `.venv/bin/pyright`, `.venv/bin/pytest -q tests/unit`, `.venv/bin/python -c 'import agentrules; print("import ok")'`, `uv lock --check`, `.venv/bin/agentrules execplan-registry update`, and `git diff --check`. Expect all green and no unintended registry drift.
- Run `.venv/bin/agentrules snapshot sync` after file path additions/moves/removals and inspect the diff. Check import-smoke and prompt-template CI jobs on the PR.
- Before/after check: open the CLI picker or its test fixture, load an old saved config, and inspect effective wire ID; run fake-provider pipeline smoke. The new choice should be usable, and the old choice should follow the documented lifecycle.

## Rollout / Ops Notes

Release in reviewed provider slices with old explicit models available as rollback. Record any skipped live smoke and exact reason. Only after passing mandatory gates, complete each milestone and `EP-20261023-001` via the CLI; attach final evidence to PR.

## Execution Evidence

- The direct preset matrix now covers every new GPT-6, Claude 5.5/Fable 5.1, Grok 4.7, and Gemini 3.8/4 variant from saved key through request construction; 137 cases pass. Existing lifecycle and invalid-effort tests remain in the full unit suite.
- An isolated `agentrules analyze --offline` run completed Phase 1 through final analysis and wrote `AGENTS.md`, `SNAPSHOT.md`, and all phase outputs. The new CI smoke test repeats this public CLI path with a temporary Python project.
- The picker labels disclose Fable retention, Gemini aliases, and runtime ownership; DeepSeek legacy keys resolve directly to canonical Flash modes. GPT-5.6 Sol phase defaults remain in place. No provider live opt-in flag was set, so paid smokes and comparative default measurements were skipped.
- Local gates: `pytest -q tests/unit` (1,110 passed, 57 subtests), `ruff check .`, `pyright`, import smoke, and `uv lock --check` passed. PR CI for the new workflow is pending.
- The first Linux/Python 3.11 quality job found 17 portability failures outside provider adapters. Exclusion matching now uses paths relative to the project root; scaffold templates load with Python 3.11-compatible resource joins; the CLI error assertion ignores ANSI styling. The full unit suite now passes locally under locked Python 3.11 (1,111 passed, 57 subtests); PR rerun is pending.
- Review found that the new quality job ran only unit tests. It now runs `pytest -q tests --ignore=tests/live` so CI covers the full non-live phase and pipeline suites. Local `pytest -q` passed 1,158 tests with 12 opt-in live skips and 57 subtests; the updated PR run is pending.
- The expanded Linux PR workflow and lockfile check passed. Review found no further actionable defects after the quality job was expanded. Static contracts and offline integration are release-ready; live entitlement and comparative default evaluation remain unmeasured because all provider opt-in flags were unset.

## Changelog

- 2026-10-23: Defined integration, default-evaluation, and release acceptance.
- 2026-10-31: Began integrated saved-key, picker, request, pipeline, and release validation after MS001–MS007 completion.
- 2026-10-31: Added cross-provider cases, focused prompt/parser fixtures, full offline CLI smoke, and missing PR test jobs; local gates passed, PR check pending.
- 2026-10-31: Fixed Linux/Python 3.11 failures exposed by the new quality job and reproduced the complete suite in a locked 3.11 environment.
- 2026-10-31: Expanded PR quality job to the complete non-live test tree after review.
- 2026-10-31: Final PR CI and read-only review passed; milestone ready for CLI completion.
