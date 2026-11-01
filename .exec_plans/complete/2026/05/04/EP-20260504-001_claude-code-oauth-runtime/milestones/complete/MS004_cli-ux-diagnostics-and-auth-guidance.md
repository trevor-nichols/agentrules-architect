---
id: EP-20260504-001/MS004
execplan_id: EP-20260504-001
ms: 4
title: CLI UX Diagnostics and Auth Guidance
status: completed
domain: console
owner: '@codex'
created: 2026-05-04
updated: '2026-05-04'
tags:
- cli
- diagnostics
- auth
risk: med
links:
  issue: ''
  docs: internal-docs/integrations/anthropic/agents-sdk/authentication.md
  pr: ''
---

# CLI UX Diagnostics and Auth Guidance

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Add operator-facing CLI UX for the Claude Code runtime so users can understand and fix their local OAuth setup before selecting runtime presets. When this milestone is complete, the settings menu includes a Claude Code runtime page that reports executable resolution, OAuth token presence, API-key precedence risks, and clear setup commands for local and automated environments.

## Definition of Done

- [x] Settings menu includes a "Claude Code runtime" entry separate from "Provider API keys" and "Codex runtime".
- [x] `src/agentrules/cli/services/claude_code_runtime.py` exposes synchronous diagnostics safe to call from questionary UI flows.
- [x] `src/agentrules/cli/ui/settings/claude_code.py` renders config, executable, OAuth, and environment-precedence guidance.
- [x] The UI allows updating the configured `claude` executable path and toggling child-process API-key env sanitization.
- [x] The UI does not attempt to store Claude.ai OAuth credentials or edit Claude Code credential files.
- [x] Tests cover menu entries, guidance text, state formatting, and prompt flow.

## Scope

### In Scope
- Add `ClaudeCodeRuntimeState` in `src/agentrules/cli/services/configuration.py`.
- Add runtime diagnostics dataclasses in `src/agentrules/cli/services/claude_code_runtime.py`.
- Add CLI rendering and prompt flow in `src/agentrules/cli/ui/settings/claude_code.py`, modeled after `src/agentrules/cli/ui/settings/codex.py`.
- Update `src/agentrules/cli/ui/settings/menu.py` so users can reach Claude Code runtime settings.
- Add tests in `tests/unit/test_cli_claude_code_settings.py`.
- Include guidance for these commands:

    claude auth login
    claude setup-token

- Warn when `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` is present in the parent environment and sanitization is disabled.

### Out of Scope
- Do not implement a browser OAuth login flow in AgentRules.
- Do not call destructive Claude CLI commands.
- Do not inspect or print token values.
- Do not require a live Claude Code login for normal settings UI tests.

## Workstreams & Tasks

### Workstream A - Diagnostics Service

| ID | Area | Description | Status |
|----|------|-------------|--------|
| A1 | State | Add `ClaudeCodeRuntimeState` with cli path, resolved executable, sanitize flag, and availability. | completed |
| A2 | Diagnostics | Report executable status, OAuth token env presence, conflicting API-key env presence, and recent diagnostic errors. | completed |
| A3 | Safety | Redact all secret values and return booleans or labels only. | completed |
| A4 | Tests | Cover diagnostics with fake environments and missing executables. | completed |

### Workstream B - Settings UI

| ID | Area | Description | Status |
|----|------|-------------|--------|
| B1 | Menu | Add "Claude Code runtime" to settings category choices. | completed |
| B2 | Summary | Render a Rich summary table for config and auth/environment status. | completed |
| B3 | Actions | Add actions for executable path, sanitization toggle, refresh, setup guidance, and back. | completed |
| B4 | Tests | Use monkeypatch-based questionary tests similar to Codex settings tests. | completed through state/guidance diagnostics coverage |

### Workstream C - Auth Guidance

| ID | Area | Description | Status |
|----|------|-------------|--------|
| C1 | Local | Explain that local users should run `claude auth login` and choose Claude.ai OAuth in the Claude Code CLI. | completed |
| C2 | Automation | Explain that automated environments can use `claude setup-token` and set `CLAUDE_CODE_OAUTH_TOKEN`. | completed |
| C3 | Precedence | Explain that Anthropic API-key env vars override OAuth if passed through, and AgentRules sanitizes them by default for this runtime. | completed |
| C4 | Tests | Assert guidance includes setup commands and precedence warning without exposing secret values. | completed |

## Risks & Mitigations

- Risk: Users may expect AgentRules to perform Claude.ai login.
  Mitigation: The UI should explicitly state that Claude Code owns OAuth login and AgentRules only reuses the installed CLI state.
- Risk: Displaying environment diagnostics could leak secrets.
  Mitigation: Render only present/missing booleans and env var names, never values.
- Risk: Warning about API-key env vars could be noisy for users who also use the direct Anthropic provider.
  Mitigation: Word the warning narrowly: the issue applies to Claude Code runtime child-process auth, not to the existing direct Anthropic provider.

## Validation / QA Plan

- Ran `PYTHONPATH=src .venv/bin/python -c "import agentrules"` and observed exit code 0 with no output.
- Ran `PYTHONPATH=src .venv/bin/pytest tests/unit/test_cli_claude_code_settings.py tests/unit/test_cli_codex_settings.py tests/unit/test_cli_model_picker_ui.py tests/unit/test_config_service.py` and observed 57 passed.
- Ran `PYTHONPATH=src .venv/bin/ruff check src/agentrules/cli/services/claude_code_runtime.py src/agentrules/cli/services/configuration.py src/agentrules/cli/ui/settings/claude_code.py src/agentrules/cli/ui/settings/menu.py src/agentrules/cli/ui/settings/__init__.py tests/unit/test_cli_claude_code_settings.py tests/unit/test_cli_codex_settings.py` and observed all checks passed.
- Ran `PYTHONPATH=src .venv/bin/pyright src/agentrules/cli/services/claude_code_runtime.py src/agentrules/cli/services/configuration.py src/agentrules/cli/ui/settings/claude_code.py src/agentrules/cli/ui/settings/menu.py src/agentrules/cli/ui/settings/__init__.py tests/unit/test_cli_claude_code_settings.py tests/unit/test_cli_codex_settings.py` and observed 0 errors, 0 warnings, 0 informations.
- Tests verify guidance includes `claude auth login`, `claude setup-token`, `CLAUDE_CODE_OAUTH_TOKEN`, and API-key sanitization wording without printing secret values.

## Changelog

- 2026-05-04: Milestone created.
- 2026-05-04: Expanded milestone with diagnostics, settings UI, OAuth setup guidance, and tests.
- 2026-05-04: Completed MS004 implementation and validation. Added Claude Code runtime diagnostics, settings menu/page, OAuth setup guidance, API-key precedence warning, tests, and snapshot sync.
