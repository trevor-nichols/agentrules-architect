---
id: EP-20260308-001/MS002
execplan_id: EP-20260308-001
ms: 2
title: "Add app-server process, auth, and model catalog services"
status: planned
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

- [ ] Transport: create process and protocol helpers under `src/agentrules/core/agents/codex/`.
- [ ] Services: implement account and model catalog methods on top of the transport.
- [ ] Settings UX: surface install/account/model status in the CLI.
- [ ] Tests: build a fake app-server script/fixture that can emit responses and notifications deterministically.

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
