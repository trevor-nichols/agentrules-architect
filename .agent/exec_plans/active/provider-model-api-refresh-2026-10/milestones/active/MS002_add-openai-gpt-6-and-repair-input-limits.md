---
id: EP-20261023-001/MS002
execplan_id: EP-20261023-001
ms: 2
title: "Add OpenAI GPT-6 and repair input limits"
status: planned
domain: cross-cutting
owner: "@codex"
created: 2026-10-23
updated: 2026-10-23
tags: [openai, capabilities, packing, lifecycle]
risk: high
links:
  issue: ""
  docs: "docs/provider-model-audit-2026-10.md"
  pr: "https://github.com/trevor-nichols/agentrules-architect/pull/42"
---

# Add OpenAI GPT-6 and repair input limits

This milestone is a living document under `.agent/PLANS.md`. Start after plan approval and MS001's source revalidation; keep parent Progress current.

## Objective

OpenAI GPT-6 choices produce valid Responses requests, and input packing never exceeds each model's documented maximum input or total context. Existing live presets retain their chosen endpoint.

## Definition of Done

- Revalidate official OpenAI model cards and deprecation dates/targets before edits.
- Four GPT-6 wire IDs have exact immutable capability metadata and picker presets; unsupported reasoning (including none for Astra/6.1 Sol) fails before SDK dispatch.
- Effective input limit respects maximum input, total context minus output reservation, and packer margin; GPT-5.4 Mini/Nano and GPT-5.3-Codex use 272K maximum input.
- Deprecated-but-live keys preserve wire IDs, dated notices and future one-hop retired mappings are tested; direct architect default no longer uses `o3`.
- Direct synchronous SDK call no longer blocks the event loop; request/failure tests, ruff, pyright, import smoke, and docs pass.

## Scope

### In Scope
- `src/agentrules/config/agents.py`, `src/agentrules/core/configuration/model_presets.py`, `src/agentrules/core/agents/openai/{config,request_builder,architect,compat,client}.py`, and the existing token packer/estimator integration.
- GPT-6 Astra/6.1 Sol/6 Sol/Luna on Responses; GPT-5/o3 (2026-12-11), GPT-4.1 (2027-01-14), and GPT-5.1/5.3-Codex/5.4 Nano (2027-04-01) lifecycle metadata, subject to revalidation.

### Out of Scope
- A default phase-model switch, a Codex runtime preset, and a new endpoint. Keep GPT-5.6 explicit rollback choices.

## Workstreams & Tasks

- Replace name-substring model limit selection with authoritative per-model total/input/output values; maintain one effective-budget calculation.
- Validate reasoning and structured-output/tool compatibility before building Responses payloads; add four GPT-6 families.
- Mark live deprecations without redirect and prepare exact retirement mappings; change direct `o3` constructor/compat default to a reviewed active profile.
- Use async SDK or a thread boundary for the blocking direct call, preserving timeout/error propagation.
- Add tests for wire effort, packed limits at boundaries, old keys, and concurrent loop responsiveness.

## Risks & Mitigations

- Risk: A 1.05M total window is mistaken for usable input. Mitigation: assert 922K maximum input and output reservation independently, including the existing margin.
- Risk: Deprecation changes a paid live workload. Mitigation: test old saved key → same wire model until retirement.
- Risk: Threading a synchronous SDK call changes cancellation or error handling. Mitigation: test failure propagation and avoid introducing a second client path.

## Dependencies

MS001's dated source matrix and capability conventions. No dependency on Gemini or other model slices.

## Validation / QA Plan

- From repository root run `.venv/bin/pytest -q tests/unit/agents/test_openai_helpers.py tests/unit/test_agents_openai_params.py tests/test_openai_responses.py` plus existing packing/model-preset suites found with `rg --files tests | rg 'token_packer|model_preset|agents_openai'`.
- Run `.venv/bin/ruff check .`, `.venv/bin/pyright`, import smoke, and `git diff --check`. Expect unsupported `none` for Astra to raise before a fake SDK client is called.
- Before/after check: a GPT-5.4 Mini prompt that exceeds 272K input is split/reduced by the packer; an old live GPT-4.1 key still dispatches GPT-4.1 and displays its deprecation notice.

## Rollout / Ops Notes

Keep phase defaults unchanged pending MS008 evaluation. Revert only new GPT-6 exposure if account entitlement fails; leave corrected packing and lifecycle behavior. Do not redirect a live preset early.

## Changelog

- 2026-10-23: Defined GPT-6 request, packing, lifecycle, and async-call acceptance.
