---
id: EP-20260715-001/MS002
execplan_id: EP-20260715-001
ms: 2
title: Add OpenAI GPT-5.6 model family
status: completed
domain: backend
owner: '@codex'
created: 2026-07-15
updated: '2026-07-15'
tags:
- openai
- gpt-5-6
- responses-api
- defaults
risk: med
links:
  issue: ''
  docs: https://developers.openai.com/api/docs/guides/latest-model
  pr: ''
---

# Add OpenAI GPT-5.6 model family

This milestone is a living document. Keep the YAML front matter accurate, update this file as work proceeds, and record material revisions in `Changelog`.

## Objective

Make GPT-5.6 Sol, Terra, and Luna first-class direct OpenAI choices and advance new/default AgentRules phases from GPT-5.5 to GPT-5.6 Sol. Requests must use the Responses API, preserve the new `max` reasoning effort, apply the official context limit, and leave every existing GPT-5.5 preset usable.

## Definition of Done

- [x] `gpt-5.6-sol`, `gpt-5.6-terra`, and `gpt-5.6-luna` have explicit model configs and presets.
- [x] Sol exposes none/low/medium/high/xhigh/max variants consistent with the existing GPT-5.5 preset pattern; Terra and Luna expose a smaller intentional set suited to balanced and high-volume workloads.
- [x] `ReasoningMode.MAX` exists and reaches the OpenAI Responses payload as `{"effort": "max"}` without degrading to `high`.
- [x] GPT-5.6 model prefixes resolve to Responses API defaults before the generic `gpt-5` prefix.
- [x] GPT-5.6 context metadata uses the official 1,050,000-token context and retains AgentRules' safety margin policy.
- [x] `MODEL_PRESET_DEFAULTS` points every unoverridden phase and the researcher to the Sol medium preset; explicit GPT-5.5 selections continue to resolve unchanged.
- [x] The locked OpenAI SDK accepts the final request fields used by AgentRules; the dependency is upgraded and locked if necessary.
- [x] Focused OpenAI, model-override, picker, import, Ruff, and Pyright validation passes.

## Scope

### In Scope

- Add GPT-5.6 configs in `src/agentrules/core/types/models.py` and user-facing presets in `src/agentrules/config/agents.py`.
- Add `MAX = "max"` to `ReasoningMode` and update every exhaustive mapper or formatter that must understand it. Provider adapters that do not support max must continue to reject, normalize, or omit it according to their own capability metadata.
- Update `_GPT5_RESPONSES_REASONING_SUPPORT` and `_PREFIX_DEFAULTS` so Sol, Terra, Luna, and the `gpt-5.6` alias are classified before the broad `gpt-5` fallback.
- Use the explicit tier IDs in presets. Do not use the moving `gpt-5.6` alias as the stored canonical model name.
- Create Sol preset keys `gpt56-sol-none`, `gpt56-sol-low`, `gpt56-sol-default`, `gpt56-sol-high`, `gpt56-sol-xhigh`, and `gpt56-sol-max`. Create a medium/default and high choice for Terra, and low/default choices for Luna, unless implementation-time SDK inspection shows a tier-specific effort restriction that must be represented more narrowly.
- Update tests and any CLI labels or descriptions that identify the application default.

### Out of Scope

- OpenAI `reasoning.mode="pro"`, which is a separate optional request mode and not necessary for ordinary GPT-5.6 support.
- Removing GPT-5.5, changing existing GPT-5.5 preset keys, or automatically rewriting explicit saved choices.
- Adding static GPT-5.6 presets to Codex; Codex gets models from its installed app-server.
- Adopting new Responses API features unrelated to model selection, such as new tools or conversation storage.

## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | Healthy | OpenAI already has Responses-specific config and effort maps. |
| Implementation | Complete | Sol, Terra, and Luna are explicit Responses presets; Sol medium is the new application default. |
| Tests & QA | Green | 171 focused tests and 31 subtests pass; repository-wide Ruff and Pyright are clean. |
| Dependencies | Current | OpenAI SDK 2.45.0 is locked and its typed effort literal includes `max`. |

## Architecture / Design Snapshot

Use explicit model IDs because the three tiers have different performance and pricing roles. Sol is the application default; Terra and Luna are alternatives, not aliases for Sol. Keep request behavior capability-driven in the existing OpenAI config and request-builder modules.

The shared reasoning enum gains `MAX` because direct AgentRules presets need to store and reproduce that OpenAI effort. This does not imply every provider accepts max. Anthropic already stores its effort separately, Codex retains runtime-owned strings, DeepSeek may map max or xhigh to its accepted value, and xAI must reject max for Grok 4.5.

The dependency decision is evidence-based. Inspect the installed and candidate SDK `responses.create` signature and reasoning effort types. Upgrade `pyproject.toml` and regenerate `uv.lock` only if the current lock cannot represent or safely pass the selected fields. Do not edit `uv.lock` manually.

## Workstreams & Tasks

### Workstream A - Shared and model metadata

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| A1 | Reasoning | Add `ReasoningMode.MAX` and update exhaustive mappings. | Complete |
| A2 | Models | Add explicit Sol, Terra, and Luna configs. | Complete |
| A3 | Limits | Apply 1,050,000-token context metadata. | Complete |
| A4 | Defaults | Advance phase defaults to Sol medium. | Complete |

### Workstream B - OpenAI wire support

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| B1 | Config | Add GPT-5.6 prefixes before generic GPT-5 fallbacks. | Complete |
| B2 | Request | Preserve every documented effort through `max`. | Complete |
| B3 | SDK | Verify or upgrade the OpenAI dependency and regenerate the lock. | Complete |
| B4 | Regression | Prove chat-only and older Responses models retain their request shapes. | Complete |

### Workstream C - UX and evidence

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| C1 | Presets | Add clear tier and effort labels without removing GPT-5.5. | Complete |
| C2 | Picker | Verify default and explicit legacy selections in CLI tests. | Complete |
| C3 | Unit tests | Assert model resolution, effort payloads, and context limits. | Complete |
| C4 | Quality | Run focused pytest, Ruff, Pyright, and import smoke. | Complete |

## Dependencies

- MS001 should land first because of its deadline. If this milestone upgrades the shared OpenAI SDK, rerun the DeepSeek tests before completion.
- The OpenAI SDK candidate must remain compatible with DeepSeek and xAI's OpenAI-compatible clients.
- No OpenAI API key is required for default validation.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Prefix ordering classifies GPT-5.6 as a generic older GPT-5 model. | High | Add explicit prefix-order tests for Sol, Terra, Luna, and alias forms. |
| Adding `MAX` breaks an exhaustive provider mapper. | High | Search every `ReasoningMode` branch and add provider-specific tests for unsupported behavior. |
| A dependency update changes DeepSeek or xAI client behavior. | Medium | Run all three OpenAI-compatible provider suites after `uv lock` and `uv sync`. |
| Changing the default rewrites a user's explicit choice. | Medium | Change only `MODEL_PRESET_DEFAULTS`; test explicit GPT-5.5 config round trips. |
| Context metadata is confused with output capacity. | Medium | Set only the input/context field and retain existing output-token policy. |

## Validation / QA Plan

Run from the repository root:

    .venv/bin/python -m pytest -q tests/test_openai_responses.py tests/unit/agents/test_openai_helpers.py tests/unit/test_agents_openai_params.py tests/unit/test_model_overrides.py tests/unit/test_cli_model_picker_ui.py
    .venv/bin/python -m pytest -q tests/unit/agents/test_deepseek_helpers.py tests/unit/agents/test_xai_helpers.py
    .venv/bin/ruff check src/agentrules/core/agents/base.py src/agentrules/core/types/models.py src/agentrules/config/agents.py src/agentrules/core/agents/openai tests/test_openai_responses.py tests/unit/agents/test_openai_helpers.py tests/unit/test_agents_openai_params.py tests/unit/test_model_overrides.py tests/unit/test_cli_model_picker_ui.py
    .venv/bin/pyright src/agentrules/core/agents/base.py src/agentrules/core/types/models.py src/agentrules/config/agents.py src/agentrules/core/agents/openai tests/test_openai_responses.py tests/unit/agents/test_openai_helpers.py tests/unit/test_agents_openai_params.py tests/unit/test_model_overrides.py tests/unit/test_cli_model_picker_ui.py
    .venv/bin/python -c "import agentrules"

Green means max is preserved in a Sol Responses payload, explicit tier IDs resolve to the correct defaults, context is exact, the default preset is Sol medium, GPT-5.5 remains selectable, and DeepSeek/xAI regression tests still pass. An optional live smoke must be credential- and flag-gated and use a minimal token cap.

Validation evidence recorded on 2026-07-15:

- Official model pages for Sol, Terra, and Luna each report a 1,050,000-token context, 922,000-token maximum input, 128,000-token maximum output, and Responses support.
- The official latest-model guide lists `none`, `low`, `medium`, `high`, `xhigh`, and `max`, identifies Sol as flagship, Terra as balanced-cost, Luna as high-volume, and confirms the `gpt-5.6` alias routes to Sol.
- OpenAI SDK 2.21.0 lacked `max` in `ReasoningEffort`; the regenerated lock installs 2.45.0, whose literal contains `max`. `uv sync --extra dev` completed successfully.
- Focused OpenAI, default/picker, token-limit, DeepSeek, and xAI regression suite: `171 passed, 31 subtests passed in 4.97s`.
- Repository-wide Ruff: `All checks passed!`.
- Repository-wide Pyright: `0 errors, 0 warnings, 0 informations`.
- Import smoke resolved `agentrules` from `src/agentrules/__init__.py` and exited zero.

## Rollout / Ops Notes

This is an additive model migration plus a new default. Rollback restores the prior default and removes new presets, but existing saved configurations created with GPT-5.6 keys would then stop resolving. Therefore keep the compatibility boundary clear in release notes and prefer fixing forward after release. GPT-5.5 remains an immediate fallback choice if GPT-5.6 availability differs by account.

## Changelog

- 2026-07-15 — Created milestone scaffold.
- 2026-07-15 — Added the GPT-5.6 tier strategy, max-effort interface, default migration, dependency gate, and validation plan.
- 2026-07-15 — Marked the milestone in progress after MS001 was validated, archived, and committed.
- 2026-07-15 — Added explicit Sol/Terra/Luna configs and presets, first-class max reasoning, exact context metadata, and the Sol-medium application default while retaining GPT-5.5.
- 2026-07-15 — Upgraded and locked OpenAI SDK 2.45.0 after confirming its typed request contract includes max effort.
- 2026-07-15 — Completed validation with 171 tests and 31 subtests plus clean repository-wide Ruff, Pyright, and import smoke; marked the milestone complete for archival.
