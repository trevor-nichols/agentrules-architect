---
id: EP-20260308-001/MS004
execplan_id: EP-20260308-001
ms: 4
title: "Apply phase-specific Codex pipeline exceptions"
status: completed
domain: cross-cutting
owner: "@codex"
created: 2026-03-08
updated: 2026-03-08
tags: [codex, phase1, phase3]
risk: med
links:
  issue: ""
  docs: ".agent/exec_plans/active/codex-app-server-runtime/EP-20260308-001_codex-app-server-runtime.md"
  pr: ""
---

# Apply phase-specific Codex pipeline exceptions

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Teach AgentRules to use Codex as a repository-aware coding runtime instead of a prompt-only model. When this milestone is complete, Phase 3 will stop embedding full file contents for Codex providers, and the Phase 1 researcher can run through Codex without requiring Tavily credentials or external tool-loop plumbing.

## Definition of Done

- Phase 3 skips file-content loading and token packing when the assigned provider is Codex.
- A Codex-specific phase-3 prompt path references file assignments and the repository tree instead of embedding source bodies.
- Researcher enablement no longer depends on Tavily credentials when the selected researcher preset resolves to Codex.
- Phase 1 researcher bypasses the Tavily tool loop for Codex and accepts direct findings from the runtime.
- Provider-aware branching is centralized in reusable helpers instead of scattered ad hoc conditionals.
- Tests prove the Codex path does not call the file-content loader or Tavily execution path unnecessarily.

## Scope

### In Scope
- Phase 1 researcher guard changes.
- Phase 3 prompt/context changes.
- Provider capability helpers used by phase logic.
- Regression tests around phase behavior.

### Out of Scope
- General refactors unrelated to Codex behavior.
- Changing non-Codex providers' prompt strategies.

## Workstreams & Tasks

- [x] Phase 3: add a Codex-specific prompt builder and bypass file embedding/token packing.
- [x] Phase 1: make researcher enablement and execution provider-aware.
- [x] Shared helpers: centralize capability checks such as "uses repo runtime" or "needs external research tool loop".
- [x] Tests: cover no-file-embedding behavior and no-Tavily-required researcher behavior.

## Risks & Mitigations

- Risk: Codex-specific behavior leaks into all providers and makes the phase code harder to follow.
  Mitigation: centralize the branching behind small capability helpers and separate prompt builders.
- Risk: removing file embedding from Phase 3 drops important context for Codex.
  Mitigation: include explicit file assignment lists, tree context, prior batch summaries, and `cwd` grounding in the Codex prompt path.

## Validation / QA Plan

- `PYTHONPATH=src pytest tests/phase_1_test tests/phase_3_test tests/unit -q`
- `ruff check src tests`
- Manual check: run a Codex-backed phase on a small repository and confirm the prompt path references files instead of embedding them.

## Changelog

- 2026-03-08: Milestone created.
- 2026-03-08: Completed provider-aware Codex runtime branching for Phase 1 and Phase 3, added shared capability helpers, and validated the new behavior with targeted plus milestone-level test runs.
