---
id: EP-20260505-001
title: Harden Claude Code Runtime Provider
status: done
kind: refactor
domain: cross-cutting
owner: '@codex'
created: 2026-05-05
updated: '2026-05-05'
tags:
- claude-code
- agent-sdk
- provider-runtime
- hardening
touches:
- cli
- agents
- security
- tests
- docs
risk: med
breaking: false
migration: false
links:
  issue: ''
  pr: ''
  docs: internal-docs/integrations/anthropic/agents-sdk
depends_on:
- EP-20260504-001
supersedes: []
---

# EP-20260505-001 - Harden Claude Code Runtime Provider

This ExecPlan is a living document. Keep `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` up to date as work proceeds.

If `.agent/PLANS.md` exists in this repository, maintain this plan in accordance with that guidance.

## Purpose / Big Picture

The current Claude Code runtime provider works in the focused unit suite, but review found five long-term risks in the integration boundary. This plan hardens that provider so AgentRules can route analysis phases through the Claude Agent SDK while preserving Claude Code's built-in behavior, bounding agent execution, respecting the SDK's own binary resolution path, keeping provider object coercion auditable, and making final-analysis failures explicit instead of silently producing placeholder output.

After this plan is implemented, a user can select a Claude Code runtime preset, run AgentRules in a repository, and trust that the runtime uses the Claude Code prompt preset with AgentRules instructions appended, executes within deterministic turn and timeout limits, and remains selectable even when the SDK's bundled Claude Code binary is the runtime path. The work is verified by focused Claude Code unit tests, config and CLI tests, import smoke, ruff, pyright, offline tests, and the existing gated live smoke test.

## Scope

In scope: all five review findings from the first Claude Agent SDK implementation on branch `cc-agents-sdk`. The affected areas are the Claude Code provider package under `src/agentrules/core/agents/claude_code/`, the configuration layer under `src/agentrules/core/configuration/`, provider utility code under `src/agentrules/core/utils/`, CLI runtime diagnostics under `src/agentrules/cli/`, tests under `tests/unit/` and `tests/live/`, and operator documentation in `docs/claude-code-runtime.md`.

Out of scope: changing the existing direct Anthropic API-key provider, adding file-editing behavior to Claude Code analysis phases, switching from SDK `query()` to `ClaudeSDKClient`, adding a new authentication manager for Claude.ai OAuth, or broadly rewriting unrelated provider adapters. Where a finding touches a pre-existing pattern, this plan makes the Claude Code path correct and establishes the shared helper or contract needed for future cleanup without turning this into a full provider migration.

## Context and Orientation

The existing Claude Code implementation was added by `EP-20260504-001` and lives mostly in `src/agentrules/core/agents/claude_code/`. `request_builder.py` translates AgentRules model and phase context into `ClaudeAgentOptions` arguments. `client.py` lazy-imports `claude_agent_sdk` and calls `query()`. `response_parser.py` converts SDK message objects into AgentRules result dictionaries. The provider is wired through `ModelProvider.CLAUDE_CODE`, `src/agentrules/core/agents/factory/factory.py`, `src/agentrules/config/agents.py`, and `src/agentrules/core/utils/provider_capabilities.py`.

The internal SDK documentation under `internal-docs/integrations/anthropic/agents-sdk/` is the source of truth for this plan. The important facts are embedded here so the plan is self-contained. The Python SDK exposes `query(prompt, options)`, which creates a fresh session for each request and yields SDK messages until a final `ResultMessage`. `ClaudeAgentOptions` accepts `model`, `cwd`, `cli_path`, `env`, `tools`, `allowed_tools`, `disallowed_tools`, `permission_mode`, `output_format`, `max_turns`, `max_budget_usd`, `thinking`, and `effort`. Structured outputs use `output_format={"type": "json_schema", "schema": ...}` and validated data appears as `ResultMessage.structured_output`. A raw string passed as `system_prompt` replaces Claude Code's default system prompt, while `{"type": "preset", "preset": "claude_code", "append": "..."}` preserves Claude Code's built-in prompt and appends application instructions. The SDK can bundle a native Claude Code binary, so `cli_path` should be optional unless the user explicitly configures a path.

The five review findings are:

1. `src/agentrules/core/agents/claude_code/request_builder.py` passes AgentRules instructions as a raw `system_prompt` string, replacing Claude Code's built-in prompt.
2. Claude Code requests have no `max_turns`, no cost ceiling, and no outer timeout around the SDK iterator.
3. Runtime availability is hard-coupled to resolving a `claude` executable even though the SDK can supply its own binary when `cli_path` is omitted.
4. `src/agentrules/core/agents/claude_code/response_parser.py` adds another local `_to_dict` object-coercion helper instead of using a central provider utility.
5. `src/agentrules/core/analysis/final_analysis.py` was changed to swallow final-analysis failures and return placeholder output, which diverges from Phase 5 and the repository's fail-fast directive.

## Plan of Work

First, restore the Claude Code prompt contract. `prepare_request()` should build `options["system_prompt"]` as the Claude Code preset object with `append` set to the resolved AgentRules system prompt. Use `exclude_dynamic_sections=True` when the installed SDK supports it, because the internal docs say it keeps dynamic working-directory context out of the system prompt and improves cacheability while preserving the prompt preset. Add a request-builder test that instantiates `ClaudeAgentOptions(**options)` to prove the exact payload is accepted by the installed SDK.

Second, add execution guardrails. Extend Claude Code runtime configuration with conservative defaults for maximum agent turns and request timeout, and optionally a maximum USD budget. Keep SDK options separate from AgentRules-only execution controls: `max_turns` and `max_budget_usd` belong in `ClaudeAgentOptions`, while timeout belongs around the async collection of the SDK iterator in `client.py`. The implementation should produce clear `ClaudeCodeExecutionError` messages for timeouts and SDK failures.

Third, respect SDK CLI resolution. Change the Claude Code runtime config so `cli_path` can be `None`, meaning "let the SDK resolve its bundled/default Claude Code binary." Only pass `cli_path` into SDK options when a user configured one. Availability should consider the SDK importability plus explicit path validity, not only `shutil.which("claude")`. CLI diagnostics should still explain that `claude auth login` or `claude setup-token` may require a `claude` command for operator setup, but provider selection should not be blocked merely because the SDK will use its bundled runtime.

Fourth, centralize provider object coercion. Add `src/agentrules/core/utils/provider_utils.py` with an audited `sdk_object_to_dict()` helper that handles dicts, mappings, dataclasses, Pydantic-style `model_dump()`, SDK `to_dict()` / `dict()`, and plain objects via public attributes. Replace Claude Code response parser's local `_to_dict` with this helper and add focused tests. Do not bulk-migrate every provider in this plan unless the change is trivial and covered by existing tests; the key outcome is that new Claude Code code follows the central pattern and the utility is available for subsequent cleanup.

Fifth, clarify and enforce the final-analysis failure contract. Final analysis is responsible for generating the final rules content, so errors should fail fast by default rather than return `"No final analysis generated"` as if a usable result existed. Revert `FinalAnalysis.run()` to re-raise after logging, update tests to expect the exception, and document that any future user-facing fallback belongs at the pipeline or CLI boundary where the operator can see that generation failed.

## Milestones

Milestone 1, `EP-20260505-001/MS001 Restore Claude Code Prompt Contract`, changes the SDK `system_prompt` payload from a replacement string to the Claude Code preset with AgentRules instructions appended. It ends when the request builder proves the payload preserves the preset and remains accepted by `ClaudeAgentOptions`.

Milestone 2, `EP-20260505-001/MS002 Add Runtime Execution Guardrails`, adds bounded execution settings and timeout behavior for SDK queries. It ends when requests include turn and optional budget limits, the client times out predictably, and tests cover both request construction and timeout mapping.

Milestone 3, `EP-20260505-001/MS003 Respect SDK CLI Resolution`, makes `cli_path` optional and removes provider gating that assumes a standalone `claude` executable is mandatory. It ends when default config omits `cli_path`, SDK options omit it by default, explicit bad paths are still reported, and CLI guidance distinguishes SDK runtime availability from OAuth setup commands.

Milestone 4, `EP-20260505-001/MS004 Centralize Provider Object Coercion`, introduces the shared provider coercion helper and routes Claude Code response parsing through it. It ends when response parser tests cover SDK dataclasses and plain object fixtures without a local `_to_dict`.

Milestone 5, `EP-20260505-001/MS005 Clarify Final Analysis Failure Contract`, restores fail-fast final analysis behavior and updates tests/documentation around that contract. It ends when final-analysis tests expect raised failures and broad phase validation still passes.

## Progress

- [x] (2026-05-05 America/New_York) Created this ExecPlan and five active milestones with `agentrules execplan new` and `agentrules execplan milestone new`.
- [x] (2026-05-05 America/New_York) Drafted remediation strategy for all five Claude Code runtime review findings.
- [x] (2026-05-05 America/New_York) Completed MS001: Claude Code requests now preserve the built-in Claude Code prompt preset and append AgentRules instructions; validation passed with focused tests, SDK import smoke, and ruff.
- [x] (2026-05-05 America/New_York) Completed MS002: Claude Code requests now include configurable turn and optional budget limits, and SDK query collection has an AgentRules timeout; validation passed with focused tests, live-smoke skip check, ruff, and pyright.
- [x] (2026-05-05 America/New_York) Completed MS003: default Claude Code runtime config now lets the SDK resolve its CLI path, while explicit configured paths are still validated; validation passed with config, CLI, model preset, request-builder, ruff, pyright, SDK import, and import-smoke checks.
- [x] (2026-05-05 America/New_York) Completed MS004: added shared `sdk_object_to_dict()` provider utility and moved Claude Code response parsing off its local `_to_dict`; validation passed with provider utility tests, response parser tests, ruff, pyright, and snapshot sync.
- [x] (2026-05-05 America/New_York) Completed MS005: final analysis now logs and re-raises failures so critical rules generation stops instead of returning placeholder content; validation passed with phase-edge, Claude Code architect, final-analysis, CLI boundary, broad unit/offline, ruff, pyright, and import-smoke checks.
- [x] Implementation complete.
- [x] Validation complete.

## Surprises & Discoveries

- Observation: The Claude Agent SDK prompt customization API has two materially different behaviors.
  Evidence: Internal docs state that a raw `system_prompt` string replaces Claude Code's default prompt, while the preset object with `append` preserves built-in Claude Code behavior and adds custom instructions.
- Observation: The current branch's focused Claude Code implementation is green, so remediation is hardening rather than rescue.
  Evidence: Review validation before this plan showed import smoke passing, focused Claude Code/config/Phase 3 tests passing, ruff passing, pyright reporting 0 errors, and live smoke skipped without opt-in env.
- Observation: The SDK's bundled binary behavior changes the meaning of runtime availability.
  Evidence: Internal docs state that the SDK bundles a native Claude Code binary as an optional dependency, while the current config service gates availability on resolving `claude` through `shutil.which` or an explicit executable path.

## Decision Log

- Decision: Keep Claude Code as a distinct runtime provider and harden its boundaries rather than folding it into `ModelProvider.ANTHROPIC`.
  Rationale: Claude Code uses a local SDK/CLI runtime and OAuth-oriented credentials, while the Anthropic provider is a direct API-key adapter. Keeping them separate preserves the architecture established by `EP-20260504-001`.
  Date/Author: 2026-05-05 / @codex
- Decision: Use the Claude Code system prompt preset with appended AgentRules instructions.
  Rationale: This preserves Claude Code's tool, safety, and environment guidance while still applying the repository's phase-specific behavior.
  Date/Author: 2026-05-05 / @codex
- Decision: Make execution bounds explicit and configurable at the runtime boundary.
  Rationale: Agentic SDK runs can perform multiple tool-use turns. A production provider should have deterministic ceilings for headless CLI and CI use.
  Date/Author: 2026-05-05 / @codex
- Decision: Treat the SDK default CLI path as valid runtime resolution.
  Rationale: Requiring a standalone `claude` executable contradicts the SDK's documented bundled-binary behavior and can incorrectly hide presets from valid installations.
  Date/Author: 2026-05-05 / @codex
- Decision: Restore fail-fast behavior for final analysis.
  Rationale: Final analysis produces the critical output content. Returning placeholder analysis on failure can mask broken generation and create misleading artifacts.
  Date/Author: 2026-05-05 / @codex

## Outcomes & Retrospective

Completed all five hardening milestones. Claude Code runtime requests now preserve the Claude Code prompt preset, run with explicit execution bounds, defer to SDK-default CLI resolution when no path is configured, use a shared SDK-object coercion helper in response parsing, and fail fast during final rules generation.

Validation completed across milestone-specific suites and the broad `tests/unit tests/offline` suite. Live Claude Code smoke remains opt-in and was not run live because it requires `AGENTRULES_RUN_CLAUDE_CODE_LIVE=1` and authenticated local runtime state.

Remaining follow-up is intentionally outside this ExecPlan: other provider adapters still have local object-coercion helpers that can be migrated to `sdk_object_to_dict()` in a separate, low-risk cleanup once covered by provider-specific tests.

## Concrete Steps

Work from the repository root:

    cd /Volumes/AGENAI/Coding/public-github/agentrules-architect

For each milestone, read the milestone file first, make the narrow implementation changes it describes, update that milestone's `Changelog`, and run the milestone-specific validation commands before moving to the next milestone. Keep `.agent/PLANS.md` rules in force and update this ExecPlan's `Progress`, `Surprises & Discoveries`, and `Decision Log` whenever implementation discoveries change the plan.

The full validation gate for the complete plan is:

    PYTHONPATH=src .venv/bin/python -c "import agentrules; import agentrules.core.agents.claude_code"
    PYTHONPATH=src .venv/bin/pytest tests/unit/agents/test_claude_code_request_builder.py tests/unit/agents/test_claude_code_response_parser.py tests/unit/agents/test_claude_code_architect.py tests/unit/test_config_service.py tests/unit/test_cli_claude_code_settings.py tests/unit/utils/test_provider_capabilities.py tests/unit/analysis/test_phase3_packing.py tests/unit/test_phases_edges.py
    PYTHONPATH=src .venv/bin/pytest --run-live tests/live/test_claude_code_live_smoke.py
    PYTHONPATH=src .venv/bin/pytest tests/unit tests/offline
    PYTHONPATH=src .venv/bin/ruff check .
    PYTHONPATH=src .venv/bin/pyright

The live smoke command should skip unless `AGENTRULES_RUN_CLAUDE_CODE_LIVE=1` is set. A skip without the opt-in env is acceptable for default validation. When live validation is intentionally enabled, a successful result must include a structured phase-style payload and no authentication error.
