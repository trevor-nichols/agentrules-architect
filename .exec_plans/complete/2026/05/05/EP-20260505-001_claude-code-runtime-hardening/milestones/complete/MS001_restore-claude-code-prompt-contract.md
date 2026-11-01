---
id: EP-20260505-001/MS001
execplan_id: EP-20260505-001
ms: 1
title: Restore Claude Code Prompt Contract
status: completed
domain: backend
owner: '@codex'
created: 2026-05-05
updated: '2026-05-05'
tags:
- claude-code
- prompt-contract
- agent-sdk
risk: med
links:
  issue: ''
  docs: internal-docs/integrations/anthropic/agents-sdk/modify-system-prompt.md
  pr: ''
---

# Restore Claude Code Prompt Contract

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Restore the Claude Code prompt contract so AgentRules augments Claude Code instead of replacing it. At the end of this milestone, Claude Code runtime requests preserve Claude Code's built-in system prompt, tool instructions, safety guidance, and environment context while appending the resolved AgentRules phase instructions.

## Definition of Done

- [x] `src/agentrules/core/agents/claude_code/request_builder.py` builds `system_prompt` as a Claude Code preset object with `append` rather than a raw replacement string.
- [x] The request builder keeps the resolved AgentRules system prompt request-scoped and does not write it to Claude Code filesystem settings.
- [x] Unit tests verify the exact `system_prompt` payload and prove `ClaudeAgentOptions(**options)` accepts it.
- [x] Operator docs mention that AgentRules appends to the Claude Code preset rather than replacing it.
- [x] Focused Claude Code request-builder and architect tests pass.

## Scope

### In Scope
- Update `prepare_request()` in `src/agentrules/core/agents/claude_code/request_builder.py`.
- Add a small helper such as `_build_system_prompt_option(system_prompt: str) -> dict[str, object]` to make the SDK contract visible and testable.
- Use the SDK shape `{"type": "preset", "preset": "claude_code", "append": system_prompt, "exclude_dynamic_sections": True}` unless direct validation against the installed SDK shows that `exclude_dynamic_sections` is not accepted. The installed SDK version in the current lockfile is expected to support it.
- Update `tests/unit/agents/test_claude_code_request_builder.py` to assert the preset shape.
- Update `docs/claude-code-runtime.md` if it currently implies complete system prompt replacement.

### Out of Scope
- Do not add CLAUDE.md, `.claude/settings.json`, output styles, or any persistent Claude Code prompt files.
- Do not switch to `ClaudeSDKClient`; the provider still uses one-shot `query()` for this plan.
- Do not change prompts for the direct Anthropic API provider.

## Workstreams & Tasks

- [x] Request payload: replace the raw string assignment at `options["system_prompt"]` with the Claude Code preset object.
- [x] Tests: update the existing request-builder test that currently expects `prepared.options["system_prompt"] == "Keep responses concise."` so it expects the preset object and appended text.
- [x] SDK compatibility: add a test or assertion helper that imports `ClaudeAgentOptions` and constructs it with the prepared options without contacting the network.
- [x] Documentation: adjust runtime docs to describe "append to Claude Code preset" in plain terms.

## Risks & Mitigations

- Risk: The SDK may reject `exclude_dynamic_sections` on older versions.
  Mitigation: Validate with the installed `claude-agent-sdk` in a unit test. If it fails, keep the preset object and omit only that optional field while documenting the version behavior.
- Risk: Appending AgentRules instructions could reduce instruction priority compared with full replacement.
  Mitigation: The SDK docs identify the preset-with-append path as the way to preserve built-in functionality. Keep the appended text concise and phase-specific.

## Validation / QA Plan

- Run `PYTHONPATH=src .venv/bin/pytest tests/unit/agents/test_claude_code_request_builder.py tests/unit/agents/test_claude_code_architect.py`.
- Run `PYTHONPATH=src .venv/bin/python -c "from claude_agent_sdk import ClaudeAgentOptions; from agentrules.core.agents.claude_code.request_builder import prepare_request; print('ok')"` to smoke importability of the SDK and request builder.
- Run `PYTHONPATH=src .venv/bin/ruff check src/agentrules/core/agents/claude_code tests/unit/agents/test_claude_code_request_builder.py`.
- Green means tests pass and prepared options contain a `system_prompt` mapping with `type="preset"`, `preset="claude_code"`, and `append` equal to the resolved AgentRules system prompt.

## Changelog

- 2026-05-05: Milestone created.
- 2026-05-05: Drafted implementation scope and validation plan from Claude Code runtime review finding 1.
- 2026-05-05: Implemented preset-with-append system prompt payload, SDK compatibility assertion, and runtime documentation update. Validation passed with request-builder/architect tests, SDK import smoke, and ruff.
