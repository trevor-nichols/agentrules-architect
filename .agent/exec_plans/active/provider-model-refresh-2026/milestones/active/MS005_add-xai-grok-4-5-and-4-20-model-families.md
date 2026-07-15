---
id: EP-20260715-001/MS005
execplan_id: EP-20260715-001
ms: 5
title: "Add xAI Grok 4.5 and 4.20 model families"
status: planned
domain: backend
owner: "@codex"
created: 2026-07-15
updated: 2026-07-15
tags: [xai, grok-4-5, grok-4-20, models]
risk: med
links:
  issue: ""
  docs: "https://docs.x.ai/developers/grok-4-5"
  pr: ""
---

# Add xAI Grok 4.5 and 4.20 model families

This milestone is a living document. Keep the YAML front matter accurate, update this file as work proceeds, and record material revisions in `Changelog`.

## Objective

Expose Grok 4.5 as AgentRules' recommended general xAI model and add explicit specialized Grok 4.20 reasoning, non-reasoning, and multi-agent choices. The xAI adapter must send only reasoning efforts each model accepts and must use the correct 500k or 1M context metadata instead of provider-wide fallbacks.

## Definition of Done

- [ ] `grok-4.5` has low, medium, and high presets, defaults to high, and becomes the default model for a directly constructed `XAIArchitect`.
- [ ] No Grok 4.5 preset or request path sends `reasoning_effort="none"`; unsupported disabled/xhigh/max programmatic configurations fail before network I/O with an actionable message.
- [ ] `grok-4.20-0309-reasoning`, `grok-4.20-0309-non-reasoning`, and `grok-4.20-multi-agent-0309` are available as clearly labeled specialized/beta choices.
- [ ] Grok 4.5 receives a 500,000-token context limit and the selected Grok 4.20 models receive 1,000,000.
- [ ] `ModelDefaults` represents accepted effort values explicitly rather than with a boolean.
- [ ] Grok 4.3 and legacy redirect presets remain available and retain their existing tested request behavior.
- [ ] Focused xAI, model-override, picker, import, Ruff, and Pyright validation passes.

## Scope

### In Scope

- Add model configs to `src/agentrules/core/types/models.py` and presets to `src/agentrules/config/agents.py`.
- Change the xAI architect's default model from Grok 4.3 to Grok 4.5 while retaining Grok 4.3 as an explicit lower-cost/legacy-current choice.
- Replace `reasoning_effort_supported: bool` in `src/agentrules/core/agents/xai/config.py` with an immutable accepted-effort set or an equivalent explicit capability representation.
- Update `xai/request_builder.py` to map and validate provider-neutral reasoning modes per model. Grok 4.5 accepts only low, medium, and high; `ENABLED` should resolve to its documented high default.
- Treat the dated Grok 4.20 IDs as pinned specialized choices. The reasoning and non-reasoning variants should rely on their model identity unless xAI explicitly documents a separate effort parameter; do not invent one. Multi-agent must use the existing supported Chat Completions surface and remain opt-in.
- Add exact context-limit mapping and regression tests for the pre-existing 1M/256k xAI families.

### Out of Scope

- Removing Grok 4.3 or changing xAI's documented redirects for already retired slugs.
- Making Grok 4.20 Multi-Agent the application or xAI default.
- Adding xAI server-side web search, X search, code execution, files, compaction, or prompt-cache routing headers.
- Migrating the xAI adapter from Chat Completions to Responses.
- Adding image, video, or voice models.

## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | Good foundation | Thin OpenAI-compatible adapter with provider defaults. |
| Capability model | Too broad | Boolean effort support cannot express Grok 4.5's allowed values. |
| Implementation | Stale | Catalog stops at Grok 4.3 and Grok Build 0.1. |
| Tests & QA | Healthy baseline | xAI helper and model-override tests pass. |

## Architecture / Design Snapshot

Keep xAI capability metadata in `xai/config.py`. A model either has an explicit `frozenset` of accepted wire effort strings or an empty set, in which case the request builder omits `reasoning_effort`. Mapping and validation happen before the payload is returned, so an unsupported mode cannot become a provider-side 400.

Use the stable `grok-4.5` identifier because xAI recommends that alias for general use. Use dated `0309` IDs for the 4.20 beta variants to make experimental behavior reproducible. Labels must state that 4.20 is specialized/beta and that multi-agent can have different latency and orchestration characteristics.

## Workstreams & Tasks

### Workstream A - Catalog and defaults

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| A1 | Models | Add Grok 4.5 and three pinned Grok 4.20 configs. | Planned |
| A2 | Presets | Add effort variants and clear specialized labels. | Planned |
| A3 | Constructor | Advance `XAIArchitect` default to Grok 4.5 high. | Planned |
| A4 | Limits | Apply exact 500k and 1M context values. | Planned |

### Workstream B - Request safety

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| B1 | Capabilities | Replace boolean effort support with accepted values. | Planned |
| B2 | Mapping | Map enabled/default and validate explicit modes. | Planned |
| B3 | Rejection | Fail fast for Grok 4.5 none/xhigh/max. | Planned |
| B4 | Regression | Preserve Grok 4.3 and legacy redirect request shapes. | Planned |

### Workstream C - Evidence

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| C1 | Unit tests | Cover all Grok 4.5 efforts and 4.20 model IDs. | Planned |
| C2 | Limits | Assert every new context value and fallback. | Planned |
| C3 | Picker | Verify labels and retained old choices. | Planned |
| C4 | Quality | Run focused pytest, Ruff, Pyright, and import smoke. | Planned |

## Dependencies

- MS002 may add `ReasoningMode.MAX`; xAI tests must prove that new enum member is rejected for Grok 4.5 instead of being silently lowered.
- The existing OpenAI SDK transport must continue to accept xAI Chat Completions after any MS002 lock update.
- No xAI credentials are required for default completion.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Generic disabled reasoning sends undocumented `none` to Grok 4.5. | High | Model-specific accepted sets and pre-dispatch rejection. |
| 4.20 alias drift changes beta behavior. | Medium | Store dated model IDs and label them specialized/beta. |
| Multi-agent model requires a different endpoint. | Medium | Confirm Chat Completions support in a recording/live-gated smoke before exposing the preset. |
| OpenAI SDK upgrade affects xAI kwargs. | Medium | Run xAI request and client tests after lock refresh. |
| Context fallback under-packs or over-packs prompts. | Medium | Add exact limit tests for 4.5, 4.20, 4.3, and Grok Build. |

## Validation / QA Plan

Run from the repository root:

    .venv/bin/python -m pytest -q tests/unit/agents/test_xai_helpers.py tests/unit/test_model_overrides.py tests/unit/test_cli_model_picker_ui.py
    .venv/bin/python -m pytest -q tests/unit/agents/test_openai_helpers.py tests/unit/agents/test_deepseek_helpers.py
    .venv/bin/ruff check src/agentrules/core/types/models.py src/agentrules/config/agents.py src/agentrules/core/agents/xai tests/unit/agents/test_xai_helpers.py tests/unit/test_model_overrides.py tests/unit/test_cli_model_picker_ui.py
    .venv/bin/pyright src/agentrules/core/types/models.py src/agentrules/config/agents.py src/agentrules/core/agents/xai tests/unit/agents/test_xai_helpers.py tests/unit/test_model_overrides.py tests/unit/test_cli_model_picker_ui.py
    .venv/bin/python -c "import agentrules"

Green means exact payload tests show low/medium/high for Grok 4.5, invalid efforts fail locally, fixed 4.20 variants do not receive invented effort fields, context limits are exact, and all old xAI tests remain green. Optional live smoke is flag/key gated and may skip for regional 4.5 availability.

## Rollout / Ops Notes

This is additive except for the direct xAI constructor default. Existing explicit Grok 4.3 presets are unchanged. Users can roll back by selecting Grok 4.3 without reverting code. Release notes should distinguish 4.5's 500k context from 4.3/4.20's 1M and should not imply numerical naming determines release order or capability.

## Changelog

- 2026-07-15 — Created milestone scaffold.
- 2026-07-15 — Added the Grok 4.5/4.20 catalog, explicit effort capabilities, exact context policy, compatibility constraints, and validation plan.
