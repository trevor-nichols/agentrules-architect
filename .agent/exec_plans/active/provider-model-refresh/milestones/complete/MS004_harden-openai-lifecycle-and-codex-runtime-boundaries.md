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

Close the known OpenAI saved-preset lifecycle gaps while preserving workload intent and Codex runtime ownership. Deprecated o4-mini keys must migrate to effort-equivalent GPT-5 Mini configs, deprecated GPT-5.1/5.2 Codex keys must migrate to the active GPT-5.3 Codex compatibility target, and future Codex models/efforts must continue to come from app-server `model/list` rather than new static presets.

## Definition of Done

- [x] GPT-5 Mini has low, medium, and existing high direct-API presets using the Responses API.
- [x] Each o4-mini low/medium/high compatibility key remains registered and resolves to the matching GPT-5 Mini effort role.
- [x] Direct GPT-5.1 Codex and GPT-5.2 Codex keys remain registered and resolve to GPT-5.3 Codex.
- [x] Static Codex-derived GPT-5.1/5.2 compatibility keys, if still exposed, resolve to the existing static GPT-5.3 compatibility key.
- [x] Picker labels and descriptions disclose deprecation and replacement behavior.
- [x] Codex runtime-default and runtime-catalog behavior still accepts future model IDs and safe future effort tokens.
- [x] No static Codex GPT-5.6 preset, GPT-5.5 Pro preset, or GPT-5.6 Pro-mode pseudo-preset is added.
- [x] OpenAI, lifecycle, Codex, picker, lint, type, and import tests pass offline.

## Scope

### In Scope

- GPT-5 Mini low/medium immutable configs and direct preset definitions.
- OpenAI compatibility metadata in `DEPRECATED_PRESETS` for o4-mini and deprecated Codex model keys.
- Lifecycle-aware labels/descriptions for legacy entries.
- Regression tests for direct OpenAI request payloads, compatibility resolution, saved overrides, static Codex compatibility, and dynamic Codex runtime discovery.
- Lifecycle notes for final documentation in MS005.

### Out of Scope

- No new GPT-5.6 direct presets; Sol, Terra, and Luna are already complete.
- No new static Codex presets for GPT-5.6 or any newly observed runtime model.
- No removal of legacy keys or automatic rewrite of persisted configuration files.
- No GPT-5.5 Pro support until model-specific streaming/transport capability exists.
- No GPT-5.6 Pro mode until execution mode is represented independently from model identity.
- No default phase changes, SDK upgrades, prompt migrations, pricing changes, or paid live calls.

## Current Health Snapshot

| Area | Starting state | Milestone target |
| --- | --- | --- |
| GPT-5.6 direct API | Sol/Terra/Luna presets and contracts already present | Remains unchanged |
| GPT-5 Mini | One high-effort key `gpt5-mini` | Add low and medium canonical keys; keep existing high key |
| o4-mini lifecycle | Three keys present, no deprecation redirect | Redirect low/medium/high to equivalent GPT-5 Mini configs |
| Direct Codex API variants | 5.1, 5.2, and 5.3 static direct keys present | 5.1/5.2 compatibility keys resolve to 5.3 |
| Local Codex runtime | `model/list` generates dynamic model/effort presets | Remains authoritative and future-compatible |
| Pro variants | Current architect contract is not model-specific enough | Explicitly deferred |

## Architecture / Design

Keep `gpt5-mini` as the existing public high-effort canonical key. Add `GPT5_MINI_LOW` and `GPT5_MINI_MEDIUM` via `_gpt5_responses_model()` with matching text verbosity, then register `gpt5-mini-low` and `gpt5-mini-medium`. Do not rename the existing high key, because saved preset identifiers are public compatibility surfaces.

Use `DEPRECATED_PRESETS` as the only runtime redirect mechanism. The legacy entry stays in `MODEL_PRESETS` so picker and saved-config inspection can explain it, while `resolve_runtime_preset_key()` returns the canonical replacement before config lookup. The existing matrix test that iterates every deprecation mapping must remain the invariant: both keys exist and resolved configs are equal.

Codex has two related but distinct surfaces. Static `codex-gpt-*` presets are compatibility artifacts derived from direct configs; live model choices come from app-server `model/list` and use `codex-runtime:<model>|effort=<value>` keys. Add lifecycle redirects for exposed static old keys, but do not extend `_build_codex_runtime_presets()` for new runtime models. Preserve unknown safe lowercase effort tokens exactly as the runtime reports them.

## Compatibility Mapping

| Legacy saved key | Canonical replacement | Reason preserved |
| --- | --- | --- |
| `o4-mini-low` | `gpt5-mini-low` | low reasoning |
| `o4-mini-medium` | `gpt5-mini-medium` | medium reasoning |
| `o4-mini-high` | `gpt5-mini` | high reasoning |
| `gpt-5.1-codex` | `gpt-5.3-codex` | direct Responses coding model, medium reasoning |
| `gpt-5.2-codex` | `gpt-5.3-codex` | direct Responses coding model, medium reasoning |
| `codex-gpt-5.1-codex` | `codex-gpt-5.3-codex` | static Codex compatibility selection, medium reasoning |
| `codex-gpt-5.2-codex` | `codex-gpt-5.3-codex` | static Codex compatibility selection, medium reasoning |

If MS001 finds that a listed static Codex-derived key is no longer exposed, do not recreate it merely to redirect it; amend the table and cover only public keys that exist at implementation start.

## Workstreams & Tasks

### Workstream A - Add effort-equivalent GPT-5 Mini targets

- [x] Add `GPT5_MINI_LOW` and `GPT5_MINI_MEDIUM` using the existing Responses-model factory; retain `GPT5_MINI` as high.
- [x] Register `gpt5-mini-low` and `gpt5-mini-medium` with accurate context, effort, verbosity, and labels.
- [x] Verify `src/agentrules/core/agents/openai/config.py` already routes the `gpt-5` family through Responses and needs no new special case.
- [x] Add request tests proving low, medium, and high produce the exact `reasoning.effort` values and no unsupported Chat Completions fallback.

### Workstream B - Register lifecycle redirects

- [x] Add every applicable mapping from the compatibility table to `DEPRECATED_PRESETS` with current, actionable reasons.
- [x] Update o4-mini and deprecated Codex labels/descriptions so model-picker users see the replacement rather than assuming the old endpoint is recommended.
- [x] Preserve every legacy entry in `MODEL_PRESETS`; do not mutate persisted files or delete imported constants.
- [x] Verify `resolve_runtime_preset_key()` and `get_model_config_for_preset_key()` return canonical configs for every new mapping.

### Workstream C - Guard the Codex ownership boundary

- [x] Keep `_build_codex_runtime_presets()` free of GPT-5.6 additions and avoid editing runtime catalog results into static constants.
- [x] Extend/retain tests showing `model/list` can surface an unknown future model and an unknown safe lowercase effort token.
- [x] Verify runtime default still omits a model override when the catalog cannot provide a trustworthy default.
- [x] Verify local Codex readiness still depends on the executable and resolved `CODEX_HOME` policy, not a direct OpenAI API key.
- [x] Add a negative registry assertion that no `codex-gpt-5.6*` static key is introduced by this milestone.

### Workstream D - Prove saved-config compatibility

- [x] Extend the cross-provider deprecation iteration and model override tests for all mappings.
- [x] Test labels/descriptions through the CLI model picker without requiring a Codex runtime process.
- [x] Test static old Codex keys separately from dynamic `codex-runtime:` keys so a passing redirect cannot mask runtime catalog regressions.
- [x] Confirm `MODEL_PRESET_DEFAULTS` remains unchanged.

## Dependencies

- MS001 must reconfirm official OpenAI lifecycle status and replacement guidance.
- Existing GPT-5.3 Codex and static Codex compatibility keys must remain registered.
- MS005 owns the consolidated lifecycle prose and final full-suite validation.

## Risks & Mitigations

- Risk: All o4-mini keys collapse to the existing high GPT-5 Mini config.
  Mitigation: Add low and medium canonical configs first, then map by effort and test equality per key.

- Risk: A compatibility redirect removes the old key from the picker/registry.
  Mitigation: Keep old definitions registered and rely on `DEPRECATED_PRESETS` for runtime resolution.

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
- Every legacy key and canonical target exists; resolution returns equal configs.
- GPT-5 Mini payloads use Responses and preserve low/medium/high effort.
- Future runtime catalog model/effort tests still pass.
- No static Codex GPT-5.6 key exists; phase defaults remain GPT-5.6 Sol direct API.
- Import, lint, types, and whitespace checks pass.

## Deferred Work

- GPT-5.5 Pro requires a separate model-specific streaming/transport capability plan.
- GPT-5.6 Pro mode requires an execution-mode design independent of preset model identity.
- Removing static Codex compatibility presets, if ever desired, requires a separate saved-config migration policy.
- Paid direct OpenAI and Codex live smokes remain optional in MS005.

## Rollout / Recovery

All old keys remain registered, so rollback does not require a configuration rewrite. If a replacement has an account-availability issue, preserve the new lifecycle metadata and temporarily redirect only the affected canonical choice to a documented active fallback after amending the plan. Do not restore deprecated wire IDs as defaults, and do not convert dynamic Codex discovery into static configuration during recovery.

## Changelog

- 2026-08-29: Milestone created.
- 2026-08-29: Added effort-preserving OpenAI mappings, exact compatibility table, Codex runtime ownership guards, Pro deferrals, and recovery rules.
- 2026-08-29: Added GPT-5 Mini low/medium canonical presets and routed all o4-mini and deprecated direct/static Codex compatibility keys through `DEPRECATED_PRESETS` without removing saved keys.
- 2026-08-29: Preserved dynamic Codex `model/list` ownership and safe future effort handling. The focused audit corrected a vacuous static-Codex negative test so it now inspects the combined registry.
- 2026-08-29: Validation passed: 260 tests and 43 subtests, Ruff, Pyright, import smoke, and `git diff --check`.
