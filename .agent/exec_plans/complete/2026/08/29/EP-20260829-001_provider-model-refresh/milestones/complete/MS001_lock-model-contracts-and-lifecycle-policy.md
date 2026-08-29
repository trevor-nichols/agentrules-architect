---
id: EP-20260829-001/MS001
execplan_id: EP-20260829-001
ms: 1
title: Lock Model Contracts and Lifecycle Policy
status: completed
domain: cross-cutting
owner: '@codex'
created: 2026-08-29
updated: '2026-08-29'
tags:
- providers
- research
- contracts
- lifecycle
risk: med
links:
  issue: ''
  docs: ''
  pr: ''
---

# Lock Model Contracts and Lifecycle Policy

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Freeze an implementation-day, source-backed contract for every model and migration in EP-20260829-001 before runtime behavior changes. This milestone protects the implementation from catalog drift and ensures the existing provider baseline is green. Its output is an approved contract update in the parent ExecPlan and recorded validation evidence; it does not expose a new picker entry.

## Definition of Done

- [x] Every upstream source in the parent plan was reopened and checked on 2026-08-29.
- [x] Model IDs, context limits, supported efforts, thinking-disable behavior, transport, tool/structured-output compatibility, and lifecycle state match the amended parent contract table.
- [x] Each compatibility migration has one existing legacy key and one registered canonical target planned; no legacy key is scheduled for deletion.
- [x] The targeted offline baseline passed: 166 tests and 8 subtests in 3.11 seconds.
- [x] No provider runtime behavior, dependency version, phase default, or paid external API state changed in this milestone.
- [x] Parent `Progress`, `Surprises & Discoveries`, and `Decision Log` record the DeepSeek mapping discovery.

## Scope

### In Scope

- Revalidate official Anthropic, Gemini, xAI, DeepSeek, and OpenAI model documentation.
- Confirm that direct API providers own static registry entries while Codex and Claude Code retain runtime-owned model resolution.
- Confirm the exact preset-key matrix, effort matrix, fallbacks, exclusions, and compatibility redirects described by the parent plan.
- Run the import smoke and targeted provider contract baseline.
- Amend planning artifacts if facts changed; pause only the affected provider slice when its contract is no longer established.

### Out of Scope

- No edits under `src/agentrules` or `tests`.
- No new presets, aliases, capability profiles, request payloads, dependencies, or defaults.
- No live provider calls, account availability probes, quota checks, or model pricing comparison.
- No inference from third-party model aggregators when official documentation is unavailable.

## Current Health Snapshot

| Area | Starting state | Milestone target |
| --- | --- | --- |
| Branch | `codex/provider-model-refresh-2026-08` created from clean `main` | Same branch; only planning files changed |
| Import | Previously healthy | `uv run python -c "import agentrules"` exits 0 |
| Targeted provider suite | 166 passed plus 8 subtests on 2026-08-29 | Same tests pass on implementation day |
| Static direct registry | Last substantial refresh in July 2026 | Dated target matrix reconfirmed |
| Codex catalog | Runtime `model/list` discovery already tested | Ownership boundary explicitly preserved |
| Lifecycle map | DeepSeek/Gemini/xAI mappings exist; OpenAI gaps remain | Exact new redirects approved before coding |

## Architecture / Design

Treat the contract table in the parent ExecPlan as a precondition, not as a guess. A source establishes a model only when it names the wire ID and the capability needed by this adapter. Marketing release notes alone are insufficient when they do not specify reasoning values or endpoint compatibility.

The contract review must distinguish provider ceilings from AgentRules operational choices. For example, DeepSeek's upstream output ceiling does not automatically replace AgentRules' 32K application cap. Record both values and keep the product decision explicit.

The contract review must also distinguish a direct API model from a local runtime selection. An OpenAI API catalog entry does not authorize a static Codex picker entry, and an Anthropic API entry does not establish a pinned Claude Code minimum runtime version.

## Workstreams & Tasks

### Workstream A - Revalidate direct-provider model contracts

- [x] Opened Anthropic's current Opus 5 and effort pages; confirmed wire ID, 1M/128K limits, adaptive default, disabled-thinking restriction, and low-through-max effort set.
- [x] Opened Gemini's current model catalog and thinking pages; confirmed IDs, defaults/levels, 1,048,576/65,536 limits, structured output, and tools.
- [x] Opened xAI's Grok 4.6 and reasoning pages; confirmed 500K context, low/medium/high/xhigh, high default, inability to disable reasoning, tools, and structured output.
- [x] Opened DeepSeek's update, thinking, and pricing pages; confirmed V4 IDs, 1M/384K provider limits, low/high/max native efforts, disabled thinking, and medium/xhigh-to-high compatibility mapping.
- [x] Opened official OpenAI model pages; confirmed existing GPT-5.6 catalog, o4-mini successor guidance, and deprecated GPT-5.1/5.2 Codex status.

### Workstream B - Lock compatibility and exclusion decisions

- [x] Verified `o4-mini-low`, `o4-mini-medium`, and `o4-mini-high` and their effort-preserving planned GPT-5 Mini targets.
- [x] Verified direct and static-derived `gpt-5.1-codex`/`gpt-5.2-codex` keys before their planned redirects.
- [x] Verified generic/pinned Opus, DeepSeek legacy, and Codex runtime default keys remain registered.
- [x] Reconfirmed all exclusions: no static GPT-5.6 Codex, pinned Claude Code Opus 5, unsupported Pro modes, Grok Multi-Agent, or DeepSeek Vision Experimental.

### Workstream C - Establish a clean baseline

- [x] Ran the import smoke and targeted tests from the parent plan.
- [x] Recorded exact pass counts and elapsed time in this milestone's changelog.
- [x] Baseline was green; no unrelated-failure investigation was needed.
- [x] Updated the parent ExecPlan and MS003 for the current DeepSeek effort mapping.

## Dependencies

- Parent plan EP-20260829-001 is active after user approval on 2026-08-29.
- Network access to official documentation is needed for source revalidation; API keys are not needed.
- MS002, MS003, and MS004 depend on this milestone's contract confirmation.

## Risks & Mitigations

- Risk: Upstream catalogs change between planning and implementation.
  Mitigation: Reopen official pages, date the result, and amend the plan before code changes.

- Risk: An official page lists a model but not the adapter-specific request contract.
  Mitigation: Treat the capability as unestablished and defer that model instead of inferring support.

- Risk: A direct API release is mistaken for a local runtime capability.
  Mitigation: Require Codex `model/list` or an exact Claude Code version gate for local runtime choices.

- Risk: Baseline failures obscure regressions.
  Mitigation: Capture the exact clean baseline and stop before implementation if it is not reproducible.

## Validation / QA Plan

Run from the repository root:

    git status --short --branch
    uv run python -c "import agentrules"
    uv run pytest -q tests/unit/test_provider_model_compatibility_matrix.py tests/unit/agents/test_anthropic_capabilities.py tests/unit/agents/test_gemini_capabilities.py tests/unit/agents/test_xai_helpers.py tests/unit/agents/test_deepseek_helpers.py tests/unit/test_model_overrides.py
    git diff --check

Expected outcomes:

- Branch is `codex/provider-model-refresh-2026-08`.
- Import exits successfully.
- The targeted suite passes without network access.
- Only ExecPlan, milestone, and registry planning artifacts differ from `main`.
- No whitespace errors are reported.

## Deferred Work

- Provider source-code implementation begins in MS002 only after this milestone is complete.
- Paid live-smoke verification remains optional in MS005.
- Any model whose transport or modality cannot be established becomes a separately planned follow-up.

## Rollout / Recovery

There is no runtime rollout. If source facts changed, update the plan and keep affected code untouched. If the plan cannot establish a safe contract for one provider, the remaining independent provider slices may proceed only after the parent scope and acceptance criteria are explicitly amended and re-approved.

## Changelog

- 2026-08-29: Milestone created.
- 2026-08-29: Added implementation-day source gates, baseline evidence requirements, ownership boundaries, and drift recovery rules.
- 2026-08-29: Revalidated all official sources. DeepSeek medium/xhigh compatibility mapping amended in the parent plan and MS003. Validation: import smoke passed; targeted suite passed with 166 tests and 8 subtests in 3.11 seconds; no paid API calls were made.
