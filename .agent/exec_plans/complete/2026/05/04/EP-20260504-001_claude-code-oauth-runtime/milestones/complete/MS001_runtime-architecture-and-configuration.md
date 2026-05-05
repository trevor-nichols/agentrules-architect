---
id: EP-20260504-001/MS001
execplan_id: EP-20260504-001
ms: 1
title: Runtime Architecture and Configuration
status: completed
domain: cross-cutting
owner: '@codex'
created: 2026-05-04
updated: '2026-05-04'
tags:
- claude-code
- configuration
- oauth
risk: med
links:
  issue: ''
  docs: internal-docs/integrations/anthropic/agents-sdk/authentication.md
  pr: ''
---

# Runtime Architecture and Configuration

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Establish the Claude Code runtime as a first-class, separately configured provider target without sending any model requests yet. When this milestone is complete, AgentRules can represent Claude Code OAuth runtime settings, persist them safely, resolve the installed `claude` executable, and build an SDK child-process environment that intentionally prefers Claude.ai OAuth subscription credentials over Anthropic API-key credentials.

## Definition of Done

- [x] `ModelProvider.CLAUDE_CODE` exists and is used only for the local Claude Code runtime.
- [x] `CLIConfig` contains a `ClaudeCodeConfig` section with safe defaults and backward-compatible loading for config files that do not include it.
- [x] `src/agentrules/core/configuration/services/claude_code.py` resolves the configured `claude` executable and builds a sanitized environment for OAuth SDK runs.
- [x] Config serialization omits default Claude Code settings to avoid TOML churn and persists only user changes.
- [x] Provider availability reports Claude Code availability from executable and OAuth-friendly environment signals, not from `ANTHROPIC_API_KEY`.
- [x] Unit tests cover defaults, serialization, executable resolution, environment sanitization, and provider availability.
- [x] `python -c "import agentrules"` passes through the repo virtualenv with `PYTHONPATH=src`.

## Scope

### In Scope
- Add `CLAUDE_CODE` to `src/agentrules/core/agents/base.py`.
- Add constants in `src/agentrules/core/configuration/constants.py`: `DEFAULT_CLAUDE_CODE_CLI_PATH`, `CLAUDE_CODE_OAUTH_TOKEN_ENV_VAR`, and the set of Anthropic API-key env vars to sanitize for OAuth runtime calls.
- Add `ClaudeCodeAuthStrategy` and `ClaudeCodeConfig` in `src/agentrules/core/configuration/models.py`.
- Extend `src/agentrules/core/configuration/serde.py` so `claude_code` config loads from and saves to TOML.
- Extend `src/agentrules/core/configuration/manager.py` with accessors such as `get_claude_code_config()`, `set_claude_code_cli_path()`, `resolve_claude_code_executable()`, `is_claude_code_available()`, and `build_claude_code_environment()`.
- Extend `src/agentrules/core/configuration/services/providers.py` so `current_provider_availability()` includes `claude_code`.
- Add or update unit tests in `tests/unit/test_config_service.py` and a new focused test module such as `tests/unit/test_claude_code_config.py`.

### Out of Scope
- Do not call the Claude Agent SDK in this milestone.
- Do not add model presets or factory wiring yet.
- Do not add the interactive CLI settings screen yet.
- Do not modify existing Anthropic API-key behavior beyond ensuring the new provider does not depend on it.

## Workstreams & Tasks

### Workstream A - Provider Identity

| ID | Area | Description | Status |
|----|------|-------------|--------|
| A1 | Agents | Add `ModelProvider.CLAUDE_CODE = "claude_code"` in `src/agentrules/core/agents/base.py`. | completed |
| A2 | Capabilities | Update any provider display helper that assumes the enum is exhaustive. | completed; no display helper is used for Claude Code until MS003 preset work |
| A3 | Tests | Add a small provider enum/display regression test if no adjacent coverage exists. | completed through provider availability/config tests |

### Workstream B - Persisted Runtime Configuration

| ID | Area | Description | Status |
|----|------|-------------|--------|
| B1 | Models | Add `ClaudeCodeConfig` to `CLIConfig` with defaults: `cli_path="claude"`, `auth_strategy="oauth"`, `sanitize_api_key_env=True`. | completed |
| B2 | Serde | Load missing `claude_code` config as defaults and save only non-default values. | completed |
| B3 | Constants | Add Claude Code constants and keep `PROVIDER_ENV_MAP` API-key focused; do not add OAuth token as an API provider key. | completed |
| B4 | Tests | Cover old config payloads, customized CLI path, and default omission on save. | completed |

### Workstream C - Runtime Resolution and Environment Policy

| ID | Area | Description | Status |
|----|------|-------------|--------|
| C1 | Service | Implement `src/agentrules/core/configuration/services/claude_code.py` using `shutil.which` and `Path.expanduser()` patterns from the Codex service. | completed |
| C2 | Security | Build an SDK environment that preserves `CLAUDE_CODE_OAUTH_TOKEN` and removes `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` when sanitization is enabled. | completed |
| C3 | Availability | Report available when the executable resolves and OAuth is plausible via `CLAUDE_CODE_OAUTH_TOKEN` or local CLI credential state cannot be disproven. | completed with executable-based availability; richer auth diagnostics are in MS004 |
| C4 | Tests | Cover env sanitization with and without conflicting Anthropic API-key variables. | completed |

## Risks & Mitigations

- Risk: Removing API-key variables too broadly could surprise existing direct Anthropic API requests.
  Mitigation: Environment sanitization must be scoped to Claude Code SDK child-process calls. `EnvironmentManager.apply_provider_credentials()` should continue to serve the existing Anthropic provider unchanged.
- Risk: It may not be possible to reliably detect keychain-based Claude.ai login without invoking the CLI or SDK.
  Mitigation: Milestone 1 should keep availability conservative around executable presence and explicit OAuth token signals, then Milestone 4 can add richer diagnostics or live checks.
- Risk: Adding a new provider enum can expose unhandled branches.
  Mitigation: Search for `ModelProvider` branches, add explicit handling, and add tests around factory/capability paths in later milestones.

## Validation / QA Plan

- Ran `PYTHONPATH=src .venv/bin/python -c "import agentrules"` from the repo root and observed exit code 0 with no output.
- Ran `PYTHONPATH=src .venv/bin/pytest tests/unit/test_config_service.py tests/unit/utils/test_provider_capabilities.py` and observed 38 passed.
- Initial system-shell validation without the repo virtualenv failed because `python` could not import the local package and `pytest` was not on PATH; the successful validation used the project virtualenv and `PYTHONPATH=src`.
- Manually inspect serialized config in tests to ensure default `claude_code` settings are omitted and customized values round-trip.

## Changelog

- 2026-05-04: Milestone created.
- 2026-05-04: Expanded milestone with provider identity, config, OAuth environment policy, risks, and validation tasks.
- 2026-05-04: Completed MS001 implementation and validation. Added Claude Code config/service support, provider availability, OAuth environment sanitization, tests, and snapshot sync.
