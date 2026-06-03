---
id: EP-20260602-001
title: Codex runtime default and catalog validation
status: done
kind: feature
domain: backend
owner: '@codex'
created: 2026-06-02
updated: '2026-06-02'
tags:
- codex
- models
- validation
touches:
- cli
- agents
- tests
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

# EP-20260602-001 - Codex runtime default and catalog validation

This ExecPlan is a living document. Keep `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` up to date as work proceeds.

If `.agent/PLANS.md` exists in this repository, maintain this plan in accordance with that guidance.

## Purpose / Big Picture

Codex-auth model availability should follow the live Codex catalog instead of forcing repository updates whenever OpenAI changes the subscription model list. After this change, operators can choose a stable `Codex runtime default` preset that follows the current runtime default model automatically, while explicitly pinned Codex models are validated against the live catalog before execution.

You can verify the behavior by opening the model preset picker and confirming that the Codex section contains a `Codex runtime default` entry sourced from the runtime catalog, then by running the targeted Codex test suite and observing that unavailable pinned models fail with a clear error while the runtime-default preset resolves successfully.

## Scope

In scope: Codex runtime preset generation, Codex preset compatibility normalization, runtime-default modeling, request-time validation of pinned Codex models, and regression tests.

Out of scope: changing OpenAI preset behavior outside the Codex runtime path, adding persisted catalog caching, or redesigning the general model selection UI beyond the Codex-specific additions needed here.

## Progress

- [x] Initial draft created.
- [x] Added a `Codex runtime default` preset path and preserved legacy static Codex aliases for compatibility.
- [x] Added request-time Codex catalog validation and runtime-default resolution in the Codex architect flow.
- [x] Added regression coverage for preset generation, legacy alias normalization, runtime-default request building, and Codex runtime execution failures.
- [x] Validation complete.

## Surprises & Discoveries

- The existing CLI picker already replaced static Codex presets with runtime-discovered ones when the runtime catalog was available. The missing piece was execution-time validation, not picker-time discovery.
- The legacy `codex-gpt-5.4` preset routed through the pinned OpenAI snapshot name `gpt-5.4-2026-03-05`, which does not match the runtime catalog name `gpt-5.4`. A compatibility alias was needed so existing saved selections still normalize cleanly.

## Decision Log

- The runtime catalog is the source of truth for Codex-auth model availability. Static Codex presets remain only as compatibility paths for stored selections and older configs.
- `Codex runtime default` is represented as a dedicated preset key and an internal sentinel model name so it can follow the live default model on every run instead of freezing to a concrete model during configuration.
- Validation happens in the Codex architect execution path instead of shared CLI bootstrap so stale Codex selections do not block unrelated commands like `configure`, `keys`, or `execplan`.

## Outcomes & Retrospective

Implemented behavior:

- The Codex picker now includes a first-class `Codex runtime default` preset when the live runtime catalog is available.
- Saved Codex runtime-default selections rebuild into a Codex model config without pinning a concrete model name into persisted config.
- Codex requests resolve the runtime default model at execution time and validate pinned model names and reasoning efforts against the live catalog before `thread/start`.
- The legacy `codex-gpt-5.4` selection now normalizes to the runtime `gpt-5.4` model name.

Validation evidence:

- `uv run python -m pytest tests/unit/test_model_overrides.py tests/unit/test_cli_codex_settings.py tests/unit/agents/test_codex_request_builder.py tests/unit/agents/test_codex_architect.py tests/unit/test_codex_runtime_service.py`
- `uv run ruff check src/agentrules/core/configuration/model_presets.py src/agentrules/core/agents/codex/request_builder.py src/agentrules/core/agents/codex/architect.py src/agentrules/core/agents/codex/model_selection.py src/agentrules/cli/ui/settings/models/__init__.py tests/unit/test_model_overrides.py tests/unit/test_cli_codex_settings.py tests/unit/agents/test_codex_request_builder.py tests/unit/agents/test_codex_architect.py tests/fakes/codex_app_server.py`
- `uv run pyright src/agentrules/core/configuration/model_presets.py src/agentrules/core/agents/codex/request_builder.py src/agentrules/core/agents/codex/architect.py src/agentrules/core/agents/codex/model_selection.py src/agentrules/cli/ui/settings/models/__init__.py`
- `uv run python -c "import agentrules"`

Follow-up ideas, not required for this change:

- Add short-lived catalog caching if repeated Codex requests show noticeable overhead.
- Surface the resolved runtime-default model name in more CLI status views if operators want deeper visibility without opening the Codex runtime screen.
