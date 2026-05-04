---
id: EP-20260309-001/MS001
execplan_id: EP-20260309-001
ms: 1
title: "Dynamic Codex runtime models in phase preset picker"
status: completed
domain: console
owner: "@codex"
created: 2026-03-09
updated: 2026-03-09
tags: [codex, model-presets, cli]
risk: med
links:
  issue: ""
  docs: ""
  pr: ""
---

# Dynamic Codex runtime models in phase preset picker

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Allow users to select live Codex app-server models in the phase preset menu, even when those models are not part of static internal presets.
Selection must remain backward compatible with existing config storage and be applied by the existing model override pipeline.

## Definition of Done

- [x] Implementation complete.
- [x] Validation complete.
- [x] Documentation and operational notes updated.

## Scope

### In Scope
- Introduce runtime Codex preset key parsing/building in `core/configuration/model_presets.py`.
- Resolve runtime keys to executable `ModelConfig` entries during phase config application.
- Merge live `codex app-server` model catalog entries into model preset options in `cli/ui/settings/models/__init__.py`.
- Add unit coverage and update Codex runtime operator docs.

### Out of Scope
- Removing static Codex presets.
- Cross-provider dynamic model catalogs.
- Archiving this milestone file (left active for now).

## Workstreams & Tasks

- [x] Workstream A: Runtime-key model preset resolver path.
- [x] Workstream B: Model settings UI runtime merge + tests/docs.

## Risks & Mitigations

- Risk: Duplicate model choices if runtime catalog includes models already hardcoded in static presets.
  Mitigation: Runtime catalog entries are deduped against existing static Codex model IDs before rendering choices.
- Risk: Runtime diagnostics failures could block model settings menu.
  Mitigation: Runtime model loading is best-effort and fails closed to static presets.

## Validation / QA Plan

- `ruff check src/agentrules/core/configuration/model_presets.py src/agentrules/cli/ui/settings/models/__init__.py tests/unit/test_model_overrides.py tests/unit/test_cli_codex_settings.py`
- `pytest -q tests/unit/test_model_overrides.py tests/unit/test_cli_codex_settings.py tests/unit/test_config_service.py`
- Expected: lint passes; targeted suites pass; dynamic runtime model key tests and runtime preset merge tests pass.

## Changelog

- 2026-03-09: Milestone created.
- 2026-03-09: Implemented dynamic Codex runtime model preset flow, added tests, and updated docs.
- 2026-03-09: Refined picker UX to show runtime-only Codex options (when available) and renamed labels from `Codex Runtime:` to `Codex:`.
