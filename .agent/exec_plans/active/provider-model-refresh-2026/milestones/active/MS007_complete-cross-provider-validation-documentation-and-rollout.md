---
id: EP-20260715-001/MS007
execplan_id: EP-20260715-001
ms: 7
title: "Complete cross-provider validation documentation and rollout"
status: planned
domain: cross-cutting
owner: "@codex"
created: 2026-07-15
updated: 2026-07-15
tags: [integration, validation, documentation, rollout]
risk: med
links:
  issue: ""
  docs: ".agent/exec_plans/active/provider-model-refresh-2026/EP-20260715-001_provider-model-refresh-2026.md"
  pr: ""
---

# Complete cross-provider validation documentation and rollout

This milestone is a living document. Keep the YAML front matter accurate, update this file as work proceeds, and record material revisions in `Changelog`.

## Objective

Prove that the provider refresh works as one coherent release, not merely as seven sets of passing unit tests. Resolve cross-provider enum and SDK interactions, make every operator-facing model list and lifecycle statement accurate, capture optional live evidence safely, and leave the repository importable, lint-clean, type-clean, fully tested, and recoverable.

## Definition of Done

- [ ] Repository-wide searches find no unintended stale defaults, dead wire identifiers, invalid context assumptions, or documentation that contradicts the final model registry.
- [ ] `pyproject.toml`, `uv.lock`, and the synchronized environment agree on OpenAI, Anthropic, Google GenAI, and Claude Agent SDK requirements.
- [ ] A provider/model compatibility test matrix covers every newly added canonical model, compatibility redirect, reasoning/thinking mode, context limit, and local-runtime selection mode.
- [ ] The full pytest suite, import smoke, Ruff, Pyright, offline pipeline smoke, prompt template validation, and all existing required CI-equivalent checks pass.
- [ ] Optional direct-provider live smokes are credential- and flag-gated, use minimal token limits, redact secrets/responses, and skip by default; Codex and Claude Code live paths remain aligned with their docs.
- [ ] `README.md`, provider/runtime docs, release-facing guidance, and `AGENTS.md` are updated wherever architecture or lifecycle rules materially changed.
- [ ] `SNAPSHOT.md` is synchronized and an immediate second sync produces no diff.
- [ ] Every milestone file and the parent ExecPlan contain final evidence and outcomes; completed milestones are moved with the CLI and the registry is updated.
- [ ] Rollout notes list changed defaults, preserved keys, redirected keys, availability caveats, and a tested rollback/fallback model for every provider.

## Scope

### In Scope

- Search all source, tests, fixtures, docs, examples, and templates for affected model IDs and default descriptions.
- Consolidate dependency changes after the provider milestones, run `uv lock`, run `uv sync --extra dev`, and rerun OpenAI-compatible plus Claude runtime suites.
- Add or extend a parameterized model contract test that verifies registry membership, provider, reasoning mode, context limit, and request builder behavior without network calls.
- Add a narrowly scoped `tests/live/test_provider_model_live_smoke.py` only if direct-provider live coverage does not already have a suitable home. Gate each provider independently with `AGENTRULES_RUN_<PROVIDER>_LIVE=1`, `pytest --run-live`, and the provider key.
- Update `docs/claude-code-runtime.md`, `docs/codex-runtime.md`, general model/provider documentation, and user-visible CLI help. Add a concise current-model/lifecycle section instead of duplicating provider documentation across many files.
- Update `AGENTS.md` with lasting architectural rules discovered during implementation, such as explicit provider capability metadata, saved-key compatibility redirects, direct-versus-runtime model ownership, and fail-closed runtime minimum gates.
- Run snapshot and ExecPlan registry tooling and record exact command output in the plan.

### Out of Scope

- Publishing a release, pushing the branch, opening a PR, or merging without a separate user request.
- Running paid live requests automatically or requiring live results for CI.
- Addressing unrelated pre-existing lint/test failures by broad refactor. Any baseline issue must be recorded and isolated.
- Removing legacy presets whose upstream models still work unless an earlier milestone explicitly defines a compatibility redirect.
- Adding monitoring or scheduled automation for future provider releases.

## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Focused baseline | Healthy | 129 provider/model tests passed before implementation. |
| Cross-provider integration | Pending | Shared enum and SDK changes will span several milestones. |
| Documentation | Pending | Current docs predate most July model changes. |
| Rollout evidence | Pending | Must be captured after implementation, not inferred from plans. |

## Architecture / Design Snapshot

Validation has three layers. Contract tests prove deterministic request and response behavior without credentials. Repository-wide integration gates prove imports, typing, style, templates, snapshots, and the offline pipeline. Optional live smokes prove that an account can resolve a current model identifier and return a minimal response; they do not replace contract tests because availability is account- and region-specific.

Prefer one parameterized compatibility matrix over repeated fixture-shaped assertions. Each row should identify provider, preset key, expected wire model, expected reasoning/thinking behavior, context limit, and whether the key is canonical, pinned runtime, moving runtime, deprecated, or redirected. Provider-specific tests still own detailed payloads.

Dependency validation must include downstream transports. An OpenAI SDK change is not complete until direct OpenAI, DeepSeek, and xAI pass. A Claude Agent SDK change is not complete until the bundled executable version, Claude Code requests, CLI diagnostics, and the gated live-smoke skip path all pass.

## Workstreams & Tasks

### Workstream A - Cross-provider consistency

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| A1 | Search | Audit stale IDs, defaults, descriptions, limits, and fixtures. | Planned |
| A2 | Matrix | Add a parameterized provider/preset compatibility contract. | Planned |
| A3 | Dependencies | Finalize constraints/lock and revalidate shared SDK consumers. | Planned |
| A4 | Regression | Run full deterministic test, lint, type, and offline gates. | Planned |

### Workstream B - Live and operator proof

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| B1 | Direct live | Add minimal independently gated provider smokes if useful. | Planned |
| B2 | Runtime live | Align Codex/Claude Code smoke instructions with actual behavior. | Planned |
| B3 | Redaction | Verify logs contain no keys, authorization headers, or raw sensitive responses. | Planned |
| B4 | Availability | Record account/region/ZDR skips separately from contract errors. | Planned |

### Workstream C - Documentation and closure

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| C1 | User docs | Document current defaults, model roles, aliases, pins, and retirements. | Planned |
| C2 | Maintainer docs | Update AGENTS architecture/lifecycle guidance. | Planned |
| C3 | Snapshots | Synchronize and prove idempotence. | Planned |
| C4 | ExecPlan | Record outcomes, complete milestones, and update registry. | Planned |

## Dependencies

- MS001 through MS006 must be implemented and individually green.
- The user must approve implementation before this milestone begins; branch planning alone is not approval.
- Live smokes depend on explicit user/operator credentials and account availability but are optional by design.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Focused tests pass while shared enum or SDK changes break another provider. | High | Run the compatibility matrix and full suite after the final lock refresh. |
| Live tests leak credentials or create unexpected spend. | High | Triple gate, minimal output cap, redacted logging, and default skip. |
| Documentation lists models that a runtime/account cannot access. | Medium | Distinguish direct catalog facts from runtime/account-dependent availability. |
| Snapshot or registry generation creates noisy unrelated changes. | Medium | Inspect diffs, rerun idempotently, and preserve comments with supported CLI commands. |
| Plan is marked complete without recorded behavior. | Medium | Require command transcripts, exact test count, and milestone completion through the CLI. |

## Validation / QA Plan

Run from the repository root after the final dependency sync:

    .venv/bin/python -c "import agentrules; print(agentrules.__file__)"
    .venv/bin/python -m pytest -q
    .venv/bin/ruff check src tests
    .venv/bin/pyright
    .venv/bin/agentrules snapshot sync
    git diff --check
    .venv/bin/agentrules snapshot sync
    .venv/bin/agentrules execplan-registry update

Also run the repository's explicit offline pipeline smoke and prompt/template validation tests discovered from CI configuration. Record their exact commands and results in this file rather than assuming the full suite makes separate jobs redundant.

Run live files without credentials to prove safe skips. Run a real provider smoke only with explicit operator opt-in. Green means deterministic gates exit zero, the second snapshot sync changes nothing, registry paths/statuses are correct, and default live execution reports skips rather than failures or network calls.

## Rollout / Ops Notes

Release notes must call out the DeepSeek hard migration, GPT-5.6 Sol new default, generic Opus move to 4.8, xAI constructor move to Grok 4.5, Gemini key redirects, and the distinction between moving and pinned runtime choices. List GPT-5.5, Claude Opus 4.8, Grok 4.3, Gemini 3.5 Flash, and runtime-default sentinels as immediate fallbacks where relevant.

If a release issue appears, select a retained previous preset before reverting the whole branch. Revert by milestone because each provider slice is independently tested. Never roll DeepSeek back to a retired identifier after July 24 or generic Opus back to Opus 4.1 after August 5. Do not publish, push, or open a PR until the user separately authorizes those external actions.

## Changelog

- 2026-07-15 — Created milestone scaffold.
- 2026-07-15 — Added the cross-provider matrix, dependency, full-validation, live-smoke, documentation, rollout, rollback, snapshot, and ExecPlan closure requirements.
