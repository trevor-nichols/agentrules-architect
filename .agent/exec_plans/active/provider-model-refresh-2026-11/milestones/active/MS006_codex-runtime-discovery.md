---
id: EP-20261127-001/MS006
execplan_id: EP-20261127-001
ms: 6
title: "Verify Codex runtime discovery for GPT-6.2"
status: planned
domain: cross-cutting
owner: "@codex"
created: 2026-11-27
updated: 2026-11-27
tags: []
risk: low
links:
  issue: ""
  docs: ""
  pr: ""
---

# Verify Codex runtime discovery for GPT-6.2

This milestone is a living document. Keep the YAML front matter accurate and log material changes in Changelog.

## Objective

Verify that a configured Codex runtime can expose GPT-6.2 Astra and Sol, carry its advertised reasoning effort through the picker and saved config, and return structured phase output.

## Definition of Done

- A fake app-server advertises GPT-6.2 models and efforts. The picker shows the runtime data, a selection survives save and reload, and the selected effort reaches the provider-native request.
- An unavailable or hidden runtime model remains governed by existing runtime behavior. The default follows the runtime's own default.
- `docs/codex-runtime.md` explains the 0.166.0 minimum for GPT-6.2, the exact executable check, and account-dependent discovery and smoke instructions.

## Scope

Verify `src/agentrules/core/agents/codex/client.py`, `model_selection.py`, the CLI runtime service and picker, and the central configuration manager. Add focused fake-runtime coverage or fix a confirmed discovery incompatibility. Keep model/effort lists runtime-owned and avoid new static Codex IDs or a Python dependency.

## Current Health Snapshot

The October branch already consumes app-server `model/list` and passes `outputSchema` for structured phases. The Codex binary on this machine's `PATH` reported 0.172.0 during research. Custom executable settings and account eligibility can produce a different catalog.

## Architecture / Design Snapshot

`ConfigManager.build_codex_launch_config()` determines the executable and `CODEX_HOME` policy. The runtime catalog controls model visibility, effort, and default. Direct API model contracts do not determine local runtime availability.

## Workstreams & Tasks

1. Extend `tests/fakes/codex_app_server.py` or the existing fixture to advertise GPT-6.2 Astra and Sol with model names, supported effort entries, and a default. Verify selection and persistence via the CLI configuration path, including an orderable standard effort and an advertised effort string absent from the static display order.
2. Verify that app-server receives the selected model/effort and output schema exactly. Do not gate ordinary AgentRules Codex use on a version minimum specific to GPT-6.2. Verify graceful handling of a catalog that omits GPT-6.2 and a saved pin no longer returned by the runtime. Follow the existing request-scoped developer instructions and launch configuration.
3. Update `docs/codex-runtime.md` with the current GPT-6.2 requirement and an operator check of the executable configured in `Settings → Codex runtime` using `--version`. Explain that the next step is to refresh the model list under the same account and runtime home.

## Dependencies

The current app-server catalog schema and the repository's fake Codex app-server. The upstream GPT-6.2 minimum is Codex CLI 0.166.0. This milestone does not depend on the direct OpenAI model registry or Python SDK release.

## Risks & Mitigations

Checking only the global `PATH` binary can misdiagnose a custom executable. Use the executable and home resolved by AgentRules. A model missing from the catalog can be an entitlement or rollout issue. Validate discovery offline and record live availability separately.

## Validation / QA Plan

    uv run --python 3.11 --no-sync pytest -q tests/unit/agents/test_codex_client.py tests/unit/agents/test_codex_architect.py tests/unit/agents/test_codex_request_builder.py tests/unit/test_codex_runtime_service.py tests/unit/test_cli_model_picker_ui.py

With separate opt-in and a signed-in runtime that advertises the model, set `AGENTRULES_RUN_CODEX_LIVE=1 AGENTRULES_CODEX_MODEL=gpt-6.2-sol` and run `uv run --python 3.11 --no-sync pytest --run-live -q tests/live/test_codex_live_smoke.py`. Use `AGENTRULES_CODEX_CLI` and the existing home controls to match the intended configuration. A skipped smoke means the model's live availability remains unverified.

## Rollout / Ops Notes

Ship the operator guide with the tests. The compatibility fallback remains the runtime default or another model the account advertises.

## Changelog

- 2026-11-27 — Documented runtime discovery verification and version requirement.

[Codex runtime model discovery](https://learn.chatgpt.com/docs/app-server#list-models-modellist) · [GPT-6.2 release requirements](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex)
