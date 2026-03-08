---
id: EP-20260308-001/MS005
execplan_id: EP-20260308-001
ms: 5
title: "Finish CLI workflows, tests, and rollout validation"
status: planned
domain: cross-cutting
owner: "@codex"
created: 2026-03-08
updated: 2026-03-08
tags: [codex, cli, tests, docs]
risk: med
links:
  issue: ""
  docs: ".agent/exec_plans/active/codex-app-server-runtime/EP-20260308-001_codex-app-server-runtime.md"
  pr: ""
---

# Finish CLI workflows, tests, and rollout validation

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Close the implementation with coherent CLI workflows, durable documentation, and the full validation matrix needed to trust the new provider path. When this milestone is complete, a user can configure and use Codex end-to-end from AgentRules, and the repository has enough automated coverage to keep the integration stable.

## Definition of Done

- The settings menu cleanly separates API-key providers from the Codex runtime configuration flow.
- Researcher and phase-model selection text accurately reflects Codex availability and Tavily requirements.
- The test suite includes unit coverage, offline/fake integration coverage, and an optional live smoke for local verification.
- The implementation instructions for managed versus inherited `CODEX_HOME` are documented.
- Final validation commands are recorded in the milestone and pass locally before the milestone is archived.

## Scope

### In Scope
- Final settings/menu polish.
- Documentation and operator notes.
- Test-suite completion and any necessary fixture cleanup.
- Optional live smoke flow behind an explicit environment flag.

### Out of Scope
- New product features unrelated to Codex.
- Performance optimization beyond what is needed to make the rollout safe.

## Workstreams & Tasks

- [ ] UX polish: finish settings copy and menu integration.
- [ ] Docs: explain login flow, `CODEX_HOME` modes, and model-preset selection.
- [ ] Tests: add any missing unit/offline/live smoke coverage.
- [ ] Validation: run import smoke, ruff, pyright, targeted pytest, and the new smoke instructions.

## Risks & Mitigations

- Risk: the implementation works but the CLI still tells users to add Tavily or API keys for Codex paths.
  Mitigation: include explicit UX review and test assertions around settings copy.
- Risk: live Codex verification becomes required in CI and destabilizes the suite.
  Mitigation: gate live smoke behind a dedicated environment flag and keep the default CI path on fake/offline fixtures.

## Validation / QA Plan

- `PYTHONPATH=src python -c "import agentrules"`
- `ruff check src tests`
- `pyright`
- `PYTHONPATH=src pytest tests/unit tests/offline tests/phase_1_test tests/phase_3_test -q`
- Optional live smoke documented by the implementation, run only when its flag is set.

## Changelog

- 2026-03-08: Milestone created.
