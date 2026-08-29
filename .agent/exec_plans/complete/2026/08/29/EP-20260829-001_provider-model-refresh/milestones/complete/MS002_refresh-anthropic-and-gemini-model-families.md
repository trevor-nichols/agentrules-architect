---
id: EP-20260829-001/MS002
execplan_id: EP-20260829-001
ms: 2
title: Refresh Anthropic and Gemini Model Families
status: completed
domain: cross-cutting
owner: '@codex'
created: 2026-08-29
updated: '2026-08-29'
tags:
- providers
- anthropic
- gemini
- capabilities
- presets
risk: med
links:
  issue: ''
  docs: ''
  pr: ''
---

# Refresh Anthropic and Gemini Model Families

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Deliver complete, fail-fast direct-API support for Claude Opus 5, Gemini 3.7 Flash, Gemini 3.6 Flash, and Gemini 3.5 Flash-Lite. Each family must be represented consistently across immutable configs, picker presets, context metadata, provider capability profiles, request translation, and tests. Generic Opus keys move to Opus 5 only after the pinned Opus 5 path is proven; local Claude Code model ownership does not change.

## Definition of Done

- [x] Opus 5 has one disabled-thinking preset plus adaptive low/medium/high/xhigh/max presets.
- [x] Generic `claude-opus` keys resolve to Opus 5 and every pinned Opus 4.8 key remains unchanged.
- [x] Opus 5 capability metadata drives request construction without family-specific string checks in the request builder.
- [x] Gemini 3.7 exposes low/medium/high only; disabled/minimal fails before dispatch.
- [x] Gemini 3.6 and Gemini 3.5 Flash-Lite expose minimal/low/medium/high with documented defaults.
- [x] All three Gemini profiles support structured output with tools and resolve to the correct family despite prefix overlap.
- [x] Provider-specific and cross-provider contract tests pass offline.
- [x] Lifecycle notes needed by MS005 are captured in this milestone's changelog.

## Scope

### In Scope

- Model constants and generic Opus alias targets in `src/agentrules/core/types/models.py`.
- Direct preset definitions, labels, descriptions, imports, and input-limit handling in `src/agentrules/config/agents.py`.
- Anthropic immutable capability metadata and request-builder regression coverage.
- Gemini immutable capability metadata, exact reasoning-mode validation, and architect/request configuration integration.
- Unit and compatibility-matrix cases for valid payloads, invalid modes, context limits, labels, aliases, and rollback keys.

### Out of Scope

- No phase-default changes; GPT-5.6 Sol remains the project default.
- No new pinned Claude Code Opus 5 presets or Claude Code version-gate changes.
- No removal or redirect of Opus 4.8, Gemini 2.5, or existing Gemini compatibility keys.
- No SDK upgrades, pricing metadata, account/retention policy automation, or paid live requests.
- No Anthropic Mythos 5 or unreviewed preview model.

## Current Health Snapshot

| Area | Starting state | Milestone target |
| --- | --- | --- |
| Anthropic latest Opus | Generic keys point to Opus 4.8 | New pinned Opus 5 family; generic keys point to 5; 4.8 remains pinned |
| Anthropic capability model | Immutable prefix profiles already drive adaptive thinking | Add Opus 5 profile using the same mechanism |
| Gemini stable Flash | 3.5 Flash represented | Add 3.7, 3.6, and 3.5 Flash-Lite families |
| Gemini reasoning | Nearest-level resolution can coerce unsupported modes | Exact validation for new family contracts before dispatch |
| Gemini profile matching | Ordered prefix matching | More-specific `3.5-flash-lite` must precede `3.5-flash` |
| Contract coverage | Sonnet/Fable/Opus 4.8 and Gemini 3.5/3.1 rows exist | Add every new default/effort variant and invalid combination |

## Architecture / Design

Keep model identity in `ModelConfig` and capability behavior in provider-local immutable profiles. The Anthropic request builder should learn Opus 5 through `resolve_capability_profile()` rather than another `model_name.startswith()` branch. Model presets may derive effort variants with `_replace()` so that wire ID, tools config, and provider identity have one source.

For Opus 5, define `CLAUDE_OPUS_5` with `ReasoningMode.DISABLED` and `CLAUDE_OPUS_5_WITH_REASONING` with `ReasoningMode.DYNAMIC`. The profile uses adaptive default thinking, no manual budget thinking, structured output, and effort levels low through max. A disabled request must not send `output_config.effort`; adaptive requests send the selected effort. Reassign existing generic `CLAUDE_OPUS` constants to the Opus 5 configs, but leave `CLAUDE_OPUS_48` constants untouched.

Gemini profiles must model the exact allowed level set. Add provider-local validation that rejects an unsupported generic mode before SDK dispatch rather than selecting the nearest allowed level. Existing families should retain their tested behavior unless MS001 finds an upstream contract change. Place the `gemini-3.5-flash-lite` profile before `gemini-3.5-flash`, because profile matching accepts the exact prefix and suffixed snapshots.

## Preset Contract

### Anthropic keys

| Key | Wire model | Generic mode | Anthropic effort |
| --- | --- | --- | --- |
| `claude-opus-5` | `claude-opus-5` | disabled | none |
| `claude-opus-5-reasoning-low` | `claude-opus-5` | dynamic | low |
| `claude-opus-5-reasoning-medium` | `claude-opus-5` | dynamic | medium |
| `claude-opus-5-reasoning-high` | `claude-opus-5` | dynamic | high |
| `claude-opus-5-reasoning-xhigh` | `claude-opus-5` | dynamic | xhigh |
| `claude-opus-5-reasoning-max` | `claude-opus-5` | dynamic | max |
| `claude-opus` | `claude-opus-5` | disabled | none |
| `claude-opus-reasoning` | `claude-opus-5` | dynamic | provider default/no explicit effort |

All rows use a 1,000,000-token input limit. Existing `claude-opus-4.8*` rows remain wire-identical to their pre-milestone state.

### Gemini keys

| Key | Wire model | Generic mode | Wire thinking level |
| --- | --- | --- | --- |
| `gemini-3.7-flash` | `gemini-3.7-flash` | medium | medium |
| `gemini-3.7-flash-reasoning-low` | `gemini-3.7-flash` | low | low |
| `gemini-3.7-flash-reasoning-high` | `gemini-3.7-flash` | high | high |
| `gemini-3.6-flash` | `gemini-3.6-flash` | medium | medium |
| `gemini-3.6-flash-reasoning-minimal` | `gemini-3.6-flash` | minimal | minimal |
| `gemini-3.6-flash-reasoning-low` | `gemini-3.6-flash` | low | low |
| `gemini-3.6-flash-reasoning-high` | `gemini-3.6-flash` | high | high |
| `gemini-3.5-flash-lite` | `gemini-3.5-flash-lite` | minimal | minimal |
| `gemini-3.5-flash-lite-reasoning-low` | `gemini-3.5-flash-lite` | low | low |
| `gemini-3.5-flash-lite-reasoning-medium` | `gemini-3.5-flash-lite` | medium | medium |
| `gemini-3.5-flash-lite-reasoning-high` | `gemini-3.5-flash-lite` | high | high |

All rows use a 1,048,576-token input limit. Do not add disabled/minimal 3.7 presets or silently coerce those modes to low.

## Workstreams & Tasks

### Workstream A - Add immutable model configurations

- [x] Add `CLAUDE_OPUS_5` and `CLAUDE_OPUS_5_WITH_REASONING`; retarget generic `CLAUDE_OPUS` constants without changing pinned 4.8 constants.
- [x] Add the three Gemini base configurations and derive only the variants listed in the preset contract.
- [x] Import the new constants into `src/agentrules/config/agents.py` without duplicating wire IDs in request builders.
- [x] Extend `_apply_model_limits()` so Opus 5 is explicitly in the 1M Anthropic family. Verify the existing Gemini branch supplies 1,048,576 without a special case.

### Workstream B - Extend provider capability metadata

- [x] Add the Opus 5 `CapabilityProfile` before older Opus profiles with structured output, adaptive thinking, no manual budget, low-through-max effort, and adaptive-default policy.
- [x] Confirm the existing Anthropic request builder emits `thinking.type=disabled` for the non-thinking config and `thinking.type=adaptive` plus effort for variants.
- [x] Add Gemini profiles for 3.7 Flash, 3.6 Flash, and 3.5 Flash-Lite with exact supported levels and structured-output-with-tools support.
- [x] Put the Flash-Lite profile before the broader 3.5 Flash profile and test exact IDs plus date-suffixed snapshots.
- [x] Add or extend a Gemini validation helper and call it from the request configuration path so unsupported 3.7 disabled/minimal values raise an actionable `ValueError` before a client method executes.

### Workstream C - Register and label direct presets

- [x] Add every key from the preset tables to `BASE_MODEL_PRESETS` with labels that state family and effort.
- [x] Make Opus 5 the generic Opus target only after its pinned rows pass request-contract tests.
- [x] Preserve older explicit presets and generic Gemini 2.5 compatibility behavior; do not silently repoint `gemini-flash` because its non-thinking role is incompatible with Gemini 3.7.
- [x] Ensure no pinned Opus 5 presets are added to `_build_claude_code_runtime_presets()`; the existing moving `claude-code-opus` alias remains runtime-owned.

### Workstream D - Prove behavior

- [x] Add Anthropic capability tests for profile resolution, effort set, adaptive default, structured output, disabled payload, and invalid effort.
- [x] Add Gemini capability tests for defaults, all valid levels, invalid 3.7 modes, prefix ordering, snapshots, and structured output with tools.
- [x] Add `ModelContract` rows for every listed preset and update model override tests for presence, labels, generic aliases, and pinned rollback keys.
- [x] Verify invalid modes fail without invoking a mocked provider client.

## Dependencies

- MS001 must confirm the model contracts before code changes.
- Existing provider SDK versions must already expose the fields used by current adapters. Any required upgrade stops this milestone and triggers a plan amendment.
- MS005 owns the consolidated lifecycle document and full repository validation.

## Risks & Mitigations

- Risk: Opus 5 generic alias changes the model used by an existing saved generic key.
  Mitigation: Keep pinned 4.8 keys, disclose the generic move in labels/docs, and test both targets explicitly.

- Risk: Gemini prefix overlap assigns Flash-Lite the 3.5 Flash profile.
  Mitigation: Order specific prefixes first and add resolution tests for exact and suffixed IDs.

- Risk: Gemini's current nearest-level helper silently upgrades invalid 3.7 requests.
  Mitigation: Validate against profile metadata before translation and assert no dispatch on invalid modes.

- Risk: Direct Anthropic availability is confused with Claude Code availability.
  Mitigation: Do not derive pinned Claude Code Opus 5 presets without a reviewed exact-runtime version gate.

- Risk: Large repetitive preset blocks drift.
  Mitigation: Derive effort variants from one immutable base config and keep provider behavior in profiles; do not introduce a speculative registry framework.

## Validation / QA Plan

Run from the repository root:

    uv run pytest -q tests/unit/agents/test_anthropic_capabilities.py tests/unit/agents/test_anthropic_request_builder.py tests/unit/agents/test_gemini_capabilities.py tests/unit/test_provider_model_compatibility_matrix.py tests/unit/test_model_overrides.py tests/unit/test_cli_model_picker_ui.py
    uv run ruff check src/agentrules/core/types/models.py src/agentrules/config/agents.py src/agentrules/core/agents/anthropic src/agentrules/core/agents/gemini tests/unit/agents/test_anthropic_capabilities.py tests/unit/agents/test_anthropic_request_builder.py tests/unit/agents/test_gemini_capabilities.py tests/unit/test_provider_model_compatibility_matrix.py tests/unit/test_model_overrides.py
    uv run pyright
    uv run python -c "import agentrules"
    git diff --check

Expected outcomes:

- All targeted tests pass offline.
- Invalid Opus/Gemini combinations produce provider- and model-specific errors before dispatch.
- Import, lint, type checking, and whitespace checks pass.
- `MODEL_PRESET_DEFAULTS` is unchanged.

## Deferred Work

- Pinned Claude Code Opus 5 support awaits a documented exact executable version gate.
- Automatic migration of generic Gemini 2.5 non-thinking selections awaits their lifecycle event and a role-compatible successor decision.
- Pricing/cost comparison and optional provider live smokes remain outside this milestone.

## Rollout / Recovery

These entries are additive except the two generic Opus targets. If Opus 5 proves unavailable in a deployment, retain the new pinned keys and change only the generic keys back to Opus 4.8 while recording the rollback in lifecycle documentation. Never delete published Opus 5 saved keys. Gemini additions can be disabled from recommendation labels without removing their keys.

## Changelog

- 2026-08-29: Milestone created.
- 2026-08-29: Defined exact Anthropic/Gemini preset matrices, capability rules, prefix-order constraint, fail-fast validation, and rollback behavior.
- 2026-08-29: Added Claude Opus 5 and the Gemini 3.7/3.6/3.5 Flash-Lite preset families. Generic Opus keys now resolve to Opus 5; pinned Opus 4.8 and moving Claude Code aliases remain unchanged.
- 2026-08-29: The AI-code audit identified and removed a subtle SDK-level fallback for exact Gemini families. Missing required SDK enum members now fail closed instead of silently selecting a different thinking level.
- 2026-08-29: Validation passed: 232 tests and 5 subtests, Ruff, Pyright, import smoke, and `git diff --check`.
