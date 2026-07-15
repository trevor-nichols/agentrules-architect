---
id: EP-20260715-001/MS001
execplan_id: EP-20260715-001
ms: 1
title: Migrate DeepSeek to V4 before legacy retirement
status: completed
domain: backend
owner: '@codex'
created: 2026-07-15
updated: '2026-07-15'
tags:
- deepseek
- migration
- models
- deadline
risk: high
links:
  issue: ''
  docs: https://api-docs.deepseek.com/news/news260424/
  pr: ''
---

# Migrate DeepSeek to V4 before legacy retirement

This milestone is a living document. Keep the YAML front matter accurate, update this file as work proceeds, and record material revisions in `Changelog`.

## Objective

Move every normal AgentRules DeepSeek request to `deepseek-v4-flash` or `deepseek-v4-pro` before `deepseek-chat` and `deepseek-reasoner` become inaccessible on 2026-07-24. The result must expose V4 thinking and non-thinking modes explicitly, retain old saved preset keys through transparent compatibility redirects, and send payloads that match DeepSeek's current OpenAI-compatible API.

## Definition of Done

- [x] `deepseek-v4-flash` and `deepseek-v4-pro` have canonical model configs and user-facing presets for their useful thinking/non-thinking modes.
- [x] The generic `DeepSeekArchitect()` default uses V4 Flash rather than a retiring wire identifier.
- [x] Saved keys `deepseek-chat` and `deepseek-reasoner` still resolve, but send V4 Flash with thinking disabled and enabled respectively; labels disclose the redirect.
- [x] Thinking requests send `extra_body={"thinking": {"type": "enabled"}}` plus an accepted `reasoning_effort`; non-thinking requests explicitly send `type="disabled"`.
- [x] V4 thinking requests can carry function tools, and old reasoner-only tool suppression is not applied to V4.
- [x] V4 context metadata is 1,000,000 tokens and the output cap remains a conservative AgentRules limit rather than the provider's theoretical maximum.
- [x] Focused tests, import smoke, Ruff, and Pyright pass for all modified files.
- [x] Operator-facing model/deprecation documentation is accurate, and this milestone is marked completed only after evidence is recorded.

## Scope

### In Scope

- Update `src/agentrules/core/types/models.py` with V4 Pro and Flash configs. Define thinking-high and non-thinking configs for both families; add a max-effort Pro config only if it maps cleanly through the existing enum during this milestone.
- Update `src/agentrules/config/agents.py` with canonical presets, compatibility redirects, exact 1M context metadata, and descriptions that name the July 24 retirement.
- Update `src/agentrules/core/agents/deepseek/config.py` so `ModelDefaults` expresses thinking support, default reasoning, accepted effort values, tool support, and conservative output limits.
- Update `src/agentrules/core/agents/deepseek/request_builder.py` to translate `ReasoningMode` into the documented thinking toggle and effort. `LOW` and `MEDIUM` may normalize to `high`; `XHIGH` may normalize to `max`; `DISABLED` must omit effort and explicitly disable thinking.
- Update `src/agentrules/core/agents/deepseek/architect.py`, `tooling.py`, response fixtures, and tests as needed for the V4 contract.
- Verify whether AgentRules continues a provider-native tool turn or starts a fresh prompt after a returned tool call. If it continues the same DeepSeek conversation, preserve `reasoning_content` exactly as DeepSeek requires; if it starts a fresh request, document that no provider-native message history is replayed.

### Out of Scope

- Adding the Anthropic-compatible DeepSeek endpoint; AgentRules retains its existing OpenAI-compatible client path.
- Raising generation limits to DeepSeek's maximum 384k output, which would create uncontrolled cost and latency.
- Reworking the provider-neutral tool loop beyond what is necessary to keep V4 tool calls valid.
- Removing legacy preset keys or creating a generic provider lifecycle framework.

## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | Healthy | V4 model identity, thinking mode, sampling, tools, and accepted effort values are modeled independently. |
| Implementation | Complete | Canonical V4 presets and adapter-boundary compatibility aliases prevent retired wire IDs from being sent. |
| Tests & QA | Green | 125 focused tests and 3 subtests pass; Ruff, Pyright, and import smoke also pass. |
| Docs & runbooks | Current | README and preset labels disclose V4 behavior and the July 24 alias retirement. |

Implementation began and completed on 2026-07-15 after explicit user approval. The pre-change and post-change focused provider suites were green.

## Architecture / Design Snapshot

One V4 identifier supports both thinking and non-thinking. Therefore model identity and reasoning mode must be independent. `ModelDefaults` remains the single source of provider defaults, while the pure request builder owns wire translation. The architect should not infer capabilities with direct string comparisons.

Use V4 Flash as the new constructor default because it is DeepSeek's economical general tier and the current legacy aliases already route to it temporarily. Use V4 Pro as the explicit higher-capability choice. Preserve the old preset keys by changing the config behind each key, not by sending a retired slug after its deadline.

Temperature is permitted only for non-thinking requests. Thinking mode ignores sampling parameters, so the architect must suppress temperature before dispatch rather than send a misleading setting. Tools are allowed in both V4 modes; the old `deepseek-reasoner` restriction remains relevant only to that historical wire model while compatibility configs no longer use it.

## Workstreams & Tasks

### Workstream A - Model and preset migration

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| A1 | Models | Add V4 Flash/Pro configs with explicit reasoning modes. | Complete |
| A2 | Presets | Add canonical V4 choices and redirect the two legacy keys. | Complete |
| A3 | Limits | Assign 1M context and a conservative output policy. | Complete |
| A4 | Defaults | Change `DeepSeekArchitect` default to V4 Flash. | Complete |

### Workstream B - Wire contract

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| B1 | Config | Replace model-ID inference with explicit thinking/effort capabilities. | Complete |
| B2 | Request | Add `extra_body.thinking` and normalized `reasoning_effort`. | Complete |
| B3 | Tools | Permit V4 thinking tool calls and verify turn-history handling. | Complete |
| B4 | Sampling | Suppress temperature for thinking requests only. | Complete |

### Workstream C - Evidence

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| C1 | Unit tests | Assert exact enabled/disabled/high/max payload variants. | Complete |
| C2 | Compatibility | Assert legacy keys resolve to V4 semantics. | Complete |
| C3 | Parsing | Preserve reasoning content and tool-call extraction. | Complete |
| C4 | Quality | Run focused pytest, Ruff, Pyright, and import smoke. | Complete |

## Dependencies

- No other milestone must land first.
- The existing OpenAI SDK remains the transport dependency. This milestone should avoid an SDK upgrade unless the installed client cannot pass `extra_body`; any shared SDK upgrade is coordinated with MS002 and revalidated against both providers.
- Official contract facts are embedded above; live credentials are not required for completion.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| July 24 retirement arrives before the full provider refresh is complete. | High | Keep MS001 independently releasable and do not make it depend on later model work. |
| A saved legacy preset silently changes reasoning behavior. | High | Map chat to explicit disabled thinking and reasoner to explicit enabled/high, with tests and disclosed labels. |
| `extra_body` is nested incorrectly and appears in the JSON body under the wrong key. | High | Assert the exact kwargs passed to `chat.completions.create` with a recording fake. |
| Thinking-mode tool continuation loses `reasoning_content`. | Medium | Trace the existing tool loop and add a regression test for whichever continuation model AgentRules actually uses. |
| A 1M context is treated as a 1M generation budget. | Medium | Change context metadata only; retain conservative max output tokens. |

## Validation / QA Plan

Run from the repository root:

    .venv/bin/python -m pytest -q tests/unit/agents/test_deepseek_helpers.py tests/unit/test_agents_deepseek.py tests/unit/agents/test_deepseek_agent_parsing.py tests/unit/test_model_overrides.py
    .venv/bin/ruff check src/agentrules/core/types/models.py src/agentrules/config/agents.py src/agentrules/core/agents/deepseek tests/unit/agents/test_deepseek_helpers.py tests/unit/test_agents_deepseek.py tests/unit/agents/test_deepseek_agent_parsing.py tests/unit/test_model_overrides.py
    .venv/bin/pyright src/agentrules/core/types/models.py src/agentrules/config/agents.py src/agentrules/core/agents/deepseek tests/unit/agents/test_deepseek_helpers.py tests/unit/test_agents_deepseek.py tests/unit/agents/test_deepseek_agent_parsing.py tests/unit/test_model_overrides.py
    .venv/bin/python -c "import agentrules"

Green means all commands exit zero and new tests demonstrate enabled, disabled, effort normalization, tools, compatibility redirects, and 1M context. An optional live smoke may make a minimal V4 Flash request only when `AGENTRULES_RUN_DEEPSEEK_LIVE=1`, `--run-live`, and a key are all present; a default skip is expected.

Validation evidence recorded on 2026-07-15:

- Focused provider/configuration/token/streaming/structured-output suite: `125 passed, 3 subtests passed in 2.88s`.
- Ruff on all modified Python source and test paths: `All checks passed!`.
- Pyright on the modified DeepSeek, model, preset, and configuration paths: `0 errors, 0 warnings, 0 informations`.
- Import smoke resolved `agentrules` from `src/agentrules/__init__.py` and exited zero.
- The Phase 1 researcher loop rebuilds `context_payload` from `base_context` and embeds normalized tool feedback on every iteration. It starts a fresh provider request rather than replaying DeepSeek assistant messages, so provider-native `reasoning_content` continuation is not required.

## Rollout / Ops Notes

This is an in-place compatibility migration. It needs no data backfill. Users with old DeepSeek preset keys receive V4 Flash with the closest explicit old semantics. Rollback is the milestone commit, but after July 24 a rollback restores identifiers known to fail, so release recovery should fix forward unless the provider extends the deadline.

## Changelog

- 2026-07-15 — Created milestone scaffold.
- 2026-07-15 — Replaced scaffold with the DeepSeek V4 migration design, compatibility mapping, deadline controls, and validation gates.
- 2026-07-15 — Marked the milestone in progress after the user approved sequential execution.
- 2026-07-15 — Added V4 Flash/Pro presets, explicit thinking and effort payloads, 1M limits, tool support, legacy preset and constructor redirects, parsing coverage, and operator guidance.
- 2026-07-15 — Completed all focused validation with 125 tests and 3 subtests passing, plus clean Ruff, Pyright, and import-smoke results; marked the milestone complete for archival.
