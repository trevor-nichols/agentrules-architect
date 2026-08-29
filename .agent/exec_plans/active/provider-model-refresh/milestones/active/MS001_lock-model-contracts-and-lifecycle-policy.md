---
id: EP-20260829-001/MS001
execplan_id: EP-20260829-001
ms: 1
title: "Lock Model Contracts and Lifecycle Policy"
status: planned
domain: cross-cutting
owner: "@codex"
created: 2026-08-29
updated: 2026-08-29
tags: [providers, research, contracts, lifecycle]
risk: med
links:
  issue: ""
  docs: ""
  pr: ""
---

# Lock Model Contracts and Lifecycle Policy

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Freeze an implementation-day, source-backed contract for every model and migration in EP-20260829-001 before runtime behavior changes. This milestone protects the implementation from catalog drift and ensures the existing provider baseline is green. Its output is an approved contract update in the parent ExecPlan and recorded validation evidence; it does not expose a new picker entry.

## Definition of Done

- [ ] Every upstream source in the parent plan has been reopened and checked on the implementation date.
- [ ] Model IDs, context limits, supported efforts, thinking-disable behavior, transport, tool/structured-output compatibility, and lifecycle state match the parent contract table or the table has been amended with a dated decision.
- [ ] Each compatibility migration has one existing legacy key and one registered canonical target planned; no legacy key is scheduled for deletion.
- [ ] The targeted offline baseline passes and its exact result is recorded below.
- [ ] No provider runtime behavior, dependency version, phase default, or paid external API state changes in this milestone.
- [ ] Parent `Progress`, `Surprises & Discoveries`, and `Decision Log` reflect any implementation-day drift.

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

- [ ] Open Anthropic's current model overview, adaptive-thinking, and effort pages. Confirm Opus 5 wire ID, context/output ceilings, adaptive default, disabled-thinking support, and low-through-max effort set.
- [ ] Open Gemini's current model catalog and thinking pages. Confirm 3.7 Flash, 3.6 Flash, and 3.5 Flash-Lite IDs, default and allowed thinking levels, context/output ceilings, structured output, and tools.
- [ ] Open xAI's Grok 4.6 and reasoning pages. Confirm the 500K context, low/medium/high/xhigh set, inability to disable reasoning, and the ordinary adapter transport features.
- [ ] Open DeepSeek's update/model pages. Confirm V4 Flash/Pro IDs, low/high/max effort, thinking toggle, and current published output ceiling.
- [ ] Open official OpenAI model pages. Confirm GPT-5.6 is already current, o4-mini is deprecated and succeeded by GPT-5 Mini, and GPT-5.1/5.2 Codex are deprecated relative to the active 5.3 Codex compatibility target.

### Workstream B - Lock compatibility and exclusion decisions

- [ ] Verify that `o4-mini-low`, `o4-mini-medium`, and `o4-mini-high` exist and that planned GPT-5 Mini targets preserve the same generic effort role.
- [ ] Verify that direct and static-derived `gpt-5.1-codex`/`gpt-5.2-codex` keys exist before planning their redirects.
- [ ] Verify that `claude-opus`, `claude-opus-reasoning`, pinned Opus 4.8 keys, DeepSeek legacy keys, and Codex runtime default keys remain registered.
- [ ] Reconfirm exclusions: no static GPT-5.6 Codex, no pinned Claude Code Opus 5 without an exact runtime gate, no GPT-5.5 Pro or GPT-5.6 Pro mode, no Grok Multi-Agent, and no DeepSeek Vision Experimental.

### Workstream C - Establish a clean baseline

- [ ] Run the import smoke and targeted tests from the parent plan.
- [ ] Record exact pass/fail counts and elapsed time in this milestone's changelog.
- [ ] If a baseline fails, determine whether it predates this branch. Fixing unrelated baseline failures is not authorized by this milestone; record and escalate them before provider implementation.
- [ ] Update the parent ExecPlan's dated snapshot and decisions when source facts changed.

## Dependencies

- Parent plan EP-20260829-001 must remain in `planned` status until user approval.
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
