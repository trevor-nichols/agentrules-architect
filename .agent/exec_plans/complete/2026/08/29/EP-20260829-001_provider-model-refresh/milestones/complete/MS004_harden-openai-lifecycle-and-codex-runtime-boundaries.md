---
id: EP-20260829-001/MS004
execplan_id: EP-20260829-001
ms: 4
title: Harden OpenAI Lifecycle and Codex Runtime Boundaries
status: completed
domain: cross-cutting
owner: '@codex'
created: 2026-08-29
updated: '2026-08-29'
tags:
- providers
- openai
- codex
- lifecycle
- compatibility
risk: med
links:
  issue: ''
  docs: ''
  pr: ''
---

# Harden OpenAI Lifecycle and Codex Runtime Boundaries

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Close the known OpenAI saved-preset lifecycle gaps while preserving workload intent and Codex runtime ownership. Deprecated-but-live o4-mini and GPT-5 Mini keys must remain bound to their selected endpoints while recommending effort-equivalent GPT-5.6 Terra choices. Retired direct GPT-5.1/5.2 Codex keys must resolve to GPT-5.6 Sol, static Codex compatibility selections must remain catalog-gated, and future Codex models/efforts must continue to come from app-server `model/list` rather than new static presets.

## Definition of Done

- [x] GPT-5 Mini low, medium, and high saved keys remain registered, deprecated, and bound to GPT-5 Mini until retirement.
- [x] Each o4-mini low/medium/high key remains registered and bound to o4-mini until retirement, with effort-matched GPT-5.6 Terra guidance.
- [x] Direct GPT-5.1 Codex and GPT-5.2 Codex keys remain registered and resolve to medium-effort GPT-5.6 Sol before dispatch.
- [x] Static Codex-derived GPT-5.1/5.2 compatibility keys remain bound to their original runtime model and are selectable only when app-server reports them.
- [x] GPT-5.6 Terra has low, medium, and high direct presets for effort-preserving operator migrations.
- [x] Picker labels and descriptions disclose deprecation and replacement behavior.
- [x] Codex runtime-default and runtime-catalog behavior still accepts future model IDs and safe future effort tokens.
- [x] No static Codex GPT-5.6 preset, GPT-5.5 Pro preset, or GPT-5.6 Pro-mode pseudo-preset is added.
- [x] OpenAI, lifecycle, Codex, picker, lint, type, and import tests pass offline.

## Scope

### In Scope

- GPT-5 Mini low/medium immutable configs and deprecated direct preset definitions.
- GPT-5.6 Terra low immutable config and direct preset definition.
- OpenAI compatibility metadata in `DEPRECATED_PRESETS` for o4-mini, GPT-5 Mini, retired direct Codex keys, and static Codex runtime compatibility keys.
- Lifecycle-aware labels/descriptions for legacy entries.
- Regression tests for direct OpenAI request payloads, compatibility resolution, saved overrides, static Codex compatibility, and dynamic Codex runtime discovery.
- Lifecycle notes for final documentation in MS005.

### Out of Scope

- No new GPT-5.6 direct presets beyond the Terra low effort needed to complete the approved migration matrix.
- No new static Codex presets for GPT-5.6 or any newly observed runtime model.
- No removal of legacy keys or automatic rewrite of persisted configuration files.
- No GPT-5.5 Pro support until model-specific streaming/transport capability exists.
- No GPT-5.6 Pro mode until execution mode is represented independently from model identity.
- No default phase changes, SDK upgrades, prompt migrations, pricing changes, or paid live calls.

## Current Health Snapshot

| Area | Starting state | Milestone target |
| --- | --- | --- |
| GPT-5.6 direct API | Sol/Terra/Luna presets and contracts already present | Add Terra low; retain existing Terra medium/high and all Sol/Luna behavior |
| GPT-5 Mini | One high-effort key `gpt5-mini` | Add low/medium saved keys; mark all three deprecated-but-live without runtime redirects |
| o4-mini lifecycle | Three keys present, no deprecation redirect | Preserve each live endpoint binding and recommend the matching Terra effort |
| Direct Codex API variants | 5.1 and 5.2 endpoints retired; Sol already active | Preserve saved keys and redirect both to medium-effort GPT-5.6 Sol |
| Static Codex compatibility | 5.1/5.2 saved keys predate runtime discovery | Preserve identity and expose only when the app-server catalog reports the model |
| Local Codex runtime | `model/list` generates dynamic model/effort presets | Remains authoritative and future-compatible |
| Pro variants | Current architect contract is not model-specific enough | Explicitly deferred |

## Architecture / Design

Keep `gpt5-mini` as the existing public high-effort saved key. Add `GPT5_MINI_LOW` and `GPT5_MINI_MEDIUM` via `_gpt5_responses_model()` with matching text verbosity, then register `gpt5-mini-low` and `gpt5-mini-medium`. Mark all three as deprecated-but-live without `replacement_key`, because saved preset identifiers are public compatibility surfaces and runtime behavior must not change before retirement. Add `GPT5_6_TERRA_LOW` alongside the existing medium/high Terra configs so operator migrations can preserve effort.

Use `DEPRECATED_PRESETS` as the single lifecycle boundary, with two explicit states. Deprecated-but-live entries have warning metadata and no `replacement_key`, so `resolve_runtime_preset_key()` returns the saved key unchanged. Retired entries retain their public key and set a registered canonical `replacement_key`, so resolution redirects before config lookup. Tests must cover both invariants: preserved entries keep their original config, and redirect entries resolve to an existing canonical config.

Codex has two related but distinct surfaces. Static `codex-gpt-*` presets are saved compatibility selections, while live model choices come from app-server `model/list` and use `codex-runtime:<model>|effort=<value>` keys. Keep static old keys bound to their original runtime model and let catalog filtering determine availability; do not redirect them to a direct OpenAI preset or extend `_build_codex_runtime_presets()` for new runtime models. Preserve unknown safe lowercase effort tokens exactly as the runtime reports them.

## Compatibility Mapping

| Saved key(s) | Lifecycle state | Runtime resolution | Operator guidance |
| --- | --- | --- | --- |
| `o4-mini-low`, `o4-mini-medium`, `o4-mini-high` | Deprecated, live | Original o4-mini config | Matching GPT-5.6 Terra low/medium/high |
| `gpt5-mini-low`, `gpt5-mini-medium`, `gpt5-mini` | Deprecated, live | Original GPT-5 Mini config | Matching GPT-5.6 Terra low/medium/high |
| `gpt-5.1-codex`, `gpt-5.2-codex` | Retired direct endpoints | `gpt56-sol-default` | Automatic medium-effort Sol redirect |
| `codex-gpt-5.1-codex`, `codex-gpt-5.2-codex` | Deprecated runtime selections | Original Codex config when catalog-reported | Prefer a current app-server catalog selection |

## Workstreams & Tasks

### Workstream A - Preserve saved Mini keys and add effort-equivalent Terra targets

- [x] Add `GPT5_MINI_LOW` and `GPT5_MINI_MEDIUM` using the existing Responses-model factory; retain `GPT5_MINI` as high.
- [x] Register `gpt5-mini-low` and `gpt5-mini-medium` with accurate context, effort, verbosity, and deprecated labels.
- [x] Add `GPT5_6_TERRA_LOW` and `gpt56-terra-low` so Terra low/medium/high cover every preserved effort role.
- [x] Verify `src/agentrules/core/agents/openai/config.py` already routes the `gpt-5` family through Responses and needs no new special case.
- [x] Add request tests proving low, medium, and high produce the exact `reasoning.effort` values and no unsupported Chat Completions fallback.

### Workstream B - Register lifecycle states and retired redirects

- [x] Add every key from the compatibility table to `DEPRECATED_PRESETS` with the correct preserve-or-redirect state and actionable reason.
- [x] Update o4-mini, GPT-5 Mini, and retired direct Codex labels/descriptions so model-picker users see current Terra/Sol guidance.
- [x] Preserve every legacy entry in `MODEL_PRESETS`; do not mutate persisted files or delete imported constants.
- [x] Verify deprecated-but-live keys remain on their configured model and retired direct Codex keys resolve to the canonical Sol config.

### Workstream C - Guard the Codex ownership boundary

- [x] Keep `_build_codex_runtime_presets()` free of GPT-5.6 additions and avoid editing runtime catalog results into static constants.
- [x] Extend/retain tests showing `model/list` can surface an unknown future model and an unknown safe lowercase effort token.
- [x] Verify runtime default still omits a model override when the catalog cannot provide a trustworthy default.
- [x] Verify local Codex readiness still depends on the executable and resolved `CODEX_HOME` policy, not a direct OpenAI API key.
- [x] Add a negative registry assertion that no `codex-gpt-5.6*` static key is introduced by this milestone.

### Workstream D - Prove saved-config compatibility

- [x] Extend the cross-provider deprecation iteration and model override tests for all mappings.
- [x] Test labels/descriptions through the CLI model picker without requiring a Codex runtime process.
- [x] Test static old Codex keys separately from dynamic `codex-runtime:` keys so direct-provider redirects cannot mask runtime catalog regressions.
- [x] Confirm `MODEL_PRESET_DEFAULTS` remains unchanged.

## Dependencies

- MS001 must reconfirm official OpenAI lifecycle status and replacement guidance.
- Existing saved OpenAI/Codex compatibility keys and canonical GPT-5.6 Sol/Terra targets must remain registered.
- MS005 owns the consolidated lifecycle prose and final full-suite validation.

## Risks & Mitigations

- Risk: A migration recommendation collapses low/medium/high intent.
  Mitigation: Complete the Terra low/medium/high matrix and test guidance per saved effort role.

- Risk: Deprecation metadata silently redirects a still-live endpoint.
  Mitigation: Leave `replacement_key` unset until retirement and assert runtime resolution returns the saved key.

- Risk: Direct OpenAI model availability is mistaken for Codex runtime availability.
  Mitigation: Keep runtime `model/list` authoritative; add negative tests for static GPT-5.6 Codex keys.

- Risk: Static compatibility tests pass while future runtime effort support regresses.
  Mitigation: Retain dedicated tests that pass an unknown safe effort token through runtime selection and request preparation.

- Risk: Adding GPT-5.5 Pro appears trivial but breaks streaming.
  Mitigation: Keep it out of scope until model-specific transport capability and tests are designed.

## Validation / QA Plan

Run from the repository root:

    uv run pytest -q tests/unit/agents/test_openai_helpers.py tests/unit/test_provider_model_compatibility_matrix.py tests/unit/test_model_overrides.py tests/unit/test_cli_model_picker_ui.py tests/unit/agents/test_codex_architect.py tests/unit/agents/test_codex_request_builder.py tests/unit/test_cli_codex_settings.py tests/unit/test_codex_runtime_service.py
    uv run ruff check src/agentrules/core/types/models.py src/agentrules/config/agents.py src/agentrules/core/configuration/model_presets.py src/agentrules/core/agents/openai src/agentrules/core/agents/codex tests/unit/agents/test_openai_helpers.py tests/unit/agents/test_codex_architect.py tests/unit/test_provider_model_compatibility_matrix.py tests/unit/test_model_overrides.py tests/unit/test_cli_codex_settings.py
    uv run pyright
    uv run python -c "import agentrules"
    git diff --check

Expected outcomes:

- All targeted tests pass without network access or a real Codex process.
- Every saved key exists; live entries preserve their configs and retired direct entries resolve to registered canonical targets.
- GPT-5 Mini payloads remain available for saved selections, and Terra low/medium/high provide explicit migration choices.
- Future runtime catalog model/effort tests still pass.
- No static Codex GPT-5.6 key exists; phase defaults remain GPT-5.6 Sol direct API.
- Import, lint, types, and whitespace checks pass.

## Deferred Work

- GPT-5.5 Pro requires a separate model-specific streaming/transport capability plan.
- GPT-5.6 Pro mode requires an execution-mode design independent of preset model identity.
- Removing static Codex compatibility presets, if ever desired, requires a separate saved-config migration policy.
- Paid direct OpenAI and Codex live smokes remain optional in MS005.

## Rollout / Recovery

All old keys remain registered, so rollback does not require a configuration rewrite. Do not add a runtime redirect for a live deprecated endpoint merely because its recommendation changes. If a retired endpoint's canonical target has an account-availability issue, amend the plan and redirect its saved key only to another documented active target. Do not restore retired wire IDs as defaults or convert dynamic Codex discovery into static configuration during recovery.

## Changelog

- 2026-08-29: Milestone created.
- 2026-08-29: Added effort-preserving OpenAI mappings, exact compatibility table, Codex runtime ownership guards, Pro deferrals, and recovery rules.
- 2026-08-29: Added GPT-5 Mini low/medium saved presets and registered o4-mini plus direct/static Codex lifecycle metadata without removing public keys.
- 2026-08-29: Preserved dynamic Codex `model/list` ownership and safe future effort handling. The focused audit corrected a vacuous static-Codex negative test so it now inspects the combined registry.
- 2026-08-29: Validation passed: 260 tests and 43 subtests, Ruff, Pyright, import smoke, and `git diff --check`.
- 2026-08-29: Post-completion reviews finalized the lifecycle matrix: o4-mini and GPT-5 Mini remain bound while live and recommend effort-matched Terra; retired direct GPT-5.1/5.2 Codex keys redirect to medium-effort Sol; static Codex selections remain catalog-gated. Added Terra low and reconciled this milestone with shipped behavior.
