---
id: EP-20261127-001/MS003
execplan_id: EP-20261127-001
ms: 3
title: "Add Gemini 4 models and validate the GenAI SDK upgrade"
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

# Add Gemini 4 models and validate the GenAI SDK upgrade

This milestone is a living document. Keep the YAML front matter accurate and log material changes in Changelog.

## Objective

Make Gemini 4 Carbon, Hydrogen, and Neon selectable on the existing GenerateContent adapter. Users should get the advertised effort, input budget, tool behavior, and preview access from a clean locked install.

## Definition of Done

- Carbon, Hydrogen, and Neon dispatch their exact IDs and supported efforts, and reject unsupported values before transport. Hydrogen and Neon expose native `xhigh`.
- The three new models use the shared context window and signed Gemini tool turns. Existing Gemini presets still use valid URLs and payloads after the SDK upgrade.
- `pyproject.toml`, `uv.lock`, and the Google SDK stubs reflect tested requirements. The locked Python 3.11 suite passes.

## Scope

Update `src/agentrules/core/agents/gemini/capabilities.py`, `client.py` and request construction as needed, `src/agentrules/config/agents.py`, `src/agentrules/core/types/models.py`, `typings/google/genai/__init__.pyi` and `types.pyi`, and lifecycle docs. Existing GenerateContent work covers this rollout. The Gemini Interactions API is separate.

## Current Health Snapshot

The October branch locks `google-genai==2.33.0` and uses the default API version when constructing the client. Gemini 4 Argon already has signed tool replay, a shared context calculation, and request continuation. SDK 3 changes the default Gemini Developer API version to `v1` and switches to HTTPX2.

## Architecture / Design Snapshot

Define a separate immutable profile for each Gemini 4 family using the existing capability resolver. All share 1,048,576 tokens across input, thinking, and output. With the existing 65,536 generation reservation, maximum packed input is 983,040 before the safety margin. The SDK already supports continuation on GenerateContent from 2.30.1 onward.

## Workstreams & Tasks

1. Add `gemini-4-carbon` (default medium, low/medium/high, paid), `gemini-4-hydrogen` (default high, low/medium/high/xhigh, free and paid), and `gemini-4-neon` (default high, low/medium/high/xhigh, paid). Carbon and Argon allow 32,768 tokens per direct non-streaming REST call, with SDK continuation for 65,536. Hydrogen and Neon allow up to 65,536 in one call. Keep the existing generation target and timeout strategy where needed. Use the provider's compatible structured output and signed function call behavior.
2. Add `XHIGH` in exact thinking-level mapping and stub. Reject the value for all other families unless their own contract allows it. For an exact profile, fail with an SDK capability error if the relevant enum or enum member is missing. Keep the existing compatibility behavior for legacy budget-mode models.
3. Raise the package floor to `google-genai>=3.3.0`. Start review with 3.6.1, the current candidate at planning time. Regenerate the lock using `uv lock --upgrade-package google-genai` and review the resolved HTTP client and related changes. If resolution or a regression makes the candidate unsuitable, use the nearest supported 3.x release verified through the same checks.
4. Preserve current Gemini Developer API preview compatibility explicitly if SDK 3's default would remove access. Respect an explicit API version override and the SDK's Vertex or Enterprise selection. Extend the client constructor and `HttpOptions` stubs if exposing `http_options.api_version`. Test the actual URL using the installed SDK, including configured-key and SDK-key loading and the interaction between client version and per-request timeout.
5. Reuse the signed native tool history path with matching call IDs, including error responses. Check a combined schema-and-tool request where supported. Omit unsupported sampling parameters for the Gemini 4 calls. Update lifecycle docs with paid availability, token limits, and precise effort levels.

## Dependencies

MS001's Gemini constructor and saved-key fixes. SDK 3.3.0 introduced `ThinkingLevel.XHIGH`. Model availability and payment tier are account-dependent.

## Risks & Mitigations

SDK 3 can break preview IDs or alter HTTP behavior even where stable models still work. Check outbound URLs through the real SDK with an offline transport, exercise the existing preview choices, and rerun all provider tests against the resolved lock. If long output exceeds the shared input reservation, exact packing tests should show the input bound. Test error branches for missing SDK enum members and unsupported reasoning.

## Validation / QA Plan

    uv lock --check --python 3.11
    uv sync --locked --extra dev --python 3.11
    uv run --python 3.11 --no-sync pytest -q tests/unit/agents/test_gemini_capabilities.py tests/unit/agents/test_gemini_agent_parsing.py tests/unit/test_gemini_current_presets.py tests/phase_1_test/test_phase1_gemini_tool_turn.py tests/unit/test_provider_model_compatibility_matrix.py tests/unit/utils/test_token_packer.py
    uv run --python 3.11 --no-sync pyright

The mocked request should demonstrate exact `XHIGH` for Hydrogen and Neon, rejection for Carbon, a valid preview URL, preserved timeout on a continuation-capable model, and matching signed tool-call identity across turns.

## Rollout / Ops Notes

Ship the SDK floor, lockfile, stubs, and new picker capabilities together after validation. If the SDK or model slice must roll back, preserve the December 1 routes and the existing signed-turn adapter. Record the version pinned and preview-mode choice in the plan.

## Changelog

- 2026-11-27 — Documented model profiles, SDK migration, and preview regression checks.

[Gemini catalog](https://aistudio.google.com/docs/models#gemini-4) · [GenerateContent continuation](https://aistudio.google.com/docs/long-decode?generate-content=true) · [SDK 3.3](https://github.com/googleapis/python-genai/releases/tag/v3.3.0) · [SDK 3.0](https://github.com/googleapis/python-genai/releases/tag/v3.0.0)
