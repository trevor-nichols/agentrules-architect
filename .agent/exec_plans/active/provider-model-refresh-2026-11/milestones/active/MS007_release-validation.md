---
id: EP-20261127-001/MS007
execplan_id: EP-20261127-001
ms: 7
title: "Validate the release and document rollout and recovery"
status: planned
domain: cross-cutting
owner: "@codex"
created: 2026-11-27
updated: 2026-11-27
tags: []
risk: med
links:
  issue: ""
  docs: ""
  pr: ""
---

# Validate the release and document rollout and recovery

This milestone is a living document. Keep the YAML front matter accurate and log material changes in Changelog.

## Objective

Prove the compatibility fixes and the new provider choices work on a clean install before release. Record the merge order and a retry or rollback path that preserves compatibility after each cutover.

## Definition of Done

- Python 3.11 locked install, import smoke, full offline suite, Ruff, Pyright, lock validation, and PR CI pass.
- The release includes the October provider refresh and every due retirement route. Supported live checks report observed results, while skipped ones are identified.
- Lifecycle, provider runtime, and repository guidance reflect shipped changes. Release notes identify changed saved-model behavior and dependency floors. Milestones and registry agree.

## Scope

Run end-to-end offline and focused package checks, verify merge ancestry and release contents, update operator-facing docs, and complete the ExecPlan after the acceptance criteria are satisfied. Credentialed smokes and comparative model evaluations remain opt-in. Existing phase defaults stay in place.

## Current Health Snapshot

The October provider branch includes the CI workflow and compatibility fixtures and is the dependency of this branch. The November work was prepared as a separate stack and is awaiting implementation approval. The planning baseline passed 1,160 tests and 57 subtests on locked Python 3.11.18. An earlier local run reported two width-sensitive picker assertions. Recheck the baseline after integrating the target branch.

## Architecture / Design Snapshot

Validate through the public CLI/settings path, provider request adapters, and the offline analysis pipeline. Use mock SDK transports and fake app-server executables for deterministic evidence. Record lifecycle decisions in the centralized resolver rather than altering stored profiles directly.

## Workstreams & Tasks

1. Verify the actual integration base before release. If the October refresh lands as a squash, verify its capability code, key mappings, lockfile, and CI contents on the target branch and rebase or retarget the November changes while preserving their milestone boundaries. Keep the independent ExecPlan directory change out of the implementation diff. If the chosen target already uses the new layout, follow the target CLI and update plan paths, links, and registry accordingly.
2. Recheck primary provider lifecycle dates and record the tested before-and-after transitions. Confirm the first compatibility slice can ship independently. If provider review or account access delays a model, hold that new preset on its own without delaying an already-required retirement route.
3. Inspect the new lock on a clean install. Check managed and custom runtime behavior, existing saved-config reloads, refusal and settings messages, the parser corpus, and a complete fake pipeline. Apply the applicable parts of `AGENTS.md` where long-lived repo conventions change. Update the snapshots for any file moves or additions.
4. Record offline results and each live smoke's opt-in or skipped status. If an operator enables live inference, test only the provider and model requested, using the project's existing flags. Use representative repository evaluations for any future default proposal.
5. Inspect the registry after milestone completion and close this ExecPlan only after the acceptance criteria are met. Prepare review or release material with the changed requirements and rollback sequence. Let existing release automation own version bumps.

## Dependencies

MS001 through MS006 for the full release. MS001 can ship independently on top of the October changes. CI uses `.github/workflows/test.yml` and `.github/workflows/validate-uv-lock.yml`.

## Risks & Mitigations

A clean branch can still miss its base dependency if the stacked PR is retargeted incorrectly. Verify merged contents and lockfile on the actual integration base. App-level fallback can silently undo a deadline fix if SDK or picker work gets rolled back. Separate the compatibility slice and record provider-level reversions. A synthetic fixture proves request behavior and local wiring. Track account access, quota, and production behavior separately.

## Validation / QA Plan

From the repository root, run these checks under a fresh locked development environment.

    uv lock --check --python 3.11
    uv sync --locked --extra dev --python 3.11
    uv run --python 3.11 --no-sync python -c 'import agentrules; print(agentrules.__file__)'
    uv run --python 3.11 --no-sync ruff check .
    uv run --python 3.11 --no-sync pyright
    uv run --python 3.11 --no-sync pytest -q tests --ignore=tests/live
    agentrules execplan-registry check
    git diff --check

Confirm the PR workflow's import, prompt template, parser corpus, token-packer regression, offline pipeline, quality, and lock checks. Inspect model selection with examples from each changed provider. Run separately permitted live commands with the flags documented in `docs/provider-model-lifecycle.md`, `docs/claude-code-runtime.md`, and `docs/codex-runtime.md`. Record command, selected model, outcomes, and skip reasons without retaining credentials or raw transcripts.

## Rollout / Ops Notes

Publish compatibility routes with the October dependency available. Roll out each model or SDK slice with its matching capability tests and docs. If a dependency bump must be reverted, restore its previous lock and remove the corresponding new feature exposure while keeping compatible saved-key redirects. After each provider cutover, keep routes to current endpoints in the release branch. Refresh the registry after moving the final milestone and plan.

## Changelog

- 2026-11-27 — Documented release, rollback, and live validation boundaries.
