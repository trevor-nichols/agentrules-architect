---
id: EP-20260313-001
title: Phase 1 Project Profile and Specialized Agent Contracts
status: archived
kind: feature
domain: backend
owner: '@codex'
created: 2026-03-13
updated: '2026-03-13'
tags:
- phase1
- profiling
- agents
touches:
- agents
- cli
- tests
- docs
risk: med
breaking: false
migration: false
links:
  issue: ''
  pr: ''
  docs: ''
depends_on: []
supersedes: []
---

# EP-20260313-001 - Phase 1 Project Profile and Specialized Agent Contracts

This ExecPlan is a living document. Keep `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` up to date as work proceeds.

If `.agent/PLANS.md` exists in this repository, maintain this plan in accordance with that guidance.

## Purpose / Big Picture

Phase 1 currently provides generic discovery context (tree + dependency manifests) and a fixed set of agents. After this change, Phase 1 will also produce a concrete `project_profile` describing ecosystem and architecture signals, and will dynamically add specialized discovery agents when a frontend-design or Python-tooling surface is detected.

User-visible outcome: running the pipeline against different repositories should produce Phase 1 results that include a stable profile schema and specialized findings for detected project types, without changing behavior for repositories that do not match those profiles.

## Context and Orientation

Relevant runtime flow:

- `src/agentrules/cli/services/pipeline_runner.py` builds `PipelineSettings` and starts the pipeline.
- `src/agentrules/core/pipeline/snapshot.py` currently builds the tree and dependency summary used by Phase 1.
- `src/agentrules/core/analysis/phase_1.py` defines Phase 1 agent construction and context payloads.
- `src/agentrules/config/prompts/phase_1_prompts.py` defines existing agent prompt contracts.
- `src/agentrules/core/utils/dependency_scanner/*` provides dependency manifests and parsed manifest metadata.

Current baseline:

- Phase 1 has fixed agents (`Dependency`, optional `Researcher`, `Structure`, `Tech Stack`).
- Phase 1 contexts do not include a normalized project-type profile.
- Specialized UI/design vs Python tooling discovery must be inferred indirectly today.

## Concrete `project_profile` Schema

`project_profile` is a JSON-serializable dict attached to `ProjectSnapshot` and propagated into Phase 1 output. The schema is deterministic and additive.

Required top-level keys:

- `schema_version: str` (fixed value `"1.0"`)
- `detected_types: list[str]`
- `ecosystem: dict`
- `frontend: dict`
- `python: dict`
- `signals: dict`

Detailed shape:

- `schema_version`: `"1.0"`
- `detected_types`: ordered unique values from:
  - `"frontend-web"`
  - `"frontend-nextjs"`
  - `"python"`
  - `"polyglot"`
  - `"generic"` (fallback)
- `ecosystem`:
  - `dependency_managers: list[str]` (from dependency summary keys)
  - `manifest_types: list[str]` (from manifest records)
  - `manifest_paths: list[str]` (repo-relative)
- `frontend`:
  - `detected: bool`
  - `frameworks: list[str]` (e.g. `nextjs`, `react`)
  - `styling_systems: list[str]` (e.g. `tailwindcss`, `css`, `sass`, `less`, `styled-components`, `emotion`)
  - `signal_files: list[str]` (e.g. `next.config.ts`, `tailwind.config.js`, `postcss.config.js`)
  - `style_file_count: int` (`.css/.scss/.sass/.less/.styl` count)
- `python`:
  - `detected: bool`
  - `managers: list[str]` (subset of dependency managers indicating Python ecosystem)
  - `packaging_files: list[str]` (e.g. `pyproject.toml`, `requirements*.txt`, `Pipfile`, `setup.py`, `setup.cfg`)
  - `task_runner_files: list[str]` (`Makefile`, `justfile`, `Justfile`)
  - `tooling_files: list[str]` (`tox.ini`, `noxfile.py`)
- `signals`:
  - `tree_max_depth: int`
  - `files_scanned: int`

## New Phase 1 Specialized Agent Contracts

Two conditional agents are introduced and only run when their corresponding profile slice is detected.

1. Frontend Design Agent

- Name: `Frontend Design Agent`
- Trigger: `project_profile.frontend.detected == true`
- Role: identify style-system architecture and design surface signals.
- Responsibilities:
  - Identify primary styling approach (Tailwind, CSS modules/global CSS, CSS-in-JS).
  - Identify where design tokens/variants likely live from config and file layout.
  - Summarize frontend architecture patterns relevant to onboarding (app router, components, design-system placement).
  - Call out uncertainty explicitly when style evidence is incomplete.
- Context keys:
  - `project_profile`
  - `frontend_profile` (project_profile.frontend)
  - `tree_structure`
  - `dependency_summary`
  - `dependency_findings`
  - `research_findings`

2. Python Tooling Agent

- Name: `Python Tooling Agent`
- Trigger: `project_profile.python.detected == true`
- Role: identify packaging/runtime/tooling surface for Python projects.
- Responsibilities:
  - Summarize packaging/build conventions (pyproject/setup/requirements).
  - Identify task orchestration entry points (Makefile/justfile/tox/nox).
  - Capture likely local developer workflow commands from tooling surface.
  - Flag mixed packaging conventions that may confuse onboarding.
- Context keys:
  - `project_profile`
  - `python_profile` (project_profile.python)
  - `tree_structure`
  - `dependency_summary`
  - `dependency_findings`
  - `research_findings`

## Milestone Plan

MS001 - Project profile detection and snapshot wiring

- Add `project_profile` builder and wire it into `ProjectSnapshot`.
- Ensure profile generation respects existing exclusion/gitignore settings.
- Add targeted unit tests for profile detection behavior.

MS002 - Phase 1 specialized agent contracts and gating

- Add new prompt contracts and phase logic for conditional specialized agents.
- Propagate `project_profile` through Phase 1 contexts and output.
- Add unit tests for gating and context payload correctness.

MS003 - Integration polish docs and regression coverage

- Update structured schemas/tests and docs for the new Phase 1 output field.
- Extend pipeline/snapshot tests and run broader validation suites.
- Sync architectural snapshot docs when file structure changes.

## Progress

- [x] (2026-03-13 16:06Z) Created ExecPlan and milestones using CLI workflows.
- [x] (2026-03-13 16:06Z) Defined concrete `project_profile` schema and Phase 1 specialized agent contracts.
- [x] (2026-03-13 16:15Z) Implemented MS001 project profile detector and snapshot wiring with new unit coverage (`tests/unit/test_project_profile.py`).
- [x] (2026-03-13 16:15Z) Validated MS001 via `ruff check src/agentrules/core/pipeline tests/unit/test_pipeline_snapshot.py tests/unit/test_project_profile.py` and `pytest -q tests/unit/test_pipeline_snapshot.py tests/unit/test_project_profile.py`.
- [x] (2026-03-13 16:21Z) Archived MS001 and committed snapshot/profile foundation (`feat(pipeline): add project profile snapshot foundation`).
- [x] (2026-03-13 16:28Z) Implemented MS002 specialized agent prompts + Phase 1 routing and added `tests/phase_1_test/test_phase1_profile_agents.py`.
- [x] (2026-03-13 16:28Z) Validated MS002 via `ruff check ...` and `pytest -q tests/phase_1_test tests/unit/utils/test_structured_outputs.py`.
- [x] (2026-03-13 16:31Z) Archived MS002 and committed specialized-agent integration (`feat(phase1): add profile-gated specialized discovery agents`).
- [x] (2026-03-13 16:38Z) Implemented MS003 integration polish (docs, contract assertions, orchestrator regression coverage, snapshot sync).
- [x] (2026-03-13 16:38Z) Validated MS003 via `ruff check src tests` and targeted 45-test regression suite.
- [x] (2026-03-13 16:42Z) Archived MS003 and committed integration polish (`test(pipeline): add profile propagation regression coverage`).
- [x] (2026-03-13 16:43Z) Prepared final retrospective and archived ExecPlan.

## Surprises & Discoveries

- Observation: `agentrules execplan new` in this repo does not accept `--ms`; deterministic milestone numbering is handled on `agentrules execplan milestone new`.
  Evidence: CLI help output and successful milestone creation with `--ms` flags.
- Observation: Adding `project_profile` to `ProjectSnapshot` can be made backward-compatible for existing tests by using a dataclass default rather than forcing every fixture constructor to change immediately.
  Evidence: `ProjectSnapshot.project_profile` uses `field(default_factory=dict)` and existing unit fixtures still construct valid snapshots.
- Observation: Specialized Phase 1 agents can be added without polluting constructor state by building them per-run from profile-gated prompt contracts.
  Evidence: `_run_specialized_profile_agents()` in `phase_1.py` creates optional agents only when `get_specialized_phase1_agent_prompts()` returns configs.
- Observation: Snapshot sync should be part of milestones that add or move plan/code files; otherwise architectural inventory drifts quickly.
  Evidence: Running `agentrules snapshot sync` updated `SNAPSHOT.md` with 5 path changes after this feature.

## Decision Log

- Decision: Keep project profile generation deterministic and rule-based (no model calls) using existing tree/dependency snapshots.
  Rationale: Fast, testable, provider-independent behavior that is safe to use as routing input.
  Date/Author: 2026-03-13 / @codex
- Decision: Introduce specialized discovery as optional additional Phase 1 agents rather than replacing existing core agents.
  Rationale: Preserves baseline behavior and minimizes regression risk while allowing targeted depth.
  Date/Author: 2026-03-13 / @codex
- Decision: Build profile signal scanning from existing `list_files` with the current exclusion/gitignore pipeline settings, not custom directory traversal.
  Rationale: Keeps profile detection behavior aligned with existing tree/dependency discovery and avoids duplicate exclusion logic.
  Date/Author: 2026-03-13 / @codex
- Decision: Keep specialized Phase 1 agent gating declarative in `phase_1_prompts.py` via `profile_key` metadata and `get_specialized_phase1_agent_prompts()`.
  Rationale: Centralized prompt contracts reduce branching logic in `Phase1Analysis` and make future agent additions low risk.
  Date/Author: 2026-03-13 / @codex
- Decision: Add an orchestrator regression test to assert `project_profile` propagation into Phase 1 invocation.
  Rationale: This edge is easy to regress during pipeline refactors and directly impacts specialized-agent execution correctness.
  Date/Author: 2026-03-13 / @codex

## Outcomes & Retrospective

Completed outcomes:

- Added deterministic `project_profile` construction in snapshot pipeline with explicit frontend/python/ecosystem signal schema.
- Propagated `project_profile` through orchestrator into Phase 1 execution context and output payload.
- Added profile-gated specialized Phase 1 contracts (`Frontend Design Agent`, `Python Tooling Agent`) while preserving baseline behavior for generic repositories.
- Updated contract docs/schema references and added regression tests covering:
  - profile detector behavior
  - snapshot wiring
  - specialized agent gating
  - orchestrator profile propagation
  - structured Phase 1 schema contract

Validation summary (all green):

- `ruff check src/agentrules/core/pipeline tests/unit/test_pipeline_snapshot.py tests/unit/test_project_profile.py`
- `pytest -q tests/unit/test_pipeline_snapshot.py tests/unit/test_project_profile.py`
- `ruff check src/agentrules/config/prompts/phase_1_prompts.py src/agentrules/core/analysis/phase_1.py src/agentrules/core/pipeline/orchestrator.py src/agentrules/core/utils/structured_outputs.py tests/phase_1_test/test_phase1_profile_agents.py tests/phase_1_test/test_phase1_researcher_guards.py tests/phase_1_test/test_phase1_offline.py`
- `pytest -q tests/phase_1_test tests/unit/utils/test_structured_outputs.py`
- `ruff check src tests`
- `pytest -q tests/unit/test_pipeline_snapshot.py tests/unit/test_project_profile.py tests/unit/test_pipeline_orchestrator.py tests/phase_1_test tests/unit/utils/test_structured_outputs.py tests/unit/test_pipeline_output_writer.py`

Remaining gap:

- Profile detection is intentionally rule-based and conservative; expanding ecosystem-specific heuristics can be handled in a follow-up ExecPlan.
