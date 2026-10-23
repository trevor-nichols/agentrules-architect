---
id: EP-20261023-001/MS008
execplan_id: EP-20261023-001
ms: 8
title: "Validate integration and release readiness"
status: planned
domain: cross-cutting
owner: "@codex"
created: 2026-10-23
updated: 2026-10-23
tags: [integration, qa, rollout, defaults]
risk: med
links:
  issue: ""
  docs: "docs/provider-model-audit-2026-10.md"
  pr: "https://github.com/trevor-nichols/agentrules-architect/pull/42"
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

## Changelog

- 2026-10-23: Defined integration, default-evaluation, and release acceptance.
