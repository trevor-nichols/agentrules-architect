---
id: EP-20260715-001/MS006
execplan_id: EP-20260715-001
ms: 6
title: Preserve dynamic Codex compatibility and update Gemini lifecycle
status: completed
domain: cross-cutting
owner: '@codex'
created: 2026-07-15
updated: '2026-07-15'
tags:
- codex
- gemini
- runtime-catalog
- lifecycle
risk: med
links:
  issue: ''
  docs: docs/codex-runtime.md
  pr: ''
---

# Preserve dynamic Codex compatibility and update Gemini lifecycle

This milestone is a living document. Keep the YAML front matter accurate, update this file as work proceeds, and record material revisions in `Changelog`.

## Objective

Keep Codex model and effort selection governed by the installed app-server without silently losing newly introduced safe effort labels, and make Gemini's existing model choices accurately reflect active, deprecated, redirected, and retired endpoints. This milestone adds no duplicate static Codex GPT-5.6 models and does not re-add Gemini 3.5 Flash because both are already handled correctly.

## Definition of Done

- [x] Live Codex catalog efforts `max` and `ultra` survive normalization, appear in dynamic preset choices, serialize into preset keys, and reach turn requests unchanged.
- [x] A future unknown but syntactically safe catalog effort is retained after known ordered values; malformed or untrusted values are rejected.
- [x] Codex's runtime-default sentinel continues to follow the model marked default by the installed runtime/account.
- [x] No static Codex GPT-5.6 Sol/Terra/Luna entries are added to `BASE_MODEL_PRESETS`.
- [x] Gemini 2.5 Flash and Pro labels/descriptions disclose their 2026-10-16 shutdown and recommend Gemini 3.5 Flash or 3.1 Pro as appropriate.
- [x] Saved keys for already retired/redirected Gemini preview endpoints continue to load but send their canonical active replacement model, with labels disclosing the redirect.
- [x] Stable `gemini-3.5-flash` remains unchanged and continues to use medium thinking and its existing capability profile.
- [x] Focused Codex catalog/config/CLI, Gemini capability, model-override, import, Ruff, and Pyright validation passes.

## Scope

### In Scope

- Update `src/agentrules/core/configuration/model_presets.py` so runtime effort values are normalized from catalog data instead of limited to a closed six-value literal.
- Accept only lowercase ASCII effort tokens matching a short safe shape such as `^[a-z][a-z0-9_-]{0,31}$`. Keep a preferred display order for known values `none`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max`, and `ultra`; append other safe server-provided values in server order or deterministic order.
- Update Codex request/config types and formatting helpers to carry safe runtime strings. Provider-neutral static reasoning mappings remain closed and do not invent new values.
- Extend `tests/fakes/codex_app_server.py`, catalog dataclasses if needed, and focused tests with `max`, `ultra`, and a future value such as `extreme`.
- Update `docs/codex-runtime.md` examples to show GPT-5.6 as runtime-discovered and explain that available options depend on the installed Codex build and account.
- Update Gemini preset descriptions in `src/agentrules/config/agents.py`. Redirect the `gemini-3.1-flash-lite-preview` saved key to stable `gemini-3.1-flash-lite`; redirect `gemini-3-pro-preview` to canonical `gemini-3.1-pro-preview` rather than relying on a provider-side alias. Retain key compatibility and disclose the mapping.
- Add lifecycle and picker tests. Do not introduce a broad lifecycle metadata subsystem solely for these labels.

### Out of Scope

- Static GPT-5.6 Codex configs, changing Codex authentication, or choosing a Codex default in AgentRules.
- Treating Codex `ultra` as a provider-neutral `ReasoningMode`; it remains runtime-specific.
- Adding Gemini Omni, Live, translation, image, video, embedding, or managed-agent models.
- Removing Gemini 2.5 before its shutdown date or silently redirecting a still-active explicit 2.5 selection.
- Rewriting the model picker around a new hidden/deprecated preset schema.

## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Codex model discovery | Healthy | App-server `model/list` already returns GPT-5.6 tiers and runtime default. |
| Codex capability discovery | Forward-compatible | Safe catalog efforts are validated, ordered, persisted, and dispatched unchanged. |
| Gemini current model | Healthy | Stable Gemini 3.5 Flash already exists and passes capability tests. |
| Gemini lifecycle UX | Current | Retired keys redirect and active deprecated models disclose exact shutdown guidance. |

## Architecture / Design Snapshot

Codex catalog strings are trusted only after syntactic validation. The app-server remains the semantic authority: AgentRules does not need to know what every future label means to preserve and send a value the runtime explicitly advertised. Known labels get stable human-friendly ordering; unknown safe labels remain visible with generic formatting rather than disappearing.

Gemini lifecycle work uses the existing preset label/description pattern. Keys are the persisted compatibility boundary; model names are the wire boundary. A legacy key may point to a current replacement and say so. Still-active 2.5 model names remain exact until shutdown because automatically replacing an explicit user choice early could change cost and behavior.

## Workstreams & Tasks

### Workstream A - Codex forward compatibility

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| A1 | Types | Carry validated runtime effort strings without a stale closed literal. | Complete |
| A2 | Normalization | Preserve known and future safe tokens; reject malformed values. | Complete |
| A3 | Ordering/labels | Order known values and format unknown values deterministically. | Complete |
| A4 | Request | Prove dynamic preset effort reaches `turn/start`. | Complete |

### Workstream B - Gemini lifecycle

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| B1 | Deprecation | Label 2.5 shutdown dates and replacements. | Complete |
| B2 | Redirects | Map already dead preview keys to active canonical IDs. | Complete |
| B3 | Stability | Keep 3.5 Flash config/capability behavior unchanged. | Complete |
| B4 | UX tests | Verify picker labels, keys, and model-name mappings. | Complete |

### Workstream C - Evidence and docs

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| C1 | Fixtures | Add max/ultra/future/malformed catalog cases. | Complete |
| C2 | Unit tests | Cover parse, build, serialization, and request propagation. | Complete |
| C3 | Docs | Update live-catalog and Gemini lifecycle guidance. | Complete |
| C4 | Quality | Run focused pytest, Ruff, Pyright, and import smoke. | Complete |

## Dependencies

- MS002 may add `ReasoningMode.MAX`, but Codex runtime strings remain a separate type and should not depend on that enum for catalog values.
- Existing Codex app-server fake and live smoke provide the protocol test boundary.
- Gemini changes depend only on existing configs and official lifecycle dates embedded in the parent plan.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Accepting arbitrary catalog strings creates unsafe preset keys or config corruption. | High | Strict short-token validation, deterministic encoding, and malformed fixture tests. |
| Unknown effort reaches a runtime that advertised it but another layer rejects it. | Medium | Trace the value through parse, preset key, config resolution, and request tests. |
| Static and runtime Codex choices duplicate or conflict. | Medium | Do not add GPT-5.6 statically; retain old static entries only for compatibility. |
| Legacy Gemini key still sends a shut-down endpoint. | High | Assert both persisted key and replacement wire model in tests. |
| Users mistake deprecated 2.5 for already retired. | Low | State the exact future shutdown date and keep it selectable until then. |

## Validation / QA Plan

Run from the repository root:

    .venv/bin/python -m pytest -q tests/unit/agents/test_codex_client.py tests/unit/agents/test_codex_request_builder.py tests/unit/test_codex_runtime_service.py tests/unit/test_cli_codex_settings.py tests/unit/agents/test_gemini_capabilities.py tests/unit/test_model_overrides.py tests/unit/test_cli_model_picker_ui.py
    .venv/bin/python -m pytest -q tests/live/test_codex_live_smoke.py
    .venv/bin/ruff check src/agentrules/core/configuration/model_presets.py src/agentrules/config/agents.py tests/fakes/codex_app_server.py tests/unit/agents/test_codex_client.py tests/unit/agents/test_codex_request_builder.py tests/unit/test_codex_runtime_service.py tests/unit/test_cli_codex_settings.py tests/unit/agents/test_gemini_capabilities.py tests/unit/test_model_overrides.py tests/unit/test_cli_model_picker_ui.py
    .venv/bin/pyright src/agentrules/core/configuration/model_presets.py src/agentrules/config/agents.py tests/fakes/codex_app_server.py tests/unit/agents/test_codex_client.py tests/unit/agents/test_codex_request_builder.py tests/unit/test_codex_runtime_service.py tests/unit/test_cli_codex_settings.py tests/unit/agents/test_gemini_capabilities.py tests/unit/test_model_overrides.py tests/unit/test_cli_model_picker_ui.py
    .venv/bin/python -c "import agentrules"

Green means max, ultra, and future safe values are visible and round-trip; malformed values do not; runtime default still follows the catalog; the live test skips without opt-in; legacy Gemini keys send active replacements; 2.5 choices disclose shutdown; and Gemini 3.5 Flash remains byte-for-byte equivalent in relevant request tests.

Validation evidence recorded on 2026-07-15:

- Focused Codex catalog, request, architect, runtime-service, CLI, Gemini capability, override, and picker suite: `150 passed, 5 subtests passed` across the focused runs.
- Repository-wide pytest: `820 passed, 7 skipped, 36 subtests passed in 11.08s`; four existing `pathspec` deprecation warnings remain.
- Opt-in Codex live smoke without authorization: `1 skipped in 0.89s`, as designed.
- Repository-wide Ruff: `All checks passed!`.
- Repository-wide Pyright: `0 errors, 0 warnings, 0 informations`.
- Import smoke and `git diff --check` exit zero.

## Rollout / Ops Notes

Codex behavior remains account/runtime dependent. The change exposes more of what the runtime already reports, so rollback can hide valid options and is not preferred. Gemini redirects affect only endpoints already retired or already server-redirected; still-active 2.5 selections are not changed. Release notes should list key-to-model redirects so saved-configuration behavior is auditable.

## Changelog

- 2026-07-15 — Created milestone scaffold.
- 2026-07-15 — Added forward-compatible Codex effort parsing and the exact Gemini lifecycle/compatibility migration strategy.
- 2026-07-15 — Marked the milestone in progress after MS005 passed validation, was archived, and was committed.
- 2026-07-15 — Revalidated the Codex runtime-owned catalog design against the current Codex manual and Gemini retirement/redirect dates against Google's official deprecations table.
- 2026-07-15 — Added strict runtime-effort validation, stable known-value ordering, forward-compatible string propagation, model-list fixtures, and end-to-end `turn/start` coverage.
- 2026-07-15 — Updated Gemini retirement redirects and picker lifecycle guidance while preserving active 2.5 endpoints and the existing Gemini 3.5 Flash profile.
- 2026-07-15 — Completed focused and repository-wide validation and marked the milestone complete for archival.
