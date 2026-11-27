---
id: EP-20261127-001/MS004
execplan_id: EP-20261127-001
ms: 4
title: "Add Fable 5.2 across Anthropic and Claude Code"
status: planned
domain: cross-cutting
owner: "@codex"
created: 2026-11-27
updated: 2026-11-27
tags: []
risk: high
links:
  issue: ""
  docs: ""
  pr: ""
---

# Add Fable 5.2 across Anthropic and Claude Code

This milestone is a living document. Keep the YAML front matter accurate and log material changes in Changelog.

## Objective

Expose Fable 5.2 for both the direct Anthropic API and the local Claude Code runtime. Direct users see the retention condition and proper refusal handling. Runtime users get an actionable version message when the exact executable cannot run the pinned model.

## Definition of Done

- Direct Fable 5.2 sends `claude-fable-5-2` with model-specific thinking, tools, output limits, and retention disclosure. A terminal model refusal never becomes successful or partially emitted output.
- The pinned Claude Code model uses the same resolved executable for the version check and SDK launch, with a minimum version of 2.1.321. Older, missing, or unversionable executables fail before dispatch.
- A clean install using the new Claude Agent SDK lock supports the pin. Existing aliases, pins, and saved unavailable selections retain expected picker and launch behavior.

## Scope

Update shared Anthropic capabilities, requests and tests, model definitions and picker, `src/agentrules/core/configuration/services/claude_code.py` and `src/agentrules/core/agents/claude_code/request_builder.py`, the Claude Agent SDK constraint and lock, and both runtime and lifecycle docs. Keep the existing Anthropic Messages SDK major version, Fable 5.1 choices, and restricted Mythos policy.

## Current Health Snapshot

The October direct adapter already supports adaptive-only Fable 5.1, the covered-model retention label, and terminal refusal buffering. Direct Fable 5.2 can reuse that shape. The locked Claude Agent SDK 0.2.173 bundles 2.1.309. Claude Code request preparation currently resolves the executable path for launch and again through the version service.

## Architecture / Design Snapshot

Use the shared capability profile for a model's request and refusal behavior. For a runtime pin, resolve a path once, probe that exact path and pass it to the SDK. The picker can resolve independently when showing availability. Runtime aliases such as `fable` and `best` remain owned by Claude Code.

## Workstreams & Tasks

1. Add the Fable 5.2 capability ahead of the broader Fable 5 prefixes in `src/agentrules/core/agents/anthropic/capabilities.py`. Apply its 1,000,000 shared context and 128,000 output cap, reserving 128,000 for generation under the existing packing policy. Support adaptive thinking only with low, medium, high, xhigh, and max, defaulting direct API effort to high. Disclose 30-day retention. Expose structured outputs under supported account policy, including the documented customer-managed encryption restriction. Keep forced tool choice out of requests.
2. Cover both direct non-streaming and streaming refusals, including a stream that produces text before its terminal stop. Apply the existing safety boundary for what is surfaced in the error summary. Current requests have one user turn. Any future history support must preserve the provider's thinking blocks as documented.
3. Add a separately typed Claude Code Fable 5.2 pin with medium as its runtime default. Put the explicit `claude-fable-5-2` minimum of 2.1.321 ahead of the generic Fable 5 family gate. Keep existing alias floors, including `fable`. Document that the runtime moves `fable` to 5.2 according to its provider policy and that `best` follows `opus` on newer versions.
4. Change the dispatch gate to probe the already-resolved executable without a second path lookup. Verify configured or bundled precedence and actionable failure for an unversionable path with a newer global binary present. Validate that an unavailable saved pin remains visible with its version note.
5. Raise the SDK floor to `claude-agent-sdk>=0.2.180`. Use `uv lock --upgrade-package claude-agent-sdk` to resolve the update, starting with 0.2.189 as the planning candidate. Verify the exact bundled CLI version in the installed distribution and rerun parsing, structured-output, and refusal checks. Document that Fable alias availability can differ when using the Claude apps gateway.

## Dependencies

October Anthropic capability and Claude Code version helpers. The first SDK bundling CLI 2.1.321 is 0.2.180. The 0.2.189 planning candidate bundles 2.1.332.

## Risks & Mitigations

A prefix collision can accidentally match the older Fable minimum or profile. Probe at 2.1.320 and 2.1.321 and exercise both older and newer Fable pins. Two executable lookups can check and launch different binaries. Use an injected two-path scenario to prove dispatch uses the same path. Buffered output must stay private through terminal refusal.

## Validation / QA Plan

    uv lock --check --python 3.11
    uv run --python 3.11 --no-sync pytest -q tests/unit/agents/test_anthropic_latest_contract.py tests/unit/agents/test_anthropic_request_builder.py
    uv run --python 3.11 --no-sync pytest -q tests/unit/agents/test_claude_code_request_builder.py tests/unit/agents/test_claude_code_client.py tests/unit/agents/test_claude_code_architect.py tests/unit/agents/test_claude_code_response_parser.py
    uv run --python 3.11 --no-sync pytest -q tests/unit/test_config_service.py tests/unit/test_cli_model_picker_ui.py tests/unit/test_provider_model_compatibility_matrix.py

When separately enabled, validate the pinned runtime with `AGENTRULES_RUN_CLAUDE_CODE_LIVE=1 AGENTRULES_CLAUDE_CODE_MODEL=claude-fable-5-2` and `pytest --run-live tests/live/test_claude_code_live_smoke.py`. Direct Anthropic live access is also opt-in and depends on the account's retention settings.

## Rollout / Ops Notes

Keep direct Fable 5.2 and the runtime SDK upgrade in individually reviewable changes. A runtime rollback can remove the new pin and its SDK requirement together while retaining direct Fable 5.2. Return a clear version or provider refusal error, preserving the user's configured selection.

## Changelog

- 2026-11-27 — Recorded direct and runtime contracts, minimum version, and path-probe check.

[Fable migration guide](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide) · [Claude Code model configuration](https://code.claude.com/docs/en/model-config) · [Claude Agent SDK 0.2.180 bundled version](https://github.com/anthropics/claude-agent-sdk-python/blob/v0.2.180/src/claude_agent_sdk/_cli_version.py)
