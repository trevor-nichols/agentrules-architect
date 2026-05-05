---
id: EP-20260504-001/MS003
execplan_id: EP-20260504-001
ms: 3
title: Pipeline and Preset Integration
status: completed
domain: cross-cutting
owner: '@codex'
created: 2026-05-04
updated: '2026-05-04'
tags:
- pipeline
- presets
- provider-capabilities
risk: med
links:
  issue: ''
  docs: ''
  pr: ''
---

# Pipeline and Preset Integration

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Make the Claude Code runtime selectable and useful in the normal AgentRules pipeline. When this milestone is complete, model presets can target `ModelProvider.CLAUDE_CODE`, the architect factory returns `ClaudeCodeArchitect`, Phase 1 and Phase 3 understand that Claude Code is a repository-aware runtime, and model picker UI can present Claude Code options when the configured runtime is available.

## Definition of Done

- [x] `ArchitectFactory.create_architect()` returns `ClaudeCodeArchitect` for `ModelProvider.CLAUDE_CODE`.
- [x] `src/agentrules/core/types/models.py` exposes `create_claude_code_config()` for deriving runtime presets from Claude model configs.
- [x] `src/agentrules/config/agents.py` includes static Claude Code presets for the currently supported Claude models.
- [x] `src/agentrules/core/configuration/model_presets.py` exposes provider display text and selected-preset behavior for Claude Code.
- [x] `src/agentrules/core/utils/provider_capabilities.py` treats Claude Code as repository-aware and runtime-native for web search.
- [x] Phase 3 packing behavior avoids embedding full file contents for Claude Code, matching the Codex runtime pattern.
- [x] Model picker tests cover Claude Code availability, active selection labels, and researcher behavior without Tavily.

## Scope

### In Scope
- Add static Claude Code presets such as `claude-code-sonnet-4.6`, `claude-code-sonnet-4.6-reasoning-medium`, and any other variants already represented for the direct Anthropic provider.
- Reuse existing Claude model identifiers unless the Agent SDK requires aliases such as `sonnet`, `opus`, or `haiku`; document the chosen mapping in the plan and tests.
- Update capability helpers: `uses_repo_runtime()`, `uses_runtime_native_web_search()`, `requires_external_research_tool_loop()`, and `should_embed_phase3_file_contents()`.
- Update model picker helper functions and tests under `src/agentrules/cli/ui/settings/models/` and `tests/unit/test_cli_model_picker_ui.py`.
- Ensure researcher mode can use Claude Code native web search without requiring Tavily.

### Out of Scope
- Do not add live model catalog discovery unless the SDK or CLI exposes a stable low-cost model listing API.
- Do not remove or rename existing Anthropic presets.
- Do not change default phase presets to Claude Code in the first pass unless separately approved.
- Do not alter Codex preset behavior.

## Workstreams & Tasks

### Workstream A - Factory and Presets

| ID | Area | Description | Status |
|----|------|-------------|--------|
| A1 | Factory | Add lazy import branch for `ModelProvider.CLAUDE_CODE` in `src/agentrules/core/agents/factory/factory.py`. | completed |
| A2 | Types | Add `create_claude_code_config(base_config: ModelConfig) -> ModelConfig`. | completed |
| A3 | Presets | Add Claude Code runtime preset definitions derived from Claude presets. | completed |
| A4 | Display | Add provider display name, likely `Claude Code Runtime`. | completed as `Claude Code` |

### Workstream B - Runtime Capabilities

| ID | Area | Description | Status |
|----|------|-------------|--------|
| B1 | Repo Runtime | Update `uses_repo_runtime()` to return true for Codex and Claude Code. | completed |
| B2 | Research | Update `uses_runtime_native_web_search()` so Claude Code can satisfy researcher mode without Tavily. | completed |
| B3 | Packing | Confirm Phase 3 file content embedding follows `should_embed_phase3_file_contents()` and add regression coverage. | completed |
| B4 | Tests | Update provider capability tests and Phase 3 packing tests. | completed |

### Workstream C - CLI Model Picker

| ID | Area | Description | Status |
|----|------|-------------|--------|
| C1 | Availability | Include `claude_code` in provider availability maps and model picker filtering. | completed |
| C2 | Labels | Show selected Claude Code presets distinctly from direct Anthropic presets. | completed |
| C3 | Researcher | Update researcher status copy to mention Tavily or runtime-native providers where appropriate. | completed |
| C4 | Tests | Add model picker tests mirroring the Codex runtime preset coverage. | completed |

## Risks & Mitigations

- Risk: Reusing direct Anthropic model IDs may not match Claude Code SDK accepted model names.
  Mitigation: Validate model option names during adapter tests and document whether full IDs or aliases are used.
- Risk: Treating Claude Code as repository-aware changes Phase 3 prompt shape.
  Mitigation: Add focused tests that prove Phase 3 does not inline file contents for Claude Code and does still inline them for direct Anthropic.
- Risk: Researcher behavior could turn on without a working runtime.
  Mitigation: Gate preset visibility and researcher native-search status on provider availability, not just provider enum.

## Validation / QA Plan

- Ran `PYTHONPATH=src .venv/bin/python -c "import agentrules"` and observed exit code 0 with no output.
- Ran `PYTHONPATH=src .venv/bin/pytest tests/unit/agents/test_claude_code_architect.py tests/unit/utils/test_provider_capabilities.py tests/unit/analysis/test_phase3_packing.py tests/unit/test_model_overrides.py tests/unit/test_cli_model_picker_ui.py tests/unit/test_config_service.py` and observed 68 passed.
- Ran `PYTHONPATH=src .venv/bin/ruff check src/agentrules/config/agents.py src/agentrules/core/types/models.py src/agentrules/core/agents/factory/factory.py src/agentrules/core/utils/provider_capabilities.py src/agentrules/cli/ui/settings/models src/agentrules/cli/ui/styles.py tests/unit/agents/test_claude_code_architect.py tests/unit/utils/test_provider_capabilities.py tests/unit/analysis/test_phase3_packing.py tests/unit/test_model_overrides.py tests/unit/test_cli_model_picker_ui.py` and observed all checks passed.
- Ran `PYTHONPATH=src .venv/bin/pyright src/agentrules/config/agents.py src/agentrules/core/types/models.py src/agentrules/core/agents/factory/factory.py src/agentrules/core/utils/provider_capabilities.py src/agentrules/cli/ui/settings/models src/agentrules/cli/ui/styles.py tests/unit/agents/test_claude_code_architect.py tests/unit/utils/test_provider_capabilities.py tests/unit/analysis/test_phase3_packing.py tests/unit/test_model_overrides.py tests/unit/test_cli_model_picker_ui.py` and observed 0 errors, 0 warnings, 0 informations.
- Tests manually distinguish direct Anthropic presets from Claude Code runtime presets via provider display text and `[CC]` picker badges.

## Changelog

- 2026-05-04: Milestone created.
- 2026-05-04: Expanded milestone with factory, preset, capability, Phase 3, and model picker integration tasks.
- 2026-05-04: Completed MS003 implementation and validation. Claude Code is now factory-wired, selectable through static runtime presets, treated as repo-runtime/native-research capable, and covered in picker/Phase 3 tests.
