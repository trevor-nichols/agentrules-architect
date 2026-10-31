---
id: EP-20261023-001/MS001
execplan_id: EP-20261023-001
ms: 1
title: Lock contracts and correct urgent lifecycle routing
status: completed
domain: cross-cutting
owner: '@codex'
created: 2026-10-23
updated: '2026-10-23'
tags:
- contracts
- deepseek
- lifecycle
- gemini
risk: med
links:
  issue: ''
  docs: docs/provider-model-audit-2026-10.md
  pr: https://github.com/trevor-nichols/agentrules-architect/pull/42
---

# Lock contracts and correct urgent lifecycle routing

This milestone is a living document under `.agent/PLANS.md`. Start only after plan approval. Keep metadata and the parent Progress current.

## Objective

Old DeepSeek Flash selections resolve directly to the current V4.1 Flash wire model, and users see truthful Gemini lifecycle information. The implementation-day source matrix is recorded before provider code changes.

## Definition of Done

- Recheck official DeepSeek models/changelog and Google deprecation schedule; record URL, date, ID, limits, and effective aliases in the parent plan.
- Canonical `deepseek-flash` presets exist; all four `deepseek-v4-flash*` keys and `deepseek-chat`/`deepseek-reasoner` resolve in one hop to the appropriate non-thinking or thinking/effort canonical preset. V4 Pro and the 32K application output cap remain usable.
- Gemini 2.5 Flash/Pro are documented as active for prior users with access limitations; 3.7→3.8 and 3.5→3.6 upstream alias labels disclose the effective model.
- Focused tests, import smoke, ruff, pyright, and documentation checks pass; milestone status and parent Progress are updated.

## Scope

### In Scope
- `src/agentrules/core/configuration/model_presets.py`, `src/agentrules/core/agents/deepseek/config.py`, direct architect/defaults, `src/agentrules/config/agents.py`, picker labels, `docs/provider-model-lifecycle.md`, and `README.md`.
- Contract tests under `tests/unit/test_agents_deepseek.py` and existing model-preset/CLI suites. Verify stored key, runtime key, and wire ID separately.

### Out of Scope
- DeepSeek vision, Search/Fetch, an increased output cap, and new Gemini 3.8/4 requests.

## Workstreams & Tasks

- Capture implementation-day official source matrix; pause affected provider slice and amend plan if facts moved.
- Add canonical Flash profiles and direct one-hop compatibility mappings; align constructor aliases and defaults.
- Correct Gemini status and alias wording in config, picker, README, and lifecycle guide.
- Add behavior tests for old saved configs, direct constructor, final wire ID, and label text.

## Risks & Mitigations

- Risk: A legacy DeepSeek key redirects through another deprecated key and stops there. Mitigation: assert each old key's final canonical runtime key and wire ID in one resolution step.
- Risk: A Google alias appears to be an AgentRules-initiated migration. Mitigation: keep saved keys and distinguish the upstream effective model in labels/docs.

## Dependencies

User approval of the ExecPlan. No other milestone is required. Revalidation uses official pages linked in the audit.

## Validation / QA Plan

- From repository root run `.venv/bin/pytest -q tests/unit/test_agents_deepseek.py tests/unit/agents/test_deepseek_helpers.py` and relevant model-preset/CLI tests discovered with `rg -n 'resolve_runtime_preset_key|gemini-2.5' tests/unit`.
- Run `.venv/bin/python -c 'import agentrules; print("import ok")'`, `.venv/bin/ruff check .`, `.venv/bin/pyright`, and `git diff --check`. Expect no failures.
- Before/after check: an old Flash key loaded from a saved config retains its key but resolves to `deepseek-flash`; picker no longer claims Gemini 2.5 shut down on October 16.

## Rollout / Ops Notes

Ship lifecycle text and routing together. Retain all old keys for recovery. If source revalidation contradicts the audit, record the change in the parent Decision Log before implementing this slice.

## Changelog

- 2026-10-23: Defined urgent compatibility and lifecycle acceptance from the dated audit.
- 2026-10-23: User approved the plan; official DeepSeek and Google sources revalidated and recorded in the parent plan.
- 2026-10-23: Implemented canonical DeepSeek Flash routing and truthful Gemini lifecycle labels. Full offline unit, static, import, and diff checks passed; bugbot follow-up review found no remaining actionable issues.
