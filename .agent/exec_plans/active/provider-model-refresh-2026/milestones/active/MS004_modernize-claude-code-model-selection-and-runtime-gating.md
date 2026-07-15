---
id: EP-20260715-001/MS004
execplan_id: EP-20260715-001
ms: 4
title: "Modernize Claude Code model selection and runtime gating"
status: planned
domain: cross-cutting
owner: "@codex"
created: 2026-07-15
updated: 2026-07-15
tags: [claude-code, agent-sdk, runtime, models]
risk: high
links:
  issue: ""
  docs: "https://code.claude.com/docs/en/model-config"
  pr: ""
---

# Modernize Claude Code model selection and runtime gating

This milestone is a living document. Keep the YAML front matter accurate, update this file as work proceeds, and record material revisions in `Changelog`.

## Objective

Give Claude Code users an explicit choice between runtime-managed model movement and reproducible pinned model IDs, while ensuring AgentRules invokes a bundled runtime new enough to understand every exposed choice. Version detection must identify the executable actually used and must not fail open when a selected pinned model has a documented minimum.

## Definition of Done

- [ ] Existing pinned Claude Code presets remain available and pinned Sonnet 5 and Fable 5 presets are added only when their thinking policies are valid.
- [ ] Runtime-managed presets exist for the SDK/account default and the `best`, `sonnet`, `opus`, and `fable` aliases, with labels explaining that aliases can move.
- [ ] The runtime-default preset omits a model override rather than pinning a model accidentally; alias presets pass the intended alias.
- [ ] The locked Claude Agent SDK bundles a Claude Code executable at or above 2.1.197, verified by running that exact binary with `--version`.
- [ ] Full Fable 5 is gated at 2.1.170 and full Sonnet 5 at 2.1.197; alias gates reflect whether the alias itself exists rather than assuming which provider model it resolves to.
- [ ] Version probing uses a realistic bounded timeout, reports timeout/parse failures distinctly, and treats an unknown version as unsupported when the chosen model has a known minimum.
- [ ] CLI diagnostics show the resolved executable source, path, parsed version, and why a model is unavailable.
- [ ] Non-interactive/SDK Fable refusals are surfaced as errors and never assumed to have switched automatically to Opus.
- [ ] Focused Claude Code request, response, client, configuration, CLI, dependency, Ruff, Pyright, and gated live-smoke tests pass.

## Scope

### In Scope

- Update static Claude Code preset construction in `src/agentrules/config/agents.py` and runtime preset resolution in `src/agentrules/core/configuration/model_presets.py` as needed for aliases and a runtime-default sentinel.
- Update `src/agentrules/core/agents/claude_code/request_builder.py` to omit `options["model"]` for the runtime-default sentinel and to pass `best`, `sonnet`, `opus`, or `fable` for alias presets.
- Add pinned full-ID presets for `claude-sonnet-5` and `claude-fable-5`, deriving their reasoning/effort behavior from the final MS003 capability profiles.
- Update `src/agentrules/core/configuration/services/claude_code.py` with minimum versions, reliable probing, executable-source diagnostics, and fail-closed behavior for version-gated selections.
- Upgrade `claude-agent-sdk` in `pyproject.toml`/`uv.lock` to a release whose bundled CLI satisfies Sonnet 5. Verify the bundled binary, not just the Python package version.
- Update `docs/claude-code-runtime.md`, CLI configuration guidance, and tests to distinguish bundled runtime, explicit `cli_path`, and global PATH behavior.
- Extend response parsing/tests for a non-interactive Fable refusal if the SDK represents it differently from ordinary result errors.

### Out of Scope

- Implementing a Claude Code `model/list` protocol that the Agent SDK does not expose.
- Making runtime aliases the only choices or removing pinned model IDs.
- Forcing AgentRules to use the user's global `claude` when the supported SDK-bundled runtime is available. Users retain the explicit `cli_path` override.
- Changing OAuth/API-key authentication strategy, allowed tools, permission mode, turn limits, or budget controls.
- Assuming interactive Fable fallback behavior applies to headless SDK execution.

## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | Mixed | Runtime boundary is clean, but model choices are static and always explicit. |
| Runtime dependency | Stale | Locked SDK bundles Claude Code 2.1.161. |
| Version gating | Unsafe | Two-second probe returned unknown locally and unknown currently bypasses gates. |
| Tests & docs | Good foundation | Focused request/config/runtime tests and a gated live smoke already exist. |

## Architecture / Design Snapshot

Expose two selection modes rather than choosing automatic versus pinned globally. A runtime-default internal sentinel maps to an omitted SDK `model` option, allowing account and organization defaults to apply. The moving aliases are passed verbatim because Claude Code owns their provider-specific resolution. Full IDs continue to be passed verbatim and carry explicit minimum-version gates.

Do not gate `sonnet` as if it always means Sonnet 5: older providers and runtimes can resolve it to an older supported Sonnet. Gate the `fable` alias and `best` only at the version that introduced those concepts, while full `claude-sonnet-5` and `claude-fable-5` use their documented model minimums. Tests must cover alias and full-ID distinctions.

Executable resolution remains bundled-first unless the user configures `cli_path`, matching the SDK-oriented architecture. Diagnostics should return a structured source such as `configured`, `sdk_bundled`, or `path` alongside the path and parsed version. Increase the probe timeout to a bounded value supported by local evidence, such as ten seconds, catch known subprocess failures, and keep the result cached by executable path.

## Workstreams & Tasks

### Workstream A - Selection semantics

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| A1 | Default | Add a sentinel that omits the SDK model override. | Planned |
| A2 | Aliases | Add best/sonnet/opus/fable moving choices with clear labels. | Planned |
| A3 | Pinned | Add full Sonnet 5 and Fable 5 presets with capability-safe efforts. | Planned |
| A4 | Compatibility | Preserve all existing pinned preset keys. | Planned |

### Workstream B - Runtime and dependency gates

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| B1 | Dependency | Upgrade SDK and verify its exact bundled CLI version. | Planned |
| B2 | Probe | Replace the unreliable two-second fail-open behavior. | Planned |
| B3 | Versions | Add full-ID and alias-specific minimum rules. | Planned |
| B4 | Diagnostics | Report executable source/path/version and support reason. | Planned |

### Workstream C - Safety and evidence

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| C1 | Refusal | Surface non-interactive Fable refusal without assumed fallback. | Planned |
| C2 | Unit tests | Cover omitted default, aliases, pins, gates, and timeout paths. | Planned |
| C3 | Live smoke | Keep live execution opt-in and verify the resolved runtime in evidence. | Planned |
| C4 | Docs | Explain automatic movement, pinning, bundling, and overrides. | Planned |

## Dependencies

- MS003 defines the final Sonnet 5/Fable 5 capability semantics.
- `claude-agent-sdk` must publish a compatible package whose bundled executable meets the minimum. If not, the pinned new-model presets remain hidden and the blocker is recorded rather than bypassed.
- Existing `tests/live/test_claude_code_live_smoke.py` remains gated by its current environment controls.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Package version is upgraded but bundled CLI remains too old. | High | Execute the resolved bundled binary and assert the parsed version in tests/diagnostics. |
| Runtime default is accidentally sent as a literal model ID. | High | Use an internal sentinel and an exact request-builder assertion that `model` is absent. |
| Unknown version bypasses a minimum gate. | High | Return unsupported/diagnostic for version-gated choices when probe is unknown. |
| Alias movement surprises reproducibility-sensitive users. | Medium | Keep pinned choices and label moving aliases explicitly. |
| Fable refusal is incorrectly assumed to fall back in SDK mode. | Medium | Test the headless result/error contract and surface refusal without hidden switching. |
| Longer probe blocks startup excessively. | Low | Cache by executable path and retain a finite timeout. |

## Validation / QA Plan

Run from the repository root:

    .venv/bin/python -m pytest -q tests/unit/agents/test_claude_code_request_builder.py tests/unit/agents/test_claude_code_response_parser.py tests/unit/agents/test_claude_code_client.py tests/unit/agents/test_claude_code_architect.py tests/unit/test_cli_claude_code_settings.py tests/unit/test_model_overrides.py
    .venv/bin/python -m pytest -q tests/live/test_claude_code_live_smoke.py
    .venv/bin/ruff check src/agentrules/core/agents/claude_code src/agentrules/core/configuration/services/claude_code.py src/agentrules/core/configuration/model_presets.py src/agentrules/config/agents.py tests/unit/agents/test_claude_code_request_builder.py tests/unit/agents/test_claude_code_response_parser.py tests/unit/agents/test_claude_code_client.py tests/unit/test_cli_claude_code_settings.py
    .venv/bin/pyright src/agentrules/core/agents/claude_code src/agentrules/core/configuration/services/claude_code.py src/agentrules/core/configuration/model_presets.py src/agentrules/config/agents.py tests/unit/agents/test_claude_code_request_builder.py tests/unit/agents/test_claude_code_response_parser.py tests/unit/agents/test_claude_code_client.py tests/unit/test_cli_claude_code_settings.py
    .venv/bin/python -c "import agentrules"

Also run a read-only diagnostic that prints the resolved executable source, path, and version. Green means the path is the same path AgentRules sends to the SDK, the version is at least 2.1.197, the runtime-default request omits `model`, aliases remain aliases, pins remain pins, and the live test skips without opt-in.

## Rollout / Ops Notes

Alias presets are opt-in and may change model, price, or availability as Claude Code and the user's provider evolve. Pinned presets are the reproducible path. The upgraded bundled runtime becomes the default because the integration already prefers it; release notes must mention the version change. Rollback must restore the prior SDK and hide any pinned choices its bundled CLI cannot select. Explicit `cli_path` remains the operator escape hatch and must be validated rather than silently ignored.

## Changelog

- 2026-07-15 — Created milestone scaffold.
- 2026-07-15 — Added the dual alias/pin model strategy, bundled-runtime dependency gate, reliable version probing, refusal behavior, and verification plan.
