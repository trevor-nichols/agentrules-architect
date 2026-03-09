---
id: EP-20260308-001/MS002
execplan_id: EP-20260308-001
ms: 2
title: "Add app-server process, auth, and model catalog services"
status: done
domain: cross-cutting
owner: "@codex"
created: 2026-03-08
updated: 2026-03-08
tags: [codex, app-server, auth]
risk: med
links:
  issue: ""
  docs: "internal-docs/integrations/codex/app-server"
  pr: ""
---

# Add app-server process, auth, and model catalog services

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Build the reusable JSON-RPC transport and service layer for Codex app-server so AgentRules can initialize a session, inspect account state, drive ChatGPT login/logout, and fetch the model catalog. When this milestone is complete, AgentRules can verify that a Codex runtime is usable before any phase provider code starts sending analysis prompts.

## Definition of Done

- A Codex process wrapper can launch `codex app-server`, send `initialize`, and shut down cleanly.
- Request/response correlation works for normal JSON-RPC messages and does not lose streamed notifications.
- Service methods exist for `account/read`, `account/login/start`, `account/logout`, and `model/list`.
- CLI settings can show Codex account state and available models from the configured runtime.
- A fake app-server test harness covers the transport and service methods without a live Codex login.

## Scope

### In Scope
- Process spawning, JSONL transport, request IDs, and lifecycle management.
- Auth/account service methods and ChatGPT login URL handling.
- Model catalog retrieval and normalization for settings/preset UI.
- Fake transport or subprocess fixture for unit tests.

### Out of Scope
- The `BaseArchitect` implementation.
- Phase execution.
- Phase-specific prompt exceptions.

## Workstreams & Tasks

- [x] Transport: created process/protocol/client helpers under `src/agentrules/core/agents/codex/` with initialize/initialized lifecycle, request correlation, notification buffering, and clean shutdown behavior.
- [x] Services: implemented account/login/logout/model-catalog helpers plus centralized launch-config construction through `ConfigManager.build_codex_launch_config()`.
- [x] Settings UX: surfaced install/account/model status in the CLI and added ChatGPT sign-in/sign-out actions via `src/agentrules/cli/ui/settings/codex.py`.
- [x] Tests: added `tests/fakes/codex_app_server.py` and Codex-focused unit coverage for transport, auth, pagination, and runtime diagnostics.

## Risks & Mitigations

- Risk: a shared client abstraction silently assumes a stateless request/response protocol.
  Mitigation: keep notification handling explicit in the client contract even before the architect adapter consumes it.
- Risk: login support mutates the wrong `CODEX_HOME`.
  Mitigation: require every client creation path to resolve and log the effective `CODEX_HOME` explicitly in debug output.

## Validation / QA Plan

- `PYTHONPATH=src pytest tests/unit -q -k codex`
- `ruff check src tests`
- Manual check: from the settings flow, confirm account status and model catalog display from the selected `CODEX_HOME`.

## Changelog

- 2026-03-08: Milestone created.
- 2026-03-08: Implemented the Codex app-server process/auth/model-catalog layer, validated it with fake-server unit tests plus the full unit/lint/type suite, and smoke-checked the installed `codex app-server`.
