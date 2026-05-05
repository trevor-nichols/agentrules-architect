---
id: EP-20260505-001/MS003
execplan_id: EP-20260505-001
ms: 3
title: "Respect SDK CLI Resolution"
status: planned
domain: backend
owner: "@codex"
created: 2026-05-05
updated: 2026-05-05
tags: [claude-code, configuration, cli-resolution]
risk: med
links:
  issue: ""
  docs: "internal-docs/integrations/anthropic/agents-sdk/overview.md"
  pr: ""
---

# Respect SDK CLI Resolution

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Make the Claude Code runtime honor the SDK's documented default binary resolution. At the end of this milestone, AgentRules no longer treats a standalone `claude` executable as mandatory when the SDK can use its bundled/default runtime, while explicit bad paths still fail fast with clear diagnostics.

## Definition of Done

- [ ] `ClaudeCodeConfig.cli_path` can represent "SDK default" as `None`.
- [ ] Default serialized config does not write a `claude_code.cli_path` value.
- [ ] `prepare_request()` omits `cli_path` from SDK options when `cli_path` is `None`.
- [ ] Provider availability is true when the Claude Agent SDK is importable and no explicit invalid CLI path is configured.
- [ ] Diagnostics clearly separate SDK runtime availability from optional operator commands like `claude auth login` and `claude setup-token`.
- [ ] Config, CLI settings, model preset gating, and request-builder tests cover default SDK resolution and explicit path behavior.

## Scope

### In Scope
- Update `src/agentrules/core/configuration/models.py` so `ClaudeCodeConfig.cli_path` is `str | None`.
- Update normalization and serialization in `src/agentrules/core/configuration/services/claude_code.py` and `src/agentrules/core/configuration/serde.py`.
- Add an SDK importability helper, preferably using `importlib.util.find_spec("claude_agent_sdk")`, so provider availability does not import heavy SDK modules at configuration load time.
- Adjust `src/agentrules/cli/services/claude_code_runtime.py` and `src/agentrules/cli/ui/settings/claude_code.py` display text for "SDK default" versus explicit executable.
- Update `tests/unit/test_config_service.py`, `tests/unit/test_cli_claude_code_settings.py`, `tests/unit/test_model_overrides.py`, and `tests/unit/agents/test_claude_code_request_builder.py`.
- Update `docs/claude-code-runtime.md`.

### Out of Scope
- Do not validate actual OAuth credentials in provider availability. Authentication remains verified by the gated live smoke or by the SDK request result.
- Do not remove support for explicit `AGENTRULES_CLAUDE_CODE_CLI` in live tests.
- Do not implement Claude Code login flows inside AgentRules.

## Workstreams & Tasks

- [ ] Config model: represent the default as `None` and only normalize non-empty user input to a string path/command.
- [ ] Availability: return false for an explicit non-resolvable path, true for SDK-default mode when the package is importable, and preserve false when the SDK is missing.
- [ ] Request options: include `cli_path` only for explicit user settings.
- [ ] CLI UX: show "SDK default" or similar in the settings table, and keep guidance for local setup commands.
- [ ] Tests: cover no `[claude_code]` section persisted by default, explicit path persistence, explicit bad path unavailability, and preset gating under SDK-default availability.

## Risks & Mitigations

- Risk: Showing Claude Code presets when the SDK is installed but the user is not authenticated may lead to runtime auth errors.
  Mitigation: Keep CLI guidance prominent and keep the live smoke gated. This mirrors the existing behavior where executable availability does not prove authentication.
- Risk: Changing the default `cli_path` representation may break existing config tests and docs.
  Mitigation: Treat this as a small config schema evolution with backward-compatible TOML reads. Existing persisted `cli_path = "claude"` should keep working.

## Validation / QA Plan

- Run `PYTHONPATH=src .venv/bin/pytest tests/unit/test_config_service.py tests/unit/test_cli_claude_code_settings.py tests/unit/test_model_overrides.py tests/unit/agents/test_claude_code_request_builder.py`.
- Run `PYTHONPATH=src .venv/bin/python -c "import importlib.util; raise SystemExit(0 if importlib.util.find_spec('claude_agent_sdk') else 1)"`.
- Run `PYTHONPATH=src .venv/bin/ruff check src/agentrules/core/configuration src/agentrules/cli/services/claude_code_runtime.py src/agentrules/cli/ui/settings/claude_code.py tests/unit/test_config_service.py tests/unit/test_cli_claude_code_settings.py`.
- Green means default config uses SDK resolution, explicit configured paths remain validated, and runtime options do not include `cli_path` unless the user configured one.

## Changelog

- 2026-05-05: Milestone created.
- 2026-05-05: Drafted SDK-default CLI resolution scope from Claude Code runtime review finding 3.
