---
id: EP-20260829-001/MS003
execplan_id: EP-20260829-001
ms: 3
title: "Refresh xAI and DeepSeek Capabilities"
status: planned
domain: cross-cutting
owner: "@codex"
created: 2026-08-29
updated: 2026-08-29
tags: [providers, xai, deepseek, reasoning, presets]
risk: med
links:
  issue: ""
  docs: ""
  pr: ""
---

# Refresh xAI and DeepSeek Capabilities

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Make Grok 4.6 the complete recommended direct xAI path and expose the missing documented DeepSeek V4 effort levels without silent coercion. Registry metadata, constructor defaults, context packing, request payloads, compatibility aliases, and tests must agree. Existing specialized xAI variants and DeepSeek legacy redirects remain available, and unsupported transport/modality models remain absent.

## Definition of Done

- [ ] Grok 4.6 has low, medium, high/default, and xhigh presets with a 500,000-token context.
- [ ] A directly constructed `XaiArchitect` defaults to Grok 4.6 high effort.
- [ ] Grok 4.6 rejects disabled, minimal, and max before dispatch and sends supported effort values unchanged.
- [ ] DeepSeek V4 Flash has disabled, low, high/default, and max presets; V4 Pro has disabled, low, high/default, and max presets.
- [ ] DeepSeek maps generic modes exactly as documented: medium and xhigh resolve to high, max resolves to max, and minimal fails.
- [ ] DeepSeek legacy keys still resolve to canonical V4 Flash configs and both V4 families retain the 32K application output cap.
- [ ] Grok Multi-Agent and DeepSeek Vision Experimental remain absent from the general picker.
- [ ] Targeted xAI/DeepSeek tests, compatibility matrix, lint, types, and import smoke pass offline.

## Scope

### In Scope

- xAI configs, immutable defaults, direct architect default, preset entries, context classification, and request-contract tests.
- DeepSeek V4 configs, immutable accepted-effort metadata, request reasoning translation/validation, preset entries, and tests.
- Model picker labels and compatibility-matrix rows for new variants.
- Lifecycle notes for MS005, including preferred fallback and conservative output cap.

### Out of Scope

- No xAI Responses API migration, xAI SDK migration, or Grok Multi-Agent preset.
- No DeepSeek image input, Vision Experimental preset, or multimodal response parsing.
- No changes to DeepSeek wire model aliases, base URLs, authentication, sampling policy, or structured-output adapter.
- No expansion of DeepSeek `max_tokens` beyond 32,000 in this refresh.
- No removal of Grok 4.5, Grok 4.20 pinned variants, Grok 4.3, or DeepSeek legacy saved keys.
- No phase-default changes, SDK upgrades, price metadata, or paid live requests.

## Current Health Snapshot

| Area | Starting state | Milestone target |
| --- | --- | --- |
| Direct xAI recommendation | Grok 4.5, high default, 500K | Grok 4.6, high default, 500K; Grok 4.5 remains fallback |
| xAI accepted efforts | Grok 4.5 accepts low/medium/high | Grok 4.6 accepts low/medium/high/xhigh exactly |
| xAI constructor | `XaiArchitect(model_name="grok-4.5")` | Default argument and tests use `grok-4.6` |
| DeepSeek effort metadata | V4 maps accepted high/max | V4 metadata accepts low/high/max |
| DeepSeek wire mapping | Enabled modes collapse to high except xhigh/max | Low/high/max are explicit; medium/xhigh follow the documented high mapping; minimal raises |
| DeepSeek output cap | 32K | 32K, documented as intentional application safety cap |
| Specialized models | Grok Multi-Agent and DeepSeek Vision absent | Remain absent |

## Architecture / Design

For xAI, add one immutable `GROK_4_6` high/default config and derive low, medium, and xhigh variants. Add a `ModelDefaults` row with `accepted_reasoning_efforts={"low", "medium", "high", "xhigh"}` and `enabled_reasoning_effort="high"`. Do not enable the legacy `normalize_higher_efforts_to_high` behavior for this family: xhigh is a real wire value. The existing request builder must reject generic modes that do not resolve to that exact accepted set.

Update both places where Grok 4.5 is currently treated as current: the default argument in `XaiArchitect.__init__` and `_apply_model_limits()` in the preset registry. Grok 4.6 stays at 500K rather than falling into the unknown-xAI 256K path.

For DeepSeek, keep wire IDs `deepseek-v4-flash` and `deepseek-v4-pro`. Expand immutable accepted efforts to low/high/max. Refactor `_resolve_v4_reasoning()` into the provider's explicit mapping: disabled/temperature means thinking disabled with no effort; low means enabled/low; medium/enabled/dynamic/high/xhigh mean enabled/high; max means enabled/max; minimal raises `ValueError`. This validation happens while preparing the request, before the network client is called.

Normalize the public `deepseek-v4-pro-max` config to `ReasoningMode.MAX` while preserving its key and wire payload. Programmatic `ReasoningMode.XHIGH` follows DeepSeek's documented compatibility behavior and maps to provider `high`.

## Preset Contract

### xAI keys

| Key | Wire model | Generic mode | Wire effort | Context |
| --- | --- | --- | --- | --- |
| `grok-4.6` | `grok-4.6` | high | high | 500,000 |
| `grok-4.6-reasoning-low` | `grok-4.6` | low | low | 500,000 |
| `grok-4.6-reasoning-medium` | `grok-4.6` | medium | medium | 500,000 |
| `grok-4.6-reasoning-xhigh` | `grok-4.6` | xhigh | xhigh | 500,000 |

There is no non-reasoning, minimal, or max preset. Existing Grok 4.5 and pinned 4.20 keys retain their current contracts.

### DeepSeek keys

| Key | Wire model | Generic mode | Thinking/effort | Context |
| --- | --- | --- | --- | --- |
| `deepseek-v4-flash-non-reasoning` | `deepseek-v4-flash` | disabled | disabled/none | 1,000,000 |
| `deepseek-v4-flash-low` | `deepseek-v4-flash` | low | enabled/low | 1,000,000 |
| `deepseek-v4-flash` | `deepseek-v4-flash` | high | enabled/high | 1,000,000 |
| `deepseek-v4-flash-max` | `deepseek-v4-flash` | max | enabled/max | 1,000,000 |
| `deepseek-v4-pro-non-reasoning` | `deepseek-v4-pro` | disabled | disabled/none | 1,000,000 |
| `deepseek-v4-pro-low` | `deepseek-v4-pro` | low | enabled/low | 1,000,000 |
| `deepseek-v4-pro` | `deepseek-v4-pro` | high | enabled/high | 1,000,000 |
| `deepseek-v4-pro-max` | `deepseek-v4-pro` | max | enabled/max | 1,000,000 |

All DeepSeek rows send at most 32,000 output tokens under this plan.

## Workstreams & Tasks

### Workstream A - Add and recommend Grok 4.6

- [ ] Add `GROK_4_6`, `GROK_4_6_LOW`, `GROK_4_6_MEDIUM`, and `GROK_4_6_XHIGH` configs in `src/agentrules/core/types/models.py`.
- [ ] Add the Grok 4.6 `ModelDefaults` row in `src/agentrules/core/agents/xai/config.py` with exact efforts and no disable behavior.
- [ ] Change only the direct `XaiArchitect` default argument from Grok 4.5 to Grok 4.6; preserve explicit older model construction.
- [ ] Extend `_apply_model_limits()` so Grok 4.6 receives 500,000 tokens.
- [ ] Add all four planned presets with labels that identify high as the recommended/default effort.
- [ ] Keep Grok 4.20 Multi-Agent absent and add a negative registry assertion if one is not already present.

### Workstream B - Complete DeepSeek V4 effort handling

- [ ] Add `DEEPSEEK_V4_FLASH_LOW`, `DEEPSEEK_V4_FLASH_MAX`, and `DEEPSEEK_V4_PRO_LOW`; change the existing Pro max constant to `ReasoningMode.MAX` without changing its public key.
- [ ] Expand both V4 `accepted_reasoning_efforts` sets to low/high/max.
- [ ] Replace implicit effort coercion in `_resolve_v4_reasoning()` with the explicit mapping documented above and an actionable error for minimal.
- [ ] Add the three missing direct presets with consistent labels/descriptions.
- [ ] Preserve `DEEPSEEK_CHAT`, `DEEPSEEK_REASONER`, `_LEGACY_MODEL_ALIASES`, and `DEPRECATED_PRESETS` targets.
- [ ] Keep `max_output_tokens=32_000` for Flash and Pro and add a regression assertion so a future catalog refresh cannot raise it accidentally.
- [ ] Keep DeepSeek Vision Experimental absent and add a negative registry assertion.

### Workstream C - Prove request and registry contracts

- [ ] Add xAI helper tests for default resolution, all four valid wire efforts, invalid disabled/minimal/max modes, context limit, and direct architect default.
- [ ] Add DeepSeek helper tests for disabled/low/medium/high/xhigh/max payloads, invalid minimal errors, tool/sampling behavior, aliases, and 32K cap.
- [ ] Add all planned rows to `DIRECT_MODEL_CONTRACTS` and extend model override/picker tests.
- [ ] Assert invalid modes fail during payload preparation without a network client call.

## Dependencies

- MS001 must confirm current xAI and DeepSeek contracts.
- MS002 may be complete or in a separate green commit; this milestone must not alter its provider behavior.
- MS005 owns consolidated lifecycle prose and full-suite validation.

## Risks & Mitigations

- Risk: Grok 4.6 falls through to the unknown-model context default.
  Mitigation: Update and test `_apply_model_limits()` alongside the constructor and registry.

- Risk: xhigh is normalized to high by legacy xAI compatibility logic.
  Mitigation: Give Grok 4.6 an exact accepted set and do not enable higher-effort normalization.

- Risk: DeepSeek low preset labels exist but the request builder still sends high.
  Mitigation: Test the final prepared payload in both provider-specific and cross-provider contract suites.

- Risk: Correcting Pro max from generic xhigh to max changes programmatic xhigh behavior.
  Mitigation: Preserve the preset key by moving it to `ReasoningMode.MAX`, and test that standalone xhigh follows DeepSeek's current documented high mapping.

- Risk: Raising the upstream output ceiling causes unexpectedly large phase results.
  Mitigation: Retain and test the 32K application cap; evaluate expansion separately with performance and cost evidence.

- Risk: Specialized new models are exposed through an incompatible adapter.
  Mitigation: Add negative registry tests for Grok Multi-Agent and DeepSeek Vision Experimental.

## Validation / QA Plan

Run from the repository root:

    uv run pytest -q tests/unit/agents/test_xai_helpers.py tests/unit/agents/test_deepseek_helpers.py tests/unit/agents/test_deepseek_agent_parsing.py tests/unit/test_provider_model_compatibility_matrix.py tests/unit/test_model_overrides.py tests/unit/test_cli_model_picker_ui.py
    uv run ruff check src/agentrules/core/types/models.py src/agentrules/config/agents.py src/agentrules/core/agents/xai src/agentrules/core/agents/deepseek tests/unit/agents/test_xai_helpers.py tests/unit/agents/test_deepseek_helpers.py tests/unit/test_provider_model_compatibility_matrix.py tests/unit/test_model_overrides.py
    uv run pyright
    uv run python -c "import agentrules"
    git diff --check

Expected outcomes:

- All targeted tests pass without network access.
- Prepared payloads carry exact documented efforts and invalid values raise before dispatch.
- `XaiArchitect` defaults to `grok-4.6`; explicit older models still resolve through their existing defaults.
- DeepSeek Flash/Pro payloads still carry `max_tokens=32000`.
- Import, lint, types, and whitespace checks pass; phase defaults are unchanged.

## Deferred Work

- Grok Multi-Agent requires a separately designed Responses/xAI-SDK transport.
- DeepSeek Vision Experimental requires a reviewed multimodal config, prompt, token, and response contract.
- DeepSeek output-cap expansion requires separate cost/latency/memory acceptance criteria.
- Paid live smokes remain optional in MS005.

## Rollout / Recovery

Grok 4.6 becomes the direct constructor default, while Grok 4.5 remains a registered fallback. If Grok 4.6 availability fails, revert the constructor default and recommendation label to 4.5 but retain all published 4.6 keys. DeepSeek additions are additive; if an effort is rejected upstream after reconfirmation, remove its recommendation and redirect only newly published compatibility behavior after a plan amendment—do not restore retired `deepseek-chat` or `deepseek-reasoner` wire IDs.

## Changelog

- 2026-08-29: Milestone created.
- 2026-08-29: Defined exact Grok 4.6 and DeepSeek V4 matrices, fail-fast mappings, 32K cap policy, exclusions, and rollback behavior.
- 2026-08-29: MS001 source revalidation amended DeepSeek compatibility behavior: medium/xhigh map to high, max maps to max, and minimal is rejected.
