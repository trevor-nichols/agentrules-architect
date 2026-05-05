---
id: EP-20260504-001/MS002
execplan_id: EP-20260504-001
ms: 2
title: "Claude Agent SDK Adapter"
status: planned
domain: backend
owner: "@codex"
created: 2026-05-04
updated: 2026-05-04
tags: [claude-code, agent-sdk, provider-adapter]
risk: med
links:
  issue: ""
  docs: "internal-docs/integrations/anthropic/agents-sdk/python-sdk.md"
  pr: ""
---

# Claude Agent SDK Adapter

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Implement the provider adapter that translates AgentRules analysis requests into Claude Agent SDK `query()` calls and translates SDK messages back into AgentRules result dictionaries. When this milestone is complete, the adapter is testable with fake SDK messages and supports text findings, structured output, basic tool-call accounting, usage metadata, and actionable error handling without requiring a live Claude Code installation in unit tests.

## Definition of Done

- [ ] `pyproject.toml` declares the Claude Agent SDK dependency using the confirmed package name.
- [ ] `src/agentrules/core/agents/claude_code/` exists with `architect.py`, `client.py`, `errors.py`, `request_builder.py`, `response_parser.py`, and `__init__.py`.
- [ ] `ClaudeCodeArchitect` implements `BaseArchitect` methods consistently with `CodexArchitect` and existing phase-specific helpers.
- [ ] The request builder maps model, system prompt, prompt text, cwd, cli path, OAuth-sanitized env, permissions, thinking/effort, and structured output schema into SDK options.
- [ ] The response parser handles assistant text blocks, result messages, final `structured_output`, tool-use blocks, usage, and SDK error subtypes.
- [ ] Unit tests use fakes/mocks and do not require the real SDK to contact Claude.
- [ ] `python -c "import agentrules"` passes after dependency and import changes.

## Scope

### In Scope
- Add a lazy SDK client boundary in `src/agentrules/core/agents/claude_code/client.py`. This module should be the only place that imports `claude_agent_sdk` at runtime.
- Add typed internal request and response dataclasses where useful, following the Codex `PreparedRequest` and `ParsedResponse` style.
- Add `ClaudeCodeArchitect.analyze()`, `create_analysis_plan()`, `synthesize_findings()`, `consolidate_results()`, and `final_analysis()`.
- Add `ClaudeCodeArchitect.stream_analyze()` if the SDK's `include_partial_messages` can be exercised cleanly with fakes. If streaming is deferred, document the deferral in the milestone changelog and ensure `supports_streaming` stays false.
- Extend `src/agentrules/core/utils/structured_outputs.py` with provider metadata and schema mode for Claude Code.
- Add tests under `tests/unit/agents/` for request building, response parsing, architect phase helpers, and structured output failure behavior.

### Out of Scope
- Do not add interactive settings UI in this milestone.
- Do not add model picker integration in this milestone.
- Do not add a live smoke test in this milestone.
- Do not implement a custom SDK transport unless `query()` cannot support required behavior.

## Workstreams & Tasks

### Workstream A - SDK Dependency and Client Boundary

| ID | Area | Description | Status |
|----|------|-------------|--------|
| A1 | Dependency | Confirm the package import and dependency name, expected to be `claude-agent-sdk` and `claude_agent_sdk`. | planned |
| A2 | Client | Implement a small `execute_query()` async wrapper around SDK `query(prompt=..., options=...)`. | planned |
| A3 | Errors | Define `ClaudeCodeRuntimeError`, `ClaudeCodeExecutableNotFoundError`, and `ClaudeCodeSDKError` or equivalent wrappers. | planned |
| A4 | Tests | Mock the client boundary rather than mocking deep SDK internals in architect tests. | planned |

### Workstream B - Request Construction

| ID | Area | Description | Status |
|----|------|-------------|--------|
| B1 | Options | Build `ClaudeAgentOptions` with `model`, `cwd`, `cli_path`, `system_prompt`, `env`, `permission_mode`, `allowed_tools`, `disallowed_tools`, and `output_format`. | planned |
| B2 | OAuth | Ensure request env is produced by the configuration service and strips `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` when configured. | planned |
| B3 | Tools | Default to read-oriented Claude Code tools for analysis: `Read`, `Glob`, `Grep`, and optionally `WebSearch` for researcher flows. | planned |
| B4 | Structured | Reuse existing AgentRules JSON schema builders for phase output schemas. | planned |

### Workstream C - Response Parsing and Architect Behavior

| ID | Area | Description | Status |
|----|------|-------------|--------|
| C1 | Parser | Collect assistant text from SDK content blocks and final result messages. | planned |
| C2 | Structured | Prefer `ResultMessage.structured_output` when present and return it under `structured_output`. | planned |
| C3 | Tool Calls | Record SDK tool-use blocks as serializable dicts without executing AgentRules-side tools. | planned |
| C4 | Phase Helpers | Mirror Codex phase helpers so Phase 2 agents can be extracted from structured payloads. | planned |
| C5 | Token Logging | Use `estimate_tokens()` with an appropriate estimator family and log preflight details. | planned |

## Risks & Mitigations

- Risk: The installed SDK type names or option names may differ slightly from the docs.
  Mitigation: Keep all SDK construction inside one request builder/client boundary and validate against the installed package before broad wiring.
- Risk: Claude Code may attempt interactive permissions during headless AgentRules runs.
  Mitigation: Use `permission_mode="dontAsk"` with explicit read-tool allow rules and write/shell deny rules by default.
- Risk: Structured outputs may arrive only on the final result message and not in streaming events.
  Mitigation: Parse structured output from the final result and treat streaming structured output as out of scope unless the SDK supports it cleanly.
- Risk: Lazy imports can mask dependency issues until runtime.
  Mitigation: Runtime errors must clearly name the missing package and the install command; import smoke must still pass.

## Validation / QA Plan

- Run `python -c "import agentrules"` and expect success even before a live Claude Code login exists.
- Run `pytest tests/unit/agents/test_claude_code_request_builder.py tests/unit/agents/test_claude_code_response_parser.py tests/unit/agents/test_claude_code_architect.py`.
- Run `pytest tests/unit/utils/test_structured_outputs.py` after adding Claude Code structured output metadata.
- Add fake SDK message fixtures covering: plain assistant text, final structured output, tool-use block, SDK process error, and structured-output retry failure subtype.

## Changelog

- 2026-05-04: Milestone created.
- 2026-05-04: Expanded milestone with SDK adapter boundaries, request/response mapping, risks, and tests.
