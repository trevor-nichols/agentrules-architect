---
id: EP-20260301-001
title: "Snapshot artifact generation and comment-preserving sync"
status: done
kind: feature
domain: backend
owner: "@codex"
created: 2026-03-01
updated: 2026-03-01
tags: [snapshot, cli, outputs]
touches: [cli, docs, tests]
risk: med
breaking: false
migration: false
links:
  issue: ""
  pr: ""
  docs: ""
depends_on: []
supersedes: []
---

# EP-20260301-001 - Snapshot artifact generation and comment-preserving sync

This ExecPlan is a living document. Keep `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` up to date as work proceeds.

If `.agent/PLANS.md` exists in this repository, maintain this plan in accordance with that guidance.

## Purpose / Big Picture

Users can now generate and maintain a `SNAPSHOT.md` artifact inside the existing analysis workflow, and keep inline tree comments stable across filesystem changes. This allows teams to curate project-structure annotations manually while still refreshing the tree and file payloads from current source state.

Behavior is visible in two ways:
1. Running `agentrules analyze` with snapshot output enabled writes/syncs the snapshot artifact.
2. Running `agentrules snapshot sync` updates only the snapshot artifact (with optional dry-run preview).

## Scope

In scope:
- Output preferences for snapshot generation + configurable filename.
- Snapshot artifact writer with:
  - `<project_structure>` output,
  - optional `<file path="...">` payload blocks,
  - comment-preserving tree sync logic.
- Atomic writes for snapshot persistence.
- CLI command group for direct snapshot syncing.
- Unit and CLI test coverage.

Out of scope:
- AI-generated tree comments.
- Snapshot import/diff tooling.

## Progress

- [x] (2026-03-01) Created ExecPlan and registry entry.
- [x] (2026-03-01) Added snapshot output preferences and config serialization wiring.
- [x] (2026-03-01) Implemented snapshot artifact generator with comment-preserving sync.
- [x] (2026-03-01) Integrated snapshot artifact generation into pipeline output writer.
- [x] (2026-03-01) Added `snapshot sync` CLI command.
- [x] (2026-03-01) Added tests for snapshot writer, pipeline integration, config, and CLI.
- [x] (2026-03-01) Ran targeted validation suite successfully.

## Surprises & Discoveries

- Existing tree generation and file retrieval logic already exposed enough primitives to avoid introducing a parallel snapshot discovery stack.
  - Evidence: `get_project_tree` + `list_files`/`read_file_with_fallback` were sufficient for deterministic snapshot materialization.

## Decision Log

- Decision: Preserve inline comments by stable relative path instead of line-number position.
  Rationale: Path-based mapping survives insertions/removals/reordering and avoids comment drift.
  Date/Author: 2026-03-01 / @codex

- Decision: Include a direct `snapshot sync` CLI path in addition to pipeline integration.
  Rationale: Snapshot refresh should not require a full multi-phase analysis run.
  Date/Author: 2026-03-01 / @codex

- Decision: Make snapshot generation opt-in by default.
  Rationale: Snapshot artifacts can be large; default-off avoids unexpected repository churn.
  Date/Author: 2026-03-01 / @codex

## Outcomes & Retrospective

Completed outcomes:
- Added output preferences: `generate_snapshot` and `snapshot_filename`.
- Added new artifact modules:
  - `core/utils/file_creation/atomic_write.py`
  - `core/utils/file_creation/snapshot_artifact.py`
- Added CLI command group:
  - `agentrules snapshot sync`
- Integrated snapshot generation into pipeline persistence.
- Added focused test coverage for the new behavior.

Validation executed:
- `PYTHONPATH=src .venv/bin/python -m pytest -q tests/unit/test_snapshot_artifact.py tests/unit/test_pipeline_output_writer.py tests/test_cli_services.py tests/unit/test_config_service.py tests/unit/test_cli.py`
- `PYTHONPATH=src .venv/bin/python -m compileall -q src/agentrules tests/unit/test_snapshot_artifact.py`

Follow-up candidates:
- Add optional AI-assisted comment generation pass.
- Add import/diff workflows against snapshot artifacts if needed.
