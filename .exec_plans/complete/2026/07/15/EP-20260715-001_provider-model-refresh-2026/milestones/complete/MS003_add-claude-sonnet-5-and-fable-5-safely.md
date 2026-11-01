---
id: EP-20260715-001/MS003
execplan_id: EP-20260715-001
ms: 3
title: Add Claude Sonnet 5 and Fable 5 safely
status: completed
domain: backend
owner: '@codex'
created: 2026-07-15
updated: '2026-07-15'
tags:
- anthropic
- sonnet-5
- fable-5
- safety
risk: high
links:
  issue: ''
  docs: https://platform.claude.com/docs/en/about-claude/models/overview
  pr: ''
---

# Add Claude Sonnet 5 and Fable 5 safely

This milestone is a living document. Keep the YAML front matter accurate, update this file as work proceeds, and record material revisions in `Changelog`.

## Objective

Add direct Anthropic API support for Claude Sonnet 5 and Claude Fable 5 without representing unsupported thinking modes or treating a classifier refusal as a successful empty response. The finished direct provider must encode each family's thinking policy, effort range, structured-output support, context window, and operational retention limits in one auditable capability profile.

## Definition of Done

- [x] `claude-sonnet-5` and `claude-fable-5` have canonical model configs and presets with 1,000,000-token context metadata.
- [x] Sonnet 5 uses adaptive thinking when enabled/dynamic and sends an explicit disabled-thinking payload when `ReasoningMode.DISABLED` is selected.
- [x] Fable 5 always uses adaptive thinking; no disabled-thinking preset exists, and a programmatic disabled configuration fails before network I/O with an actionable message.
- [x] Sonnet 5 and Fable 5 expose only their documented effort values through `max`, and neither sends a fixed manual `budget_tokens` payload.
- [x] Both families participate in Anthropic structured JSON output where the existing phase schema system requests it.
- [x] A response with `stop_reason="refusal"` becomes an explicit error result or typed error path, including a safe stop-detail summary when available, rather than `findings=None` success.
- [x] Generic Claude Opus presets stop selecting Opus 4.1 before its 2026-08-05 retirement and resolve to Opus 4.8; compatibility is covered by tests and descriptions.
- [x] Fable's 30-day retention and zero-data-retention incompatibility are documented for operators.
- [x] Focused Anthropic, structured-output, model-override, import, Ruff, and Pyright validation passes.

## Scope

### In Scope

- Add Sonnet 5 and Fable 5 configs to `src/agentrules/core/types/models.py` and presets to `src/agentrules/config/agents.py`.
- Evolve `CapabilityProfile` in `src/agentrules/core/agents/anthropic/capabilities.py` to represent default thinking behavior and whether thinking can be disabled, in addition to the existing adaptive/manual/effort/structured fields.
- Update `anthropic/request_builder.py` so omission versus explicit `thinking.type="disabled"` is chosen from capability metadata, not only `ReasoningMode`.
- Add adaptive-effort presets for Sonnet 5 and Fable 5. Fable may expose low, medium, high, xhigh, and max; Sonnet may expose the same documented range plus an explicitly non-thinking preset. Keep the set intentionally consistent with the CLI's existing preset style.
- Add refusal-aware parsing for standard responses and the final state of streaming responses where the SDK exposes stop metadata. Use duck-typed access for `stop_details` if the installed SDK model does not type it yet.
- Update the generic `claude-opus` and `claude-opus-reasoning` keys to use Opus 4.8 semantics. Do not leave an apparently current generic key on a retiring model.
- Add documentation under the existing provider/runtime docs or a concise new provider-model lifecycle section.

### Out of Scope

- Invitation-only Claude Mythos models.
- Automatic direct-API fallback from Fable to Opus after a refusal. AgentRules should surface the refusal explicitly; automatic model switching changes cost and behavior and requires a separate product decision.
- Claude Code runtime aliases or SDK upgrades, which are MS004.
- New Anthropic beta features, fast mode, priority tier, or task budgets.
- Exposing hidden chain-of-thought or storing refusal classifier internals.

## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | Good foundation | Capability profiles already centralize newer Claude family differences. |
| Implementation | Complete | Sonnet 5 and Fable 5 use explicit capability policies and valid preset sets. |
| Safety handling | Complete | Standard and streaming refusal metadata reaches a typed error boundary. |
| Lifecycle | Current | Generic Opus now resolves to Opus 4.8, and Fable retention limits are documented. |

## Architecture / Design Snapshot

Replace ambiguous thinking booleans with an explicit policy. A practical representation is a small provider-local enum or literal with three states: legacy/manual-or-omitted, adaptive-with-explicit-disable, and always-adaptive. Keep `supports_manual_thinking` only if older callers need it, but derive behavior from one coherent profile rather than contradictory flags.

For an adaptive-with-explicit-disable family, `DYNAMIC` and `ENABLED` both send `{"type": "adaptive"}`, while `DISABLED` sends `{"type": "disabled"}`. For always-adaptive Fable, `DYNAMIC` and `ENABLED` omit `thinking` because the provider documents omission as the canonical always-adaptive request shape, while `DISABLED` raises `ValueError` before dispatch. Older Claude families retain their proven wire shapes.

Add a provider-specific refusal error type if that keeps parsing and orchestration clean. The parser should inspect top-level `stop_reason` before returning `ParsedResponse`. The existing architect may convert the typed exception to its normal `{"agent": ..., "error": ...}` result boundary, but it must never report an empty successful finding. Streaming must inspect the SDK's final message/event and raise the same semantic error when possible.

## Workstreams & Tasks

### Workstream A - Capability and preset model

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| A1 | Models | Add Sonnet 5 and Fable 5 configs and exact 1M limits. | Complete |
| A2 | Capabilities | Encode adaptive default, disable support, efforts, and structured output. | Complete |
| A3 | Presets | Add valid variants and deliberately omit Fable non-thinking. | Complete |
| A4 | Lifecycle | Move generic Opus keys to Opus 4.8 and update labels. | Complete |

### Workstream B - Request and response safety

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| B1 | Request | Emit adaptive or explicit disabled thinking from policy. | Complete |
| B2 | Validation | Reject Fable disabled and all unsupported effort combinations. | Complete |
| B3 | Parsing | Detect refusal stop reasons and safe detail fields. | Complete |
| B4 | Streaming | Prevent streaming refusals from appearing as successful completion. | Complete |

### Workstream C - Evidence and guidance

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| C1 | Unit tests | Cover every new thinking, effort, refusal, and structured path. | Complete |
| C2 | Regression | Prove older Claude family payloads remain stable. | Complete |
| C3 | Docs | Record retention, ZDR, model choice, and Opus migration. | Complete |
| C4 | Quality | Run focused pytest, Ruff, Pyright, and import smoke. | Complete |

## Dependencies

- MS001 and MS002 should be complete first so shared reasoning and dependency changes are known.
- The Anthropic SDK lock must expose `stop_reason`; `stop_details` may be read defensively if its typed surface lags the API. Upgrade only when necessary and regenerate `uv.lock` through `uv lock`.
- Claude Code work in MS004 consumes the final capability decisions but must not make direct Anthropic support depend on a local runtime.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Omitting thinking on Sonnet 5 unintentionally enables adaptive reasoning. | High | Send explicit disabled thinking and assert exact payloads. |
| A Fable “disabled” preset silently reasons anyway. | High | Do not create the preset; reject programmatic misuse before dispatch. |
| HTTP-200 refusal is treated as empty successful output. | High | Inspect stop metadata first and test dict and SDK-object responses. |
| Refusal details leak sensitive classifier internals. | Medium | Include only provider-supplied safe summary fields and never hidden reasoning. |
| Generic Opus key behavior changes unexpectedly. | Medium | Preserve the key, disclose the replacement, and test that it resolves to Opus 4.8. |
| Capability refactor changes older Claude payloads. | Medium | Add table-driven regression tests for Sonnet 4.5/4.6, Haiku 4.5, and Opus 4.6/4.7/4.8. |

## Validation / QA Plan

Run from the repository root:

    .venv/bin/python -m pytest -q tests/unit/agents/test_anthropic_capabilities.py tests/unit/agents/test_anthropic_request_builder.py tests/unit/agents/test_anthropic_agent_parsing.py tests/unit/agents/test_anthropic_client_compat.py tests/unit/test_model_overrides.py
    .venv/bin/python -m pytest -q tests/unit/agents/test_claude_code_request_builder.py
    .venv/bin/ruff check src/agentrules/core/types/models.py src/agentrules/config/agents.py src/agentrules/core/agents/anthropic tests/unit/agents/test_anthropic_capabilities.py tests/unit/agents/test_anthropic_request_builder.py tests/unit/agents/test_anthropic_agent_parsing.py tests/unit/agents/test_anthropic_client_compat.py tests/unit/test_model_overrides.py
    .venv/bin/pyright src/agentrules/core/types/models.py src/agentrules/config/agents.py src/agentrules/core/agents/anthropic tests/unit/agents/test_anthropic_capabilities.py tests/unit/agents/test_anthropic_request_builder.py tests/unit/agents/test_anthropic_agent_parsing.py tests/unit/agents/test_anthropic_client_compat.py tests/unit/test_model_overrides.py
    .venv/bin/python -c "import agentrules"

Green means request tests prove adaptive, explicit disabled, fixed-budget rejection, supported efforts, structured output, and preflight Fable rejection; parser tests prove refusal handling for object and dict fixtures; and all older-family regressions pass. Optional live requests remain explicitly gated and Fable availability failures under ZDR are reported as expected availability constraints.

Validation evidence recorded on 2026-07-15:

- Focused Anthropic, structured-output, model-override, context-limit, and Claude Code regression suite: `163 passed in 1.52s`.
- Repository-wide pytest: `773 passed, 7 skipped, 31 subtests passed in 7.77s`; the four warnings are pre-existing `pathspec` deprecations.
- Repository-wide Ruff: `All checks passed!`.
- Repository-wide Pyright: `0 errors, 0 warnings, 0 informations`.
- Import smoke exited zero.
- Exact request tests cover Sonnet explicit disable, adaptive efforts through max, Fable thinking omission and disabled-mode rejection, older Claude payloads, structured output, and both object and dictionary refusal metadata.

## Rollout / Ops Notes

The direct model additions are additive. The generic Opus key advances in place to avoid retirement failure. Operators must be told that Fable can incur adaptive-thinking cost on every request, is not compatible with ZDR, and may refuse safety-classified work without automatic fallback in this direct API path. Rollback may restore the old generic Opus mapping only before August 5; afterward fix forward to an active Opus model.

## Changelog

- 2026-07-15 — Created milestone scaffold.
- 2026-07-15 — Added direct Claude 5 capability policy, refusal contract, Opus retirement migration, retention guidance, and verification criteria.
- 2026-07-15 — Marked the milestone in progress after MS002 was validated, archived, and committed.
- 2026-07-15 — Updated the Fable request design to omit `thinking` for normal requests after official guidance confirmed omission is the canonical always-adaptive wire shape; disabled thinking remains a preflight error.
- 2026-07-15 — Added Sonnet 5 and Fable 5 configs, capability-driven thinking policies, supported effort presets, exact context metadata, refusal handling, Opus 4.8 migration, and operator lifecycle guidance.
- 2026-07-15 — Completed focused and repository-wide validation and marked the milestone complete for archival.
