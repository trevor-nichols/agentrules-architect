---
id: EP-20260309-001
title: Enable dynamic Codex runtime model presets
status: archived
kind: feature
domain: console
owner: '@codex'
created: 2026-03-09
updated: '2026-03-09'
tags:
- codex
- model-presets
- cli
touches:
- cli
- agents
- tests
- docs
risk: med
breaking: false
migration: false
links:
  issue: ''
  pr: ''
  docs: ''
depends_on: []
supersedes: []
---

# EP-20260309-001 - Enable dynamic Codex runtime model presets

This ExecPlan is a living document. Keep `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` up to date as work proceeds.

If `.agent/PLANS.md` exists in this repository, maintain this plan in accordance with that guidance.

## Purpose / Big Picture

Users should be able to pick Codex models that are available in their live `codex app-server` model catalog, even when those models are not yet hardcoded in `src/agentrules/config/agents.py`.
After this change, users can configure phase presets with runtime-discovered Codex models directly from the CLI model picker, and pipeline execution resolves those selections into runnable Codex `ModelConfig` objects.
Verification is observable from the CLI and unit tests: runtime-only model IDs become selectable keys, are persisted, and are applied by `apply_user_overrides()`.

## Scope

In scope:
- Add a durable key format for runtime-only Codex selections (`codex-runtime:<model-id>`).
- Resolve runtime keys through the same model config pipeline used by static presets.
- Extend model settings UI to merge live Codex model catalog options into phase preset choices.
- Keep static presets and defaults unchanged.
- Add unit tests for resolver logic and CLI runtime-model merge behavior.
- Update Codex runtime documentation.

Out of scope:
- Removing static Codex presets.
- Adding dynamic model selection for non-Codex providers.
- Adding persistence of runtime catalog metadata beyond existing key storage.

## Progress

- [x] (2026-03-09 20:47Z) Created ExecPlan and milestone using CLI workflows (`execplan new`, `execplan milestone new`).
- [x] (2026-03-09 21:02Z) Implemented runtime Codex preset key format and dynamic resolver path in `core/configuration/model_presets.py`.
- [x] (2026-03-09 21:08Z) Implemented CLI model-picker merge of live Codex catalog models in `cli/ui/settings/models/__init__.py`.
- [x] (2026-03-09 21:11Z) Added tests for dynamic key application, runtime info generation, static-vs-runtime dedupe, and settings merge behavior.
- [x] (2026-03-09 21:13Z) Updated `docs/codex-runtime.md` to document runtime-discovered model options.
- [x] (2026-03-09 21:15Z) Validation completed: lint and targeted unit suites passed.
- [x] (2026-03-09 21:36Z) Refined UX: when runtime catalog is available, Codex options in model picker now come only from app-server listings and use `Codex: <model>` labels.

## Surprises & Discoveries

- Observation: The existing model settings flow already had a clean extension seam by augmenting the in-memory preset list before phase selection, so dynamic runtime models were added without changing persisted config schema.
  Evidence: `configure_models()` now calls `_load_runtime_codex_presets()` and `_merge_presets_with_runtime_codex()` before `_configure_general_phase()`.
- Observation: `apply_user_overrides()` previously dropped unknown keys silently, which blocked runtime-only model selection even though execution path can send arbitrary model IDs to Codex app-server.
  Evidence: Added runtime-key handling branch in `model_presets.apply_user_overrides()`.
- Observation: Showing both static Codex presets and runtime listings created duplicate/near-duplicate choices in the same menu, which reduced clarity.
  Evidence: Updated merge behavior to replace static Codex options with runtime options when runtime catalog is present.

## Decision Log

- Decision: Use `codex-runtime:<model-id>` as the canonical persisted key for runtime-only Codex models.
  Rationale: Stable, explicit, backward-compatible with existing `config.models: dict[str, str]` schema, and easy to parse/validate.
  Date/Author: 2026-03-09 / @codex
- Decision: Keep static `codex-*` presets and defaults while appending runtime-discovered models to the selection UI.
  Rationale: Preserves reproducible defaults and avoids breakage when runtime is unavailable, while still removing lag for new Codex models.
  Date/Author: 2026-03-09 / @codex
- Decision: Skip runtime catalog entries that duplicate existing static Codex model IDs.
  Rationale: Avoid duplicate choices and maintain clean UX while still exposing runtime-only additions.
  Date/Author: 2026-03-09 / @codex

## Outcomes & Retrospective

Implemented end-to-end dynamic Codex runtime model selection without migrating config formats or destabilizing existing presets.
Users can now select runtime-only Codex models from the phase preset menu; selections are persisted and applied to `MODEL_CONFIG` through a dedicated runtime key path.

Validation evidence:
- `ruff check src/agentrules/core/configuration/model_presets.py src/agentrules/cli/ui/settings/models/__init__.py tests/unit/test_model_overrides.py tests/unit/test_cli_codex_settings.py`
- `pytest -q tests/unit/test_model_overrides.py tests/unit/test_cli_codex_settings.py tests/unit/test_config_service.py`
- Result: all checks passed, 49 tests passed.

Remaining gap:
- Runtime catalog choices are fetched during the settings session only; no offline cache of model display metadata is stored. This is acceptable for current scope.
