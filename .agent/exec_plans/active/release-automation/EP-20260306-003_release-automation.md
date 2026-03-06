---
id: EP-20260306-003
title: "Add tag-driven GitHub release automation"
status: done
kind: infra
domain: infra
owner: "@codex"
created: 2026-03-06
updated: 2026-03-06
tags: [github, releases, ci]
touches: [ops, docs, tests]
risk: low
breaking: false
migration: false
links:
  issue: ""
  pr: ""
  docs: ""
depends_on: []
supersedes: []
---

# EP-20260306-003 - Add tag-driven GitHub release automation

This ExecPlan is a living document. Keep `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` up to date as work proceeds.

If `.agent/PLANS.md` exists in this repository, maintain this plan in accordance with that guidance.

## Purpose / Big Picture

This change gives the repository a predictable way to publish GitHub Releases without manually editing the release entry in the GitHub UI. After the change, maintainers will bump the package version in `pyproject.toml`, create a matching `vX.Y.Z` tag, and push that tag. GitHub Actions will validate that the tag matches the package version on that exact commit and then create or update the GitHub Release automatically.

The visible outcome is a new `.github/workflows/release.yml` workflow plus a small Python validation module that fails fast on mismatched tags. This prevents the current drift pattern where GitHub tags can point at commits whose package version does not match the release tag.

## Progress

- [x] (2026-03-06) Confirmed the repository currently has no `.github/workflows` directory on local or remote-tracking branches.
- [x] (2026-03-06) Confirmed the current release process is manual and that remote tags are not consistently version-synced.
- [x] (2026-03-06) Implemented a tag-driven workflow that creates GitHub Releases from pushed `vX.Y.Z` tags.
- [x] (2026-03-06) Added a reusable validator that enforces `pyproject.toml` version and tag parity.
- [x] (2026-03-06) Documented the release flow and ran local validation for the helper and registry updates.

## Surprises & Discoveries

- Observation: The repo has no existing GitHub Actions workflow files at all, so release automation can be added without needing to preserve an existing CI convention.
  Evidence: `git ls-tree --name-only -r origin/main | rg '^(\\.github/|pyproject.toml$)'` returned only `pyproject.toml`.

- Observation: The current remote tags already show version drift, which means validation should be part of the release flow rather than optional documentation.
  Evidence: `refs/tags/v3.2.3` points to commit `c425ac7`, while `origin/main:pyproject.toml` reports version `3.2.3` and `git show v3.2.3:pyproject.toml` reports `3.2.2`.

## Decision Log

- Decision: Use a tag-driven release workflow instead of a version-bump-on-main workflow.
  Rationale: It keeps repository mutation explicit, avoids CI creating commits or tags, and matches how this repository is already being versioned manually.
  Date/Author: 2026-03-06 / @codex

- Decision: Put tag/version validation in a Python module instead of inline shell in the workflow.
  Rationale: The repository already has Python-based validation habits, and a module is easier to test and maintain than shell parsing inside YAML.
  Date/Author: 2026-03-06 / @codex

## Outcomes & Retrospective

Completed outcomes:

- Added `.github/workflows/release.yml` to publish GitHub Releases from pushed stable tags.
- Added `src/agentrules/core/utils/release_metadata.py` so tag/version validation is centralized, testable, and reusable from CI.
- Added `tests/unit/test_release_metadata.py` to cover stable version parsing, tag mismatch failures, and GitHub output emission.
- Updated `README.md` with the maintainer-facing release flow so the intended process is documented in-repo.

Validation executed:

- `PYTHONPATH=src python -m pytest tests/unit/test_release_metadata.py`
- `PYTHONPATH=src python -m agentrules.core.utils.release_metadata --tag v3.2.3`
- `ruff check src/agentrules/core/utils/release_metadata.py tests/unit/test_release_metadata.py README.md .agent/exec_plans/active/release-automation/EP-20260306-003_release-automation.md`
- `pyright src/agentrules/core/utils/release_metadata.py tests/unit/test_release_metadata.py`
- YAML structure validation for `.github/workflows/release.yml` using `yaml.BaseLoader`
- `PYTHONPATH=src python -m agentrules execplan-registry update`
- `PYTHONPATH=src python -m agentrules execplan-registry check`

## Context and Orientation

This repository keeps its package version in `pyproject.toml` under `[project].version`. There is currently no `.github/workflows/` directory in the tree, so GitHub Releases are not being created by repository-managed automation. Remote tags exist, but they are not guarded by any version parity check.

The implementation should touch four areas:

- `.github/workflows/release.yml` for GitHub Actions release automation.
- `src/agentrules/core/utils/release_metadata.py` for version/tag validation logic that can run in CI and be unit tested.
- `tests/unit/test_release_metadata.py` for validator coverage.
- `README.md` for a short maintainer-facing release workflow note.

The workflow must be safe and auditable. It should only react to pushed tags matching the repository's stable release naming pattern (`vX.Y.Z`). It must fail if the tag does not match the `pyproject.toml` version on the tagged commit. It should use GitHub's built-in release notes generation rather than custom templating so the release body stays low maintenance.

## Implementation Plan

Create the GitHub Actions directory and add a single release workflow. Trigger it on pushes to tags that look like stable semantic versions. Set `permissions.contents` to `write`, because the workflow needs permission to create or update Releases.

Add a small Python module that reads `pyproject.toml` using `tomllib`, validates the project version format, validates the pushed tag format, and writes outputs in the format GitHub Actions expects when a `--github-output` path is provided. Keep the validation strict: only `X.Y.Z` versions are accepted for this automated flow.

Update the README's development section with the exact maintainer workflow: bump version, commit, tag the same version, push the tag. Keep the wording brief and operational.

## Validation

Run the new unit test module for release metadata. Run the validator against the current repository version using the matching tag. Run `ruff check` and `pyright` against the new module and tests. After creating the ExecPlan, update and check the execplan registry so the plan is discoverable.
