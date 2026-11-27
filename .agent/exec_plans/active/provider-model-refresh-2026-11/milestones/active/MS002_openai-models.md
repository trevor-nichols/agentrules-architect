---
id: EP-20261127-001/MS002
execplan_id: EP-20261127-001
ms: 2
title: "Add OpenAI text models and December retirement routes"
status: planned
domain: cross-cutting
owner: "@codex"
created: 2026-11-27
updated: 2026-11-27
tags: []
risk: med
links:
  issue: ""
  docs: ""
  pr: ""
---

# Add OpenAI text models and December retirement routes

This milestone is a living document. Keep the YAML front matter accurate and log material changes in Changelog.

## Objective

Add GPT-6.2 Astra, GPT-6.2 Sol, and GPT-6.1 Terra to direct OpenAI analysis and researcher selection. Users with older GPT-5 and o3 choices should reach supported models when OpenAI retires them on December 11, 2026.

## Definition of Done

- The picker exposes the three direct models and their exact permitted efforts. Each advertises 922,000 maximum input tokens and 128,000 maximum output tokens.
- Requests use Responses with instruction text, JSON Schema, and function tools where configured. Invalid efforts fail before dispatch.
- December retirement tests cover every saved GPT-5, GPT-5 Mini, and o3 preset. Existing unrelated retirement schedules keep their behavior.

## Scope

Extend `src/agentrules/core/agents/openai/capabilities.py`, `src/agentrules/core/types/models.py`, `src/agentrules/config/agents.py`, the centralized lifecycle map, and `docs/provider-model-lifecycle.md`. Keep `openai==2.45.0` and leave Codex discovery to MS006.

## Current Health Snapshot

The October branch already uses the Responses endpoint for GPT-6. OpenAI 2.45.0 forwarded all three new IDs, `max`, a function tool, and JSON Schema in a no-network serialization probe. Unknown IDs currently fall through to older heuristics, which can downgrade effort or miscalculate input budgets.

## Architecture / Design Snapshot

Register each model explicitly using the existing GPT-6 helper and immutable capability records. All three have 1,050,000 shared context tokens. The input ceiling is 922,000 after allowing for up to 128,000 generated tokens, before AgentRules' safety margin.

## Workstreams & Tasks

1. Register `gpt-6.2-astra` and `gpt-6.2-sol` with low, medium, high, xhigh, and max. Register `gpt-6.1-terra` with those values plus none. Use their provider defaults when no effort is set. Keep `max` and `xhigh` exact and test no reasoning for Terra only. Confirm published tool and structured-output combinations.
2. Retain request-scoped `instructions` with the existing Responses request builder. Make standard reasoning the initial preset contract. Separately evaluate optional provider features such as pro mode or prompt caching if they become required.
3. On December 11, route `o3-{low,medium,high}` to `gpt61-sol-{low,default,high}` and `gpt5-{default,minimal,high}` to `gpt61-sol-{default,low,high}`. The October branch schedules the old minimal key to switch to GPT-5.6 Sol with reasoning disabled. GPT-6.1 Sol requires reasoning, so disclose the low replacement. Route `gpt5-mini-low`, `gpt5-mini-medium`, and `gpt5-mini` to Terra low, medium, and high respectively. Keep the existing January and April dates unless a recheck finds revised upstream guidance.
4. Update model and lifecycle docs and record the actual token-packing input budget and wire values from tests. Keep the phase default on GPT-5.6 Sol throughout this milestone.

## Dependencies

MS001 and the October OpenAI capabilities. Recheck the OpenAI model card and retirement list before implementation.

## Risks & Mitigations

Adding IDs without capabilities uses generic fallback behavior. Assert exact serialized values and budget boundaries through the existing adapter and packer. Keep date-based mapping separate from direct model registration so the preset can remain callable before retirement. The shared OpenAI SDK is also used by xAI and DeepSeek, so major-version or HTTP-client changes belong in a separate cross-provider review.

## Validation / QA Plan

    uv run --python 3.11 --no-sync pytest -q tests/unit/agents/test_openai_gpt6_contract.py tests/unit/agents/test_openai_helpers.py tests/unit/test_openai_lifecycle.py tests/unit/test_provider_model_compatibility_matrix.py tests/unit/utils/test_token_packer.py

Add an SDK-backed HTTP mock for the new IDs and exact efforts if the existing fake only intercepts Python payloads. Capture the request sent to `/v1/responses`. A rejected combination must produce no transport call. Check the day before December 11 and the cutover day for each saved key.

## Rollout / Ops Notes

Ship the dated mappings with the new direct profiles they reference. After the cutoff, retain compatible redirects even if newer GPT-6.2 picker choices need to be disabled. Keep the locked SDK and new-model default evaluation independent.

## Changelog

- 2026-11-27 — Captured new models, compatibility routes, and existing SDK evidence.

[OpenAI models](https://developers.openai.com/api/docs/models) · [GPT-6.2 migration guide](https://developers.openai.com/api/docs/guides/latest-model) · [OpenAI deprecations](https://developers.openai.com/api/docs/deprecations)
