---
id: EP-20260306-002
title: "Add Gemini 3 family preview models with explicit capability profiles"
status: done
kind: refactor
domain: backend
owner: "@codex"
created: 2026-03-06
updated: 2026-03-06
tags: [gemini, google, models]
touches: [agents, tests]
risk: low
breaking: false
migration: false
links:
  issue: ""
  pr: ""
  docs: "https://ai.google.dev/gemini-api/docs/gemini-3"
depends_on: []
supersedes: []
---

# EP-20260306-002 - Add Gemini 3 family preview models with explicit capability profiles

This ExecPlan is a living document. Keep `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` up to date as work proceeds.

If `.agent/PLANS.md` exists in this repository, maintain this plan in accordance with that guidance.

## Purpose / Big Picture

Users need to select the newly available Google Gemini preview models `gemini-3-flash-preview`, `gemini-3.1-flash-lite-preview`, and `gemini-3.1-pro-preview` from the app without inheriting incorrect behavior from older Gemini model heuristics. The Google API transport remains the same, but Gemini 3 family models use `thinking_level`, and Flash-family models support more levels than Pro-family models.

The visible outcome is that the new Gemini models appear in the preset registry, Gemini 3 family requests use the correct `thinking_level` mapping for their model family, and the validation suite demonstrates the new mappings and preset exposure.

## Scope

In scope:
- Add model configs and presets for the requested Gemini 3 preview model IDs.
- Refactor Gemini model-family capability handling into explicit metadata instead of broad `"gemini-3"` string checks.
- Update tests for Gemini 3 family thinking-level behavior and preset registry exposure.

Out of scope:
- Removing or renaming existing Gemini presets.
- Changing the Gemini transport client or request schema.
- Broad UI redesign of provider/model selection.

## Progress

- [x] (2026-03-06) Created ExecPlan for Gemini 3 family model additions and capability cleanup.
- [x] (2026-03-06) Replace coarse Gemini family branching with explicit capability profiles.
- [x] (2026-03-06) Add the requested Gemini 3 preview model configs and presets.
- [x] (2026-03-06) Add and update tests for Gemini 3 family behavior and preset exposure.
- [x] (2026-03-06) Run targeted pytest, ruff, pyright, import-smoke, and registry validation.

## Surprises & Discoveries

- The existing Gemini architect already uses `thinking_level` for any model whose name contains `"gemini-3"`, which is close but too coarse for Gemini 3 Pro vs Gemini 3 Flash family differences.
  - Evidence: `src/agentrules/core/agents/gemini/architect.py` currently routes all `"gemini-3"` models through a single `_map_reasoning_mode_to_thinking_level()` path and only canonicalizes `"gemini-3-pro"` in `_stable_model_name()`.

## Decision Log

- Decision: Introduce a Gemini capability helper module instead of extending the architect’s string checks.
  Rationale: The Gemini 3 family now contains multiple related preview models with distinct thinking-level semantics, and future additions should be a metadata update rather than more branching.
  Date/Author: 2026-03-06 / @codex

- Decision: Preserve the existing Gemini API request shape and only change model classification plus preset exposure.
  Rationale: Google’s current Gemini 3 and thinking docs show the same `generateContent` pathway and `thinkingConfig` transport.
  Date/Author: 2026-03-06 / @codex

## Outcomes & Retrospective

Completed outcomes:
- Added a Gemini capability helper module that distinguishes Gemini 2.5, Gemini 3 Pro-family, and Gemini 3 Flash-family behavior.
- Added the requested model configs and app presets for `gemini-3-flash-preview`, `gemini-3.1-flash-lite-preview`, and `gemini-3.1-pro-preview`.
- Updated Gemini thinking-level mapping so Flash-family models can use `minimal` and `medium` while Pro-family models continue to collapse to `low` or `high`.
- Added tests for capability resolution, architect thinking-level behavior, structured output + tools behavior, and preset exposure.

Validation executed:
- `PYTHONPATH=src pytest tests/unit/agents/test_gemini_capabilities.py tests/unit/agents/test_gemini_agent_parsing.py tests/unit/test_agents_gemini_error.py tests/unit/test_streaming_support.py tests/unit/test_model_overrides.py tests/unit/test_model_config_helper.py`
- `ruff check src/agentrules/core/agents/gemini/capabilities.py src/agentrules/core/agents/gemini/architect.py src/agentrules/core/types/models.py src/agentrules/config/agents.py tests/unit/agents/test_gemini_capabilities.py tests/unit/agents/test_gemini_agent_parsing.py tests/unit/test_model_overrides.py .agent/exec_plans/active/gemini-3-family/EP-20260306-002_gemini-3-family.md`
- `pyright src/agentrules/core/agents/gemini/capabilities.py src/agentrules/core/agents/gemini/architect.py src/agentrules/core/types/models.py src/agentrules/config/agents.py tests/unit/agents/test_gemini_capabilities.py tests/unit/agents/test_gemini_agent_parsing.py tests/unit/test_model_overrides.py`
- `PYTHONPATH=src python -c "import agentrules"`
