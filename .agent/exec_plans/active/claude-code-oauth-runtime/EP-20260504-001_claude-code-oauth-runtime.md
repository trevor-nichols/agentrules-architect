---
id: EP-20260504-001
title: "Claude Code OAuth Runtime Provider"
status: planned
kind: feature
domain: cross-cutting
owner: "@codex"
created: 2026-05-04
updated: 2026-05-04
tags: [claude-code, anthropic, oauth, runtime-provider]
touches: [cli, agents, security, tests, docs]
risk: med
breaking: false
migration: false
links:
  issue: ""
  pr: ""
  docs: "internal-docs/integrations/anthropic/agents-sdk"
depends_on: []
supersedes: []
---

# EP-20260504-001 - Claude Code OAuth Runtime Provider

This ExecPlan is a living document. Keep `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` up to date as work proceeds.

If `.agent/PLANS.md` exists in this repository, maintain this plan in accordance with that guidance.

## Purpose / Big Picture

AgentRules currently supports Anthropic through direct Anthropic API credentials and supports Codex through a local runtime that can use the user's installed CLI authentication state. This change adds the same local-runtime style for Claude Code: a user who has already authenticated the installed `claude` CLI with Claude.ai OAuth subscription credentials can run AgentRules phases through the Claude Agent SDK without storing an Anthropic API key in AgentRules.

After implementation, a user can run `claude auth login` once, configure AgentRules to use the local Claude Code runtime, select Claude Code runtime presets for one or more analysis phases, and run `agentrules analyze ...`. The observable outcome is that AgentRules creates requests through the Claude Agent SDK, the SDK launches the installed Claude Code CLI as a child process, and the resulting phase outputs are returned in the same shape as the existing providers. API-key based Anthropic requests remain available through the existing `ModelProvider.ANTHROPIC` path, but they are not the target of this plan.

## Scope

This plan is in scope for a new local runtime provider backed by Claude Code and the Python Claude Agent SDK. The provider must authenticate through Claude.ai OAuth subscription credentials available to the installed CLI or through `CLAUDE_CODE_OAUTH_TOKEN` for automated environments. The provider must not require, persist, or prefer `ANTHROPIC_API_KEY`. The implementation must keep API-key Anthropic behavior separate so existing users are not broken.

The work includes configuration data models, serialization, runtime availability checks, CLI settings UI, model presets, provider factory wiring, request building, response parsing, structured output support, streaming support when practical, tests, documentation, and a gated live smoke path. The first implementation should use the SDK-level `query()` API because the SDK already owns the child process protocol. A later optimization may use `ClaudeSDKClient` for long-lived sessions if repeated process startup becomes a measurable bottleneck.

The work is out of scope for offering Anthropic API-key fallback inside the Claude Code runtime provider, adding new non-Claude vendors, changing the existing Codex app-server protocol code, or implementing unrestricted file-editing behavior. The AgentRules analysis pipeline is read-mostly and output-generating; Claude Code runtime tool permissions should default to read-oriented behavior and explicit non-interactive denial for unsafe tool requests.

## Context and Orientation

The existing provider interface is `BaseArchitect` in `src/agentrules/core/agents/base.py`. Provider implementations live in `src/agentrules/core/agents/<provider>/` and are instantiated by `ArchitectFactory.create_architect()` in `src/agentrules/core/agents/factory/factory.py`. The current Anthropic implementation in `src/agentrules/core/agents/anthropic/` uses the Anthropic Messages API client and `ANTHROPIC_API_KEY`. The current Codex implementation in `src/agentrules/core/agents/codex/` uses a local process runtime and is the closest architectural precedent for this work.

The configuration layer stores user preferences in dataclasses in `src/agentrules/core/configuration/models.py`, serializes them in `src/agentrules/core/configuration/serde.py`, exposes behavior through `src/agentrules/core/configuration/manager.py`, and adapts environment variables through `src/agentrules/core/configuration/environment.py`. Codex-specific configuration is isolated under `src/agentrules/core/configuration/services/codex.py`; the Claude Code runtime should receive a parallel service rather than being mixed into provider API-key storage.

The CLI settings screens live under `src/agentrules/cli/ui/settings/`. Codex has a runtime settings screen in `src/agentrules/cli/ui/settings/codex.py` and synchronous diagnostics in `src/agentrules/cli/services/codex_runtime.py`. The Claude Code runtime should follow the same user experience pattern while avoiding a browser login flow implemented by AgentRules. Claude Code login already belongs to the installed CLI, so AgentRules should diagnose whether `claude` is available, whether the environment is configured for OAuth use, and provide clear commands such as `claude auth login` and `claude setup-token`.

The pipeline contains provider-specific branching helpers in `src/agentrules/core/utils/provider_capabilities.py`. Codex is currently treated as a repository-aware runtime: Phase 3 can avoid embedding every selected file because Codex can read the repository itself. Claude Code should also be treated as repository-aware because the Agent SDK exposes Claude Code tools such as `Read`, `Glob`, `Grep`, and `WebSearch`, subject to permission controls.

The relevant internal docs are in `internal-docs/integrations/anthropic/agents-sdk/`. The important facts embedded in this plan are: the Python SDK exposes `query(prompt, options)`; `ClaudeAgentOptions` accepts `model`, `cwd`, `cli_path`, `system_prompt`, `tools`, `allowed_tools`, `disallowed_tools`, `permission_mode`, `output_format`, `env`, `include_partial_messages`, `thinking`, and `effort`; structured output uses `output_format={"type": "json_schema", "schema": ...}`; the SDK launches the Claude Code CLI as a child process; the CLI can read normal Claude Code credentials; `CLAUDE_CODE_OAUTH_TOKEN` can be used for automation; and `ANTHROPIC_API_KEY` takes precedence over Claude.ai subscription auth, so the runtime must deliberately avoid passing it when OAuth mode is selected.

## Plan of Work

First, add the provider identity and configuration foundation. Add a `ModelProvider.CLAUDE_CODE` enum value in `src/agentrules/core/agents/base.py`, a `ClaudeCodeConfig` dataclass in `src/agentrules/core/configuration/models.py`, default constants such as `DEFAULT_CLAUDE_CODE_CLI_PATH = "claude"`, and a configuration service in `src/agentrules/core/configuration/services/claude_code.py`. This service should resolve the executable path with `shutil.which`, normalize optional settings, and build a small immutable launch/options configuration for the SDK adapter. The service should support at least `cli_path`, `auth_strategy`, and `sanitize_api_key_env`. The initial `auth_strategy` should be `"oauth"` only or default to `"oauth"` with future room for `"inherit"` if needed. `sanitize_api_key_env` should default to true so AgentRules does not pass `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` to SDK child processes when the user chooses Claude.ai OAuth subscription auth.

Second, add the Claude Code SDK adapter package under `src/agentrules/core/agents/claude_code/`. Keep it parallel to existing providers with `architect.py`, `request_builder.py`, `response_parser.py`, `client.py`, `errors.py`, and `__init__.py`. The first adapter should depend on `claude-agent-sdk` in `pyproject.toml` and import it lazily so importing `agentrules` remains safe in environments that have not installed optional runtime pieces. `ClaudeCodeArchitect` should implement `BaseArchitect` and should look structurally similar to `CodexArchitect`: format or accept the prompt, resolve the system prompt once, prepare a request, log a token estimate, execute the SDK query, parse messages, and return `{"agent": ..., "findings": ..., "tool_calls": ...}` plus `structured_output` when present.

Third, map AgentRules request semantics into Claude Agent SDK options. The request builder should set `ClaudeAgentOptions.model` from the selected model, `cwd` from context keys such as `cwd` or `_claude_code_cwd`, `cli_path` from configuration, and `system_prompt` from the resolved AgentRules system prompt. It should pass structured output schemas through `output_format` for Phase 2, Phase 4, Phase 5, and final analysis using the existing schema builders in `src/agentrules/core/utils/structured_outputs.py`, extended for the new provider. It should set a conservative tool policy: use Claude Code's standard tool preset if the SDK requires explicit tools, auto-approve read-oriented tools such as `Read`, `Glob`, and `Grep`, disallow write and shell tools by default for analysis phases, and use `permission_mode="dontAsk"` to prevent hidden interactive prompts during headless analysis. The exact SDK names should be confirmed against the installed package during implementation, but the behavior must remain deterministic and non-interactive.

Fourth, wire the provider into presets and pipeline behavior. Add `create_claude_code_config()` in `src/agentrules/core/types/models.py`, static Claude Code presets in `src/agentrules/config/agents.py`, dynamic preset helpers in `src/agentrules/core/configuration/model_presets.py` if the SDK or CLI can expose a model catalog, and factory wiring in `src/agentrules/core/agents/factory/factory.py`. Update `src/agentrules/core/utils/provider_capabilities.py` so Claude Code is repository-aware, supports runtime-native web search, and does not require Phase 3 to embed file contents. Update provider availability in `src/agentrules/core/configuration/services/providers.py` so Claude Code availability is based on the configured `claude` executable and OAuth-friendly environment, not on `ANTHROPIC_API_KEY`.

Fifth, add CLI UX and diagnostics. Create `src/agentrules/cli/services/claude_code_runtime.py` and `src/agentrules/cli/ui/settings/claude_code.py`, then add a settings menu entry next to "Codex runtime". The diagnostics should show configured executable, resolved executable, auth mode, whether `CLAUDE_CODE_OAUTH_TOKEN` is present, whether conflicting API-key env vars are currently set in the parent environment, and the guidance needed to fix the state. AgentRules should not manage Claude.ai OAuth login itself; it should tell the user to run `claude auth login` for local use or `claude setup-token` for automation. If a cheap status command exists in the installed CLI, implementation may use it; otherwise diagnostics can stay executable/env based and reserve live verification for a gated smoke test.

Sixth, validate with focused tests before broad tests. Add unit tests for config serialization, executable resolution, environment sanitization, request building, response parsing, provider factory wiring, provider capabilities, model preset availability, CLI guidance text, and structured output handling. Add a fake SDK response stream fixture so unit tests do not require Claude Code or network access. Add a live smoke test under `tests/live/`, gated by explicit flags such as `AGENTRULES_RUN_CLAUDE_CODE_LIVE=1` and `pytest --run-live`, that runs a tiny query through the user's authenticated Claude Code runtime and validates a simple structured response.

## Milestones

Milestone 1, `EP-20260504-001/MS001 Runtime Architecture and Configuration`, establishes the provider identity, persisted config, executable resolution, environment policy, and dependency declaration without sending model requests. At the end of this milestone the project can load and save Claude Code runtime settings, decide whether the runtime is available, and build a sanitized SDK environment that prefers Claude.ai OAuth subscription credentials.

Milestone 2, `EP-20260504-001/MS002 Claude Agent SDK Adapter`, implements the provider package and proves that the adapter can translate AgentRules prompts into SDK queries and parse SDK responses back into AgentRules result dictionaries. At the end of this milestone fake SDK tests cover successful text output, structured output, tool call capture, and common SDK errors.

Milestone 3, `EP-20260504-001/MS003 Pipeline and Preset Integration`, makes Claude Code selectable for phases and teaches the pipeline to treat it as a repository-aware runtime. At the end of this milestone users can choose Claude Code presets and the factory returns `ClaudeCodeArchitect` for those presets.

Milestone 4, `EP-20260504-001/MS004 CLI UX Diagnostics and Auth Guidance`, adds the interactive settings screen and runtime diagnostics. At the end of this milestone the CLI clearly tells the user how to use their installed Claude Code OAuth state and warns about parent-process API-key variables that would otherwise override subscription auth.

Milestone 5, `EP-20260504-001/MS005 Validation Documentation and Rollout`, completes docs, live smoke coverage, import smoke validation, and rollout notes. At the end of this milestone the implementation has a deterministic offline test suite and an opt-in live verification path for a real authenticated Claude Code CLI.

## Progress

- [x] (2026-05-04 21:42 America/New_York) Created ExecPlan and five active milestones with `agentrules execplan new` and `agentrules execplan milestone new`.
- [x] (2026-05-04 21:55 America/New_York) Drafted the implementation plan around Claude Code Claude.ai OAuth subscription auth, separate from Anthropic API-key auth.
- [x] (2026-05-04 21:48 America/New_York) User approved the plan and requested milestone-by-milestone execution, validation, archiving, and commits.
- [x] (2026-05-04 22:15 America/New_York) Milestone 1 implementation complete: provider identity, Claude Code runtime config, OAuth environment sanitization, availability checks, tests, and snapshot sync are in place.
- [x] (2026-05-04 22:35 America/New_York) Milestone 2 implementation complete: Claude Code Agent SDK adapter, request builder, lazy client, response parser, structured output mapping, tests, ruff, pyright, and snapshot sync are in place.
- [ ] Milestone 3 implementation complete.
- [ ] Milestone 4 implementation complete.
- [ ] Milestone 5 implementation complete.
- [ ] Final validation complete.

## Surprises & Discoveries

- Observation: The Python Agent SDK is closer to the Codex runtime integration than to the existing Anthropic Messages API integration because it launches the installed Claude Code CLI as a child process.
  Evidence: `internal-docs/integrations/anthropic/agents-sdk/observability.md` states that the Agent SDK runs the Claude Code CLI as a child process and communicates over a local pipe.
- Observation: The SDK provides structured output directly, which means the plan can reuse AgentRules schema builders instead of relying only on prompt-only JSON instructions.
  Evidence: `internal-docs/integrations/anthropic/agents-sdk/structured-outputs.md` describes `output_format` with `type: "json_schema"` and a final `structured_output` field.
- Observation: Parent-process API-key variables are a practical implementation risk even though this plan intentionally uses OAuth subscription auth.
  Evidence: `internal-docs/integrations/anthropic/agents-sdk/authentication.md` documents that `ANTHROPIC_API_KEY` takes precedence over Claude.ai subscription OAuth credentials.
- Observation: The repo's system shell is not configured like the project virtualenv.
  Evidence: `python -c "import agentrules"` failed with `ModuleNotFoundError` and `pytest` was not on PATH, while `PYTHONPATH=src .venv/bin/python -c "import agentrules"` and `PYTHONPATH=src .venv/bin/pytest ...` succeeded.
- Observation: Existing researcher-mode tests were sensitive to ambient model preset state.
  Evidence: The first MS001 focused test run failed because the researcher phase resolved to a runtime-native Codex preset; making those tests explicitly select non-runtime `gpt5-mini` restored the intended assertion and the focused suite passed.
- Observation: The installed Claude Agent SDK matches the documented package and import names.
  Evidence: `uv add claude-agent-sdk` installed version `0.1.73`, and runtime inspection confirmed `claude_agent_sdk.query`, `ClaudeAgentOptions`, `AssistantMessage`, `ResultMessage`, `TextBlock`, and `ToolUseBlock`.
- Observation: The SDK message dataclasses expose enough fields for deterministic offline parser tests.
  Evidence: `AssistantMessage.content`, `ResultMessage.structured_output`, `ResultMessage.is_error`, and `ToolUseBlock.input` were instantiated directly in unit tests without contacting Claude.

## Decision Log

- Decision: Implement Claude Code as a distinct runtime provider rather than changing `ModelProvider.ANTHROPIC`.
  Rationale: The existing Anthropic provider is a direct Messages API adapter keyed by `ANTHROPIC_API_KEY`; the Claude Code path uses a local CLI process and OAuth credentials. Keeping the identities separate avoids surprising existing API-key users and matches the Codex precedent.
  Date/Author: 2026-05-04 / @codex
- Decision: Default the Claude Code runtime to Claude.ai OAuth subscription auth and intentionally avoid API-key fallback inside this provider.
  Rationale: The requested product direction is confirmed OAuth subscription auth through the installed Claude Code CLI. API-key fallback would blur the operational model and could accidentally bill or rate-limit through the wrong credential path.
  Date/Author: 2026-05-04 / @codex
- Decision: Use the SDK `query()` API for the first implementation instead of hand-rolling a subprocess protocol.
  Rationale: The Agent SDK already owns the CLI child-process protocol, typed options, structured output, hooks, permissions, and message types. Starting with the supported SDK surface reduces implementation risk.
  Date/Author: 2026-05-04 / @codex
- Decision: Treat Claude Code as a repository-aware runtime like Codex.
  Rationale: Claude Code exposes native repository tools such as `Read`, `Glob`, and `Grep`, so AgentRules should not have to inline all file contents for Phase 3 when this provider is selected.
  Date/Author: 2026-05-04 / @codex
- Decision: Default analysis runs to non-interactive, read-oriented permissions.
  Rationale: AgentRules analysis phases should be deterministic in CLI and CI contexts. Hidden interactive permission prompts or unrestricted write/shell tools would make runs fragile and harder to audit.
  Date/Author: 2026-05-04 / @codex
- Decision: Keep Claude Code OAuth env sanitization as a child-environment builder rather than mutating process-wide provider credentials.
  Rationale: Existing Anthropic API-key behavior must remain intact for `ModelProvider.ANTHROPIC`; the Claude Code runtime needs a sanitized environment only when launching SDK/CLI child processes.
  Date/Author: 2026-05-04 / @codex
- Decision: Defer `stream_analyze()` for Claude Code until a later pass.
  Rationale: MS002 covers the non-streaming provider contract needed by the pipeline and verifies `query()` output parsing. Streaming requires mapping partial SDK events into AgentRules `StreamChunk` semantics and is not needed to unblock phase execution.
  Date/Author: 2026-05-04 / @codex

## Outcomes & Retrospective

This section will be completed as milestones finish. Before implementation begins, the expected outcome is a selectable Claude Code runtime provider that uses the user's Claude.ai OAuth subscription credentials through the installed `claude` CLI, keeps the Anthropic API provider unchanged, and has both offline tests and a gated live smoke test.

## Concrete Steps

Work from the repository root:

    cd /Volumes/AGENAI/Coding/public-github/agentrules-architect

For Milestone 1, add config and provider identity files, then run:

    python -c "import agentrules"
    pytest tests/unit/test_config_service.py tests/unit/test_cli_codex_settings.py tests/unit/utils/test_provider_capabilities.py

For Milestone 2, add the SDK adapter and fake SDK tests, then run:

    pytest tests/unit/agents/test_claude_code_request_builder.py tests/unit/agents/test_claude_code_response_parser.py tests/unit/agents/test_claude_code_architect.py

For Milestone 3, wire presets and provider selection, then run:

    pytest tests/unit/test_model_overrides.py tests/unit/test_cli_model_picker_ui.py tests/unit/agents/test_system_prompt_policy.py tests/unit/analysis/test_phase3_packing.py

For Milestone 4, add CLI diagnostics, then run:

    pytest tests/unit/test_cli_claude_code_settings.py tests/unit/test_config_service.py

For Milestone 5, add documentation and smoke coverage, then run:

    pytest tests/unit tests/offline
    python -c "import agentrules"

The live smoke path must remain opt-in. A user with Claude Code installed and authenticated should be able to run:

    AGENTRULES_RUN_CLAUDE_CODE_LIVE=1 pytest --run-live tests/live/test_claude_code_live_smoke.py

The live test should skip with a clear reason when `claude` is unavailable, the OAuth token/login state is unavailable, or the explicit live flag is missing.

## Validation and Acceptance

Acceptance is behavior-based. A user who has run `claude auth login` with Claude.ai OAuth credentials can open AgentRules settings, see a Claude Code runtime status, select a Claude Code preset for a phase, and run an analysis without entering an Anthropic API key. The run should produce the normal phase output dictionaries and final artifacts. If `ANTHROPIC_API_KEY` exists in the parent shell, the Claude Code runtime should either sanitize it for SDK child processes or warn clearly when sanitization is disabled.

Offline validation must prove that importability still works, configuration remains backward-compatible for existing config files, the existing Anthropic API provider still uses API-key semantics, the new Claude Code provider is selectable only when runtime availability checks pass, and the pipeline treats Claude Code as repository-aware. Unit tests must not require network access or an installed Claude Code CLI.

Live validation must prove one minimal end-to-end SDK request through the user's installed Claude Code CLI. The smoke should ask for a deterministic tiny structured response such as an object with `provider: "claude_code"` and `ok: true`, then assert that the parsed result matches the schema.

## Idempotence and Recovery

All configuration changes must be additive and backward-compatible. Loading old config files that lack a Claude Code section must produce defaults without rewriting unrelated settings. Saving defaults should avoid noisy TOML churn, following the Codex pattern where default runtime settings are omitted from persisted config.

The implementation should avoid mutating user Claude Code credentials. AgentRules should not edit `~/.claude`, keychain entries, or Claude Code settings except when the user explicitly configures AgentRules-owned settings in this project. Diagnostics may read executable availability and environment variables, but login and token generation remain user-owned CLI actions.

If SDK imports fail, the runtime provider should fail with an actionable message that names the missing package and the install path. If the configured executable cannot be resolved, settings should remain intact and diagnostics should show the configured path and the expected default command name.

## Interfaces and Dependencies

Add `claude-agent-sdk` to `pyproject.toml` dependencies, unless implementation confirms a different package name in the installed docs or package index. Imports should be lazy inside `src/agentrules/core/agents/claude_code/client.py` so `python -c "import agentrules"` remains resilient.

Add `ModelProvider.CLAUDE_CODE = "claude_code"` in `src/agentrules/core/agents/base.py`.

Add `ClaudeCodeConfig` in `src/agentrules/core/configuration/models.py` with a shape similar to:

    ClaudeCodeAuthStrategy = Literal["oauth"]

    @dataclass
    class ClaudeCodeConfig:
        cli_path: str = "claude"
        auth_strategy: ClaudeCodeAuthStrategy = "oauth"
        sanitize_api_key_env: bool = True

Add a config service in `src/agentrules/core/configuration/services/claude_code.py` with functions equivalent in purpose to Codex helpers:

    get_claude_code_config(config: CLIConfig) -> ClaudeCodeConfig
    set_claude_code_cli_path(config: CLIConfig, cli_path: str | None) -> None
    set_claude_code_sanitize_api_key_env(config: CLIConfig, enabled: bool) -> None
    resolve_claude_code_executable(config: CLIConfig) -> str | None
    is_claude_code_available(config: CLIConfig, getenv: Callable[[str], str | None]) -> bool
    build_claude_code_environment(config: CLIConfig, getenv: Callable[[str], str | None]) -> dict[str, str]

Add `src/agentrules/core/agents/claude_code/request_builder.py` that returns a prepared request containing the prompt, token payload, SDK options, and output schema marker. Add `src/agentrules/core/agents/claude_code/response_parser.py` that understands SDK `AssistantMessage`, `ResultMessage`, `StreamEvent`, text blocks, tool-use blocks, `structured_output`, usage, and error subtypes.

Add docs in `docs/claude-code-runtime.md` covering local setup, CI setup with `CLAUDE_CODE_OAUTH_TOKEN`, environment precedence, settings UI, live smoke command, and troubleshooting.

## Artifacts and Notes

The implementation should update `.agent/exec_plans/registry.json` whenever the plan metadata changes materially by running:

    agentrules execplan-registry update

The implementation should update `SNAPSHOT.md` if new tracked files outside excluded plan metadata are added and the snapshot policy includes them:

    agentrules snapshot sync
