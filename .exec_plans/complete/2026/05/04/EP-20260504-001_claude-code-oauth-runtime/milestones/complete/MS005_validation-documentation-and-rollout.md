---
id: EP-20260504-001/MS005
execplan_id: EP-20260504-001
ms: 5
title: Validation Documentation and Rollout
status: completed
domain: cross-cutting
owner: '@codex'
created: 2026-05-04
updated: '2026-05-04'
tags:
- tests
- docs
- rollout
risk: med
links:
  issue: ''
  docs: docs/claude-code-runtime.md
  pr: ''
---

# Validation Documentation and Rollout

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Complete the verification, documentation, and rollout path for the Claude Code OAuth runtime provider. When this milestone is complete, maintainers have deterministic offline tests, an opt-in live smoke test for authenticated Claude Code environments, operator documentation, and release notes that explain how to use and troubleshoot the runtime.

## Definition of Done

- [x] `docs/claude-code-runtime.md` documents local setup, automated setup, settings UI, model presets, environment precedence, testing, and troubleshooting.
- [x] `tests/live/test_claude_code_live_smoke.py` exists and is gated by both `pytest --run-live` and `AGENTRULES_RUN_CLAUDE_CODE_LIVE=1`.
- [x] Live smoke skips cleanly when the Claude Code executable, opt-in env, or OAuth auth state is unavailable.
- [x] Unit, offline, import-smoke, ruff, and pyright commands are documented with expected outcomes.
- [x] `SNAPSHOT.md` is synced if the repository snapshot policy includes the new files.
- [x] The ExecPlan and milestones are updated with outcomes, discoveries, and any deviations from the approved plan.

## Scope

### In Scope
- Add `docs/claude-code-runtime.md`.
- Add a live smoke test that sends a minimal prompt through `ClaudeCodeArchitect` or the adapter client and validates a small structured output.
- Add or update test markers in `conftest.py` only if needed for live-test gating.
- Run focused and broad validation commands.
- Update `SNAPSHOT.md` with `agentrules snapshot sync` if applicable.
- Update this ExecPlan and milestone files with final status notes before completion.

### Out of Scope
- Do not make live Claude Code tests part of default CI.
- Do not document API-key fallback for the Claude Code runtime provider.
- Do not change default provider presets or enable Claude Code by default without separate approval.
- Do not commit or push changes unless explicitly requested.

## Workstreams & Tasks

### Workstream A - Documentation

| ID | Area | Description | Status |
|----|------|-------------|--------|
| A1 | Setup | Document `claude auth login` for local use and `claude setup-token` plus `CLAUDE_CODE_OAUTH_TOKEN` for automation. | completed |
| A2 | Settings | Document the new AgentRules settings screen and what each diagnostic means. | completed |
| A3 | Precedence | Document why AgentRules sanitizes `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` for this runtime. | completed |
| A4 | Troubleshooting | Include missing CLI, missing SDK package, auth failure, permission denial, and structured output failure cases. | completed |

### Workstream B - Live Smoke and Test Gates

| ID | Area | Description | Status |
|----|------|-------------|--------|
| B1 | Live Test | Add a minimal live test with explicit opt-in env gating. | completed |
| B2 | Skip Reasons | Ensure skip messages explain exactly what is missing. | completed |
| B3 | Structured | Validate a tiny structured output payload through the runtime. | completed |
| B4 | Offline | Confirm unit and offline tests do not require the live SDK runtime. | completed |

### Workstream C - Final Validation and Plan Closure

| ID | Area | Description | Status |
|----|------|-------------|--------|
| C1 | Focused | Run all new focused test modules. | completed |
| C2 | Broad | Run `pytest tests/unit tests/offline`, ruff, pyright, and import smoke if feasible. | completed |
| C3 | Snapshot | Run `agentrules snapshot sync` if new source/docs files are represented in `SNAPSHOT.md`. | completed |
| C4 | Plan | Update Progress, Surprises & Discoveries, Decision Log, and Outcomes & Retrospective. | completed |

## Risks & Mitigations

- Risk: Live smoke tests could be flaky due to user rate limits or local auth state.
  Mitigation: Keep live tests opt-in, tiny, and skip-friendly. Default CI remains offline and deterministic.
- Risk: Documentation could accidentally imply API-key support for this runtime.
  Mitigation: Use precise wording: direct Anthropic API-key auth remains in the existing Anthropic provider, while Claude Code runtime uses Claude.ai OAuth subscription auth.
- Risk: Broad validation may reveal unrelated pre-existing failures.
  Mitigation: Record unrelated failures in the final notes without expanding scope, and keep focused tests green for changed areas.

## Validation / QA Plan

- Ran `PYTHONPATH=src .venv/bin/python -c "import agentrules"` and observed exit code 0 with no output.
- Ran focused Claude Code validation:

    `PYTHONPATH=src .venv/bin/pytest tests/unit/test_config_service.py tests/unit/agents/test_claude_code_request_builder.py tests/unit/agents/test_claude_code_response_parser.py tests/unit/agents/test_claude_code_architect.py tests/unit/test_cli_claude_code_settings.py tests/unit/test_cli_model_picker_ui.py tests/unit/utils/test_provider_capabilities.py tests/unit/utils/test_structured_outputs.py tests/unit/analysis/test_phase3_packing.py`

  Observed 85 passed.
- Ran live smoke skip validation:

    `PYTHONPATH=src .venv/bin/pytest --run-live tests/live/test_claude_code_live_smoke.py`

  Observed 1 skipped because `AGENTRULES_RUN_CLAUDE_CODE_LIVE=1` was not set.
- Ran broad offline validation:

    `PYTHONPATH=src .venv/bin/pytest tests/unit tests/offline`

  Observed 544 passed, 4 warnings from existing `pathspec` deprecations.
- Ran `PYTHONPATH=src .venv/bin/ruff check .` and observed all checks passed.
- Ran `PYTHONPATH=src .venv/bin/pyright` and observed 0 errors, 0 warnings, 0 informations.
- Ran `PYTHONPATH=src .venv/bin/agentrules snapshot sync` and updated `SNAPSHOT.md` for the new docs/live-test paths.

## Changelog

- 2026-05-04: Milestone created.
- 2026-05-04: Expanded milestone with docs, live smoke, validation, rollout, and plan closure tasks.
- 2026-05-04: Completed MS005 implementation and validation. Added operator docs, opt-in live smoke, snapshot sync, broad validation, and final plan closure evidence.
