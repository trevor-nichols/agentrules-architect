---
id: EP-20260505-001/MS005
execplan_id: EP-20260505-001
ms: 5
title: "Clarify Final Analysis Failure Contract"
status: planned
domain: backend
owner: "@codex"
created: 2026-05-05
updated: 2026-05-05
tags: [final-analysis, fail-fast, pipeline-contract]
risk: med
links:
  issue: ""
  docs: ""
  pr: ""
---

# Clarify Final Analysis Failure Contract

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Restore a clear fail-fast contract for final analysis. At the end of this milestone, final analysis failures are logged and raised instead of being converted into placeholder rules content, and tests document where any user-facing error handling belongs.

## Definition of Done

- [ ] `src/agentrules/core/analysis/final_analysis.py` re-raises exceptions after logging, matching the Phase 5 fail-fast pattern.
- [ ] Tests that previously expected an error payload are updated to expect a raised exception.
- [ ] Any CLI or pipeline-level tests that rely on top-level error reporting still pass.
- [ ] The ExecPlan and milestone changelog explain why placeholder final analysis output is not acceptable for critical artifact generation.
- [ ] Broad phase-edge tests and offline tests pass.

## Scope

### In Scope
- Revert or adjust the changed catch block in `FinalAnalysis.run()`.
- Update `tests/unit/test_phases_edges.py` around final-analysis error behavior.
- Inspect `src/agentrules/cli/services/pipeline_runner.py` to ensure top-level exceptions are still presented clearly to the user.
- If documentation mentions final-analysis fallback behavior, update it to say failures stop generation.

### Out of Scope
- Do not redesign the entire pipeline error model.
- Do not add a best-effort AGENTS.md writer when final analysis fails.
- Do not hide provider errors under generic "No final analysis generated" messages.

## Workstreams & Tasks

- [ ] Contract: decide and document that final analysis is a critical generation phase and must fail fast.
- [ ] Implementation: change the exception handler back to `raise` after logging.
- [ ] Tests: update the final-analysis failure-path test to use `pytest.raises(RuntimeError, match="boom")` or the exact propagated exception.
- [ ] Regression: run Phase 5 and final-analysis edge tests together to confirm consistent behavior.

## Risks & Mitigations

- Risk: Existing tests may have encoded the placeholder-output behavior because it made failures easier to assert.
  Mitigation: Update tests to assert the intended contract directly. If a user-facing graceful message is required, add it at the CLI boundary where the run can terminate visibly.
- Risk: Re-raising can stop an otherwise partially successful analysis run.
  Mitigation: This is intentional for final artifact quality. A generated rules file based on placeholder final analysis is more dangerous than a failed run.

## Validation / QA Plan

- Run `PYTHONPATH=src .venv/bin/pytest tests/unit/test_phases_edges.py tests/unit/agents/test_claude_code_architect.py`.
- Run `PYTHONPATH=src .venv/bin/pytest tests/unit tests/offline`.
- Run `PYTHONPATH=src .venv/bin/ruff check src/agentrules/core/analysis/final_analysis.py tests/unit/test_phases_edges.py`.
- Green means final-analysis failures raise, CLI/pipeline tests still cover top-level reporting, and no placeholder final rules content is returned on provider failure.

## Changelog

- 2026-05-05: Milestone created.
- 2026-05-05: Drafted fail-fast final-analysis contract scope from Claude Code runtime review finding 5.
