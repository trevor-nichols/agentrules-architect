---
id: EP-20261127-001/MS001
execplan_id: EP-20261127-001
ms: 1
title: Restore saved presets before provider cutovers
status: completed
domain: cross-cutting
owner: '@codex'
created: 2026-11-27
updated: '2026-11-27'
tags: []
risk: high
links:
  issue: ''
  docs: ''
  pr: ''
---

# Restore saved presets before provider cutovers

This milestone is a living document. Keep the YAML front matter accurate and log material changes in Changelog.

## Objective

People using retired OpenAI and xAI presets can run again, and saved Anthropic and Gemini selections continue working through the announced cutovers. Ship this slice against the October provider SDK lock so it can go out ahead of the new model choices.

## Definition of Done

- Existing retired saved keys resolve directly to active presets and appear with a useful replacement warning.
- Date-bound transitions preserve behavior before the cutoff and send the replacement's model, reasoning, and tool request fields on and after it.
- With no model specified, direct Gemini and its legacy wrapper send a valid request to a current model.
- Focused config, CLI, adapter, and offline integration checks pass. The README and lifecycle guide disclose changed behavior.

## Scope

Update `src/agentrules/core/configuration/model_presets.py`, picker metadata in `src/agentrules/config/agents.py`, and the Gemini adapter and legacy wrapper in `src/agentrules/core/agents/gemini/`. Keep dependency versions and phase defaults in place. The OpenAI December 11 route updates move with the new Terra capability in MS002.

## Current Health Snapshot

The October branch has the Gemini 3.8 Flash and 3.5 Flash-Lite capabilities, native Gemini tool replay, and both November 30 Anthropic Sonnet routes. Its o4-mini and Grok Build selections still target retired endpoints, and Gemini 2.5 has no saved-key cutoff.

## Architecture / Design Snapshot

The deprecation table follows one hop and uses a UTC date. Resolve a key once and keep the applied request profile coherent. Account for both passive config loading, which preserves the original key, and explicit picker replacement, which may save the canonical key.

## Workstreams & Tasks

1. Map `o4-mini-low`, `o4-mini-medium`, and `o4-mini-high` to `gpt56-terra-low`, `gpt56-terra-default`, and `gpt56-terra-high`. Map both `grok-build-0.1` and `grok-code-fast` directly to `grok-4.7` (high). Keep compatibility IDs loadable. Explain the recommended Grok replacement in the labels. Verify the existing date-bound Sonnet 4.5 redirects, including `claude-sonnet` to `claude-sonnet-5.5-between-tools` and `claude-sonnet-reasoning` to `claude-sonnet-5.5` on November 30.
2. On December 1, map `gemini-pro` to `gemini-3.8-flash` (medium), `gemini-flash` to `gemini-3.5-flash-lite` (minimal), and `gemini-flash-thinking` to `gemini-3.5-flash-lite-reasoning-medium`. The plain Flash key previously disabled thinking. Disclose that Flash-Lite uses thinking at minimal effort. Keep the live 2.5 Flash-Lite upstream endpoint out of this migration.
3. Set the no-argument `GeminiArchitect()` and legacy `GeminiAgent` wire model and effort together to 3.5 Flash-Lite with minimal thinking. Preserve prior behavior for explicit older model callers and treat an unsupported explicit effort as an error. Avoid rewriting arbitrary caller-supplied model IDs because custom provider gateways can use them. Pin old SDK parsing tests to explicit legacy models when their intent is to check legacy budget mode.
4. On January 22, 2027, map `claude-opus-4.5` to `claude-opus-5.5-reasoning-low` and `claude-opus-4.5-reasoning` to `claude-opus-5.5-reasoning-high`. Explain the disabled-to-adaptive change for the plain key. Update `README.md` and `docs/provider-model-lifecycle.md` with current dates and replacements.
5. Read the picker and warning paths for scheduled deprecations. Ensure the warnings explain the future change before the date and identify the effective replacement after the date. Date-sensitive tests should inject a date or freeze the resolver clock for passive config loading and picker checks.

## Dependencies

October provider refresh `261fbb5` and the locked SDKs already on its branch. OpenAI, xAI, Gemini, and Anthropic official retirement notices establish the dates and affected wire IDs.

## Risks & Mitigations

Using the retired names or chaining old aliases leaves active user configurations broken. Assert that each replacement exists, resolves in one hop, and is a live model. Passing the old `thinking_budget` to a Google-rerouted request can fail before inference. Assert the replacement's `thinking_level` and signed tool response shape. Treat terminal wrapping as display whitespace in warning assertions while checking the complete user-visible message.

## Validation / QA Plan

From the repository root, run these checks before and after the slice.

    uv run --python 3.11 --no-sync pytest -q tests/unit/test_openai_lifecycle.py tests/unit/test_model_overrides.py tests/unit/test_cli_model_picker_ui.py
    uv run --python 3.11 --no-sync pytest -q tests/unit/test_gemini_current_presets.py tests/unit/agents/test_gemini_agent_parsing.py tests/phase_1_test/test_phase1_gemini_tool_turn.py
    uv run --python 3.11 --no-sync pytest -q tests/unit/agents/test_anthropic_latest_contract.py tests/unit/test_provider_model_compatibility_matrix.py

Check the day before, day of, and day after each cutoff. Exercise both phase and researcher picker warnings. The fake Gemini transport should receive a current model and `thinking_level`. Reopening settings without saving should preserve the originally selected ID.

## Rollout / Ops Notes

Make this an independently releasable commit or PR slice on the October refresh. If a cutoff passes first, publish the same dated route so current users resolve to a live model immediately. A rollback for later milestones must retain these routes. For a provider access problem, document another supported choice without changing the user's stored setting automatically.

## Results

Locked Python 3.11 checks passed (1,168 tests, 77 subtests, Ruff, Pyright, import smoke, lock check, and diff check). Independent review passed with no actionable findings.

## Changelog

- 2026-11-27 — Recorded the first release slice and existing SDK compatibility.

[OpenAI deprecations](https://developers.openai.com/api/docs/deprecations) · [xAI release notes](https://docs.x.ai/developers/release-notes) · [Gemini deprecations](https://aistudio.google.com/docs/deprecations) · [Claude deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations)
