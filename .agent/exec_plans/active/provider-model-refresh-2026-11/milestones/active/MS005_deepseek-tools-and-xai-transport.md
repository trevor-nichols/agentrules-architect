---
id: EP-20261127-001/MS005
execplan_id: EP-20261127-001
ms: 5
title: "Preserve DeepSeek tool turns and assess xAI transport"
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

# Preserve DeepSeek tool turns and assess xAI transport

This milestone is a living document. Keep the YAML front matter accurate and log material changes in Changelog.

## Objective

A DeepSeek-powered researcher can finish a native tool conversation in thinking mode, including when one tool call fails. Record what an xAI Responses migration would require so the team can decide on it separately from this release.

## Definition of Done

- A fake DeepSeek transport observes the original assistant content, original `reasoning_content` and call IDs, and one matching tool response for each call in their original order. Multiple turns preserve the entire relevant history.
- Tool exceptions return a result linked to the original call and let sibling calls complete. AgentRules retains its existing research safeguards and publishes no private transcript fields in phase artifacts.
- The lifecycle guide distinguishes current xAI Chat Completions support from the separately scoped Responses decision. Its notes cover encrypted reasoning, retention, structured output, and the impact on the shared SDK.

## Scope

Update the DeepSeek request builder, response handling, and Phase 1 researcher orchestration as needed. DeepSeek-V4.1-Flash-1017 and V4 Pro already run under `deepseek-flash` and `deepseek-v4-pro`. Grok 4.7 already has a tested Chat Completions adapter. Keep both existing endpoints and the shared OpenAI SDK in this milestone.

## Current Health Snapshot

Phase 1 sends tool results as text in a new request for most providers. Gemini has a native turn path already. DeepSeek's parser extracts reasoning and IDs, while its request builder emits only system and user messages. DeepSeek requires original reasoning in all continued thinking requests with tools. xAI marks Chat Completions deprecated and still serves Grok 4.7 on it.

## Architecture / Design Snapshot

Keep a request-scoped DeepSeek message history in canonical plain dictionaries. Use the native assistant and named tool-call records from the original response and leave generic tool feedback in place for other providers. Route provider-specific logic through the established capability or adapter boundary and reuse the current tool executor.

## Workstreams & Tasks

1. In `src/agentrules/core/agents/deepseek/response_parser.py` and `request_builder.py`, preserve and replay the native assistant message, including `reasoning_content`, `content`, and exact `tool_calls`. Keep IDs and argument strings intact. Send the original system/user messages once and append a tool message for each call with `role=tool` and the matching `tool_call_id`. Preserve provider-required reasoning on subsequent tool-enabled turns. Never invent missing reasoning.
2. In `src/agentrules/core/analysis/phase_1.py`, continue DeepSeek's transcript only when the provider returns the relevant native state. Reuse execution and error reporting while capturing a separate outcome for every ID. Test two calls to the same named tool and a failure in one call. Preserve iteration limits and result summaries. Strip transient private history fields from returned findings and logs. Keep analysis dispatch off the asyncio event loop when adjusting the DeepSeek request path.
3. Extend `docs/provider-model-lifecycle.md` with a scoped xAI Responses proposal. Cover request mapping, function call and structured schema translation, final streaming events, continued encrypted reasoning, and compatibility with xAI base URL overrides. Use `store=false` as the baseline for a stateless migration and verify its behavior if that follow-up is approved. Document the provider's default 30-day response storage and require explicit review for any retention change. State that the current release preserves Chat Completions and the shared SDK.

## Dependencies

MS001 has repaired the retired xAI aliases. DeepSeek supports the intended tool flow on its current Chat Completions endpoint. The Phase 1 Gemini test provides an existing fake transport pattern.

## Risks & Mitigations

A name-only lookup can misattribute multiple calls and an aborted batch can leave IDs without results. Use original call IDs and test exact replay. A full transcript can leak reasoning if attached to final pipeline output. Assert that only existing public result fields survive. Keep the xAI change to documentation and avoid changing retention behavior in this rollout.

## Validation / QA Plan

    uv run --python 3.11 --no-sync pytest -q tests/unit/agents/test_deepseek_helpers.py tests/unit/agents/test_deepseek_agent_parsing.py tests/unit/test_agents_deepseek.py tests/unit/agents/test_xai_helpers.py
    uv run --python 3.11 --no-sync pytest -q tests/phase_1_test

Add a Phase 1 DeepSeek regression modeled on `tests/phase_1_test/test_phase1_gemini_tool_turn.py`. The fake model must require verbatim reasoning and matching tool messages before returning its final findings. Include same-name calls with distinct IDs, one tool error, and multi-turn history. Keep a zero-tool path and Gemini behavior covered.

## Rollout / Ops Notes

Treat xAI Responses as a separately approved change. The current Grok 4.7 model and compatibility routes remain deployable. If DeepSeek native replay needs correction, keep the model presets and disable the affected research capability or direct researchers to a known working choice until repaired. Preserve existing user profile settings.

## Changelog

- 2026-11-27 — Documented native DeepSeek replay and the xAI migration decision boundary.

[DeepSeek thinking-mode tool contract](https://api-docs.deepseek.com/guides/thinking_mode/) · [xAI Responses migration](https://docs.x.ai/developers/model-capabilities/text/comparison)
