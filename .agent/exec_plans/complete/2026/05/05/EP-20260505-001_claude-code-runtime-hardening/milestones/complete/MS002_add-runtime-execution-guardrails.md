---
id: EP-20260505-001/MS002
execplan_id: EP-20260505-001
ms: 2
title: Add Runtime Execution Guardrails
status: completed
domain: backend
owner: '@codex'
created: 2026-05-05
updated: '2026-05-05'
tags:
- claude-code
- guardrails
- timeouts
- cost-control
risk: med
links:
  issue: ''
  docs: internal-docs/integrations/anthropic/agents-sdk/python-sdk.md
  pr: ''
---

# Add Runtime Execution Guardrails

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Bound Claude Code runtime execution so headless AgentRules runs cannot wait indefinitely or spend unbounded model/tool turns. At the end of this milestone, each Claude Code SDK request has explicit turn limits, optional cost limits, and an outer AgentRules timeout with clear error reporting.

## Definition of Done

- [x] Claude Code runtime config has validated defaults for request timeout and maximum turns.
- [x] `prepare_request()` includes `max_turns` and optional `max_budget_usd` in SDK options.
- [x] AgentRules-only timeout data is not passed as an unsupported `ClaudeAgentOptions` field.
- [x] `src/agentrules/core/agents/claude_code/client.py` wraps SDK iterator collection with `asyncio.wait_for` or equivalent cancellation-safe timeout handling.
- [x] Timeout and SDK failures map to `ClaudeCodeExecutionError` with actionable messages.
- [x] Unit tests cover default guardrail options, custom guardrail config, and timeout error mapping.

## Scope

### In Scope
- Extend `ClaudeCodeConfig` in `src/agentrules/core/configuration/models.py` with fields such as `max_turns`, `request_timeout_seconds`, and `max_budget_usd`.
- Add constants and normalization in `src/agentrules/core/configuration/constants.py`, `src/agentrules/core/configuration/utils.py`, `src/agentrules/core/configuration/serde.py`, and `src/agentrules/core/configuration/services/claude_code.py`.
- Extend `PreparedRequest` in `src/agentrules/core/agents/claude_code/request_builder.py` with an AgentRules-only `execution_timeout_seconds` field.
- Update `ClaudeCodeArchitect._execute_request()` and the injected query executor contract in a backward-compatible way for tests.
- Update `tests/unit/agents/test_claude_code_request_builder.py`, `tests/unit/agents/test_claude_code_architect.py`, and `tests/unit/test_config_service.py`.
- Update `docs/claude-code-runtime.md` with the guardrail defaults and how operators can tune them if a CLI settings surface is added now.

### Out of Scope
- Do not implement streaming timeout semantics for `stream_query()` beyond keeping the helper safe if touched.
- Do not introduce unrestricted shell or edit permissions to reduce turn count.
- Do not add a global billing subsystem. `max_budget_usd` is only the SDK's per-request client-side stop condition.

## Workstreams & Tasks

- [x] Configuration: choose conservative defaults. Suggested initial values are `max_turns=12`, `request_timeout_seconds=300.0`, and `max_budget_usd=None`.
- [x] Serialization: persist only non-default guardrail settings, preserving existing config files without migration work.
- [x] Request builder: place `max_turns` and `max_budget_usd` into SDK options only when valid, and keep timeout on `PreparedRequest`.
- [x] Client: implement timeout wrapping around message collection and make cancellation cleanup explicit.
- [x] Tests: include an async fake query that never completes and assert that the returned error mentions timeout.

## Risks & Mitigations

- Risk: A default turn limit that is too low could truncate legitimate Phase 3 repository analysis.
  Mitigation: Start with a moderate value, make it configurable, and keep live smoke plus Phase 3 unit coverage. If live validation shows frequent truncation, adjust the default in the plan before implementation completes.
- Risk: Timeout cancellation may leave a child process running if the SDK does not respond to cancellation cleanly.
  Mitigation: Keep the timeout at the outer query collection boundary first and inspect SDK behavior during the gated live smoke. If needed, add explicit transport/process cleanup in a follow-up using the SDK's supported APIs.

## Validation / QA Plan

- Run `PYTHONPATH=src .venv/bin/pytest tests/unit/agents/test_claude_code_request_builder.py tests/unit/agents/test_claude_code_architect.py tests/unit/agents/test_claude_code_client.py tests/unit/test_config_service.py`.
- Run `PYTHONPATH=src .venv/bin/pytest --run-live tests/live/test_claude_code_live_smoke.py`; without `AGENTRULES_RUN_CLAUDE_CODE_LIVE=1`, one skipped test is acceptable.
- Run `PYTHONPATH=src .venv/bin/ruff check src/agentrules/core/agents/claude_code src/agentrules/core/configuration tests/unit/agents/test_claude_code_architect.py tests/unit/test_config_service.py`.
- Green means prepared SDK options contain the configured turn and budget limits, timeout does not appear in `ClaudeAgentOptions`, and a timed-out SDK query produces a deterministic AgentRules error.

## Changelog

- 2026-05-05: Milestone created.
- 2026-05-05: Drafted guardrail config, request, client, and validation scope from Claude Code runtime review finding 2.
- 2026-05-05: Implemented Claude Code execution guardrails with persisted config defaults, SDK `max_turns` and optional budget options, AgentRules-only timeout enforcement, timeout tests, and docs. Validation passed with focused tests, live-smoke skip check, ruff, and pyright.
