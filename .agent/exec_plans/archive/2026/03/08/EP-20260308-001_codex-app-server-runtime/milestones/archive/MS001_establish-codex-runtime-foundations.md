---
id: EP-20260308-001/MS001
execplan_id: EP-20260308-001
ms: 1
title: "Establish Codex runtime foundations"
status: done
domain: cross-cutting
owner: "@codex"
created: 2026-03-08
updated: 2026-03-08
tags: [codex, config, presets]
risk: med
links:
  issue: ""
  docs: ".agent/exec_plans/active/codex-app-server-runtime/EP-20260308-001_codex-app-server-runtime.md"
  pr: ""
---

# Establish Codex runtime foundations

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Introduce the new Codex provider identity, the derived `codex-*` preset family, and the AgentRules configuration primitives required to locate a Codex installation and resolve the effective `CODEX_HOME`. When this milestone is complete, Codex is a first-class selectable runtime in configuration and preset logic even though no live app-server requests have been wired yet.

## Definition of Done

- `ModelProvider.CODEX` exists and is handled by shared preset/model metadata helpers.
- `src/agentrules/config/agents.py` exposes stable `codex-*` preset keys derived from existing model constants instead of duplicating model strings.
- `CLIConfig` persists a dedicated `codex` section with runtime location and `CODEX_HOME` strategy data.
- Config manager and CLI service helpers can read and write Codex runtime settings.
- Provider availability checks can report Codex readiness without depending on API-key environment variables.
- Targeted unit tests for config serde and preset availability pass.

## Scope

### In Scope
- Add provider enum, config dataclasses, serde support, and config-manager methods.
- Add preset derivation helpers and Codex preset registrations.
- Generalize provider-availability logic away from an API-key-only assumption.
- Add a minimal settings entry point for Codex runtime configuration persistence.

### Out of Scope
- Launching `codex app-server`.
- Login, logout, or model catalog RPCs.
- Any phase execution changes.

## Workstreams & Tasks

- [x] Provider model: added `ModelProvider.CODEX`, model-config derivation helpers, structured-output metadata support, and derived `codex-*` preset registrations.
- [x] Config model: added a dedicated `codex` config section, serde wiring, config-manager accessors, environment application for managed `CODEX_HOME`, and CLI service helpers.
- [x] Availability policy: replaced API-key-only preset gating with provider-aware runtime checks that can later grow into stronger Codex probes.
- [x] Settings stub: added the `Codex runtime` menu entry and persistence flow for executable path and `CODEX_HOME` strategy.
- [x] Tests: added unit coverage for Codex config persistence, runtime availability, preset visibility, and structured-output metadata.

## Risks & Mitigations

- Risk: Codex configuration leaks into the API-key provider store and creates permanent special cases.
  Mitigation: use a dedicated config section and dedicated settings flow from the start.
- Risk: Preset duplication drifts from the existing GPT-5 model constants.
  Mitigation: derive Codex presets from existing `ModelConfig` constants rather than copying raw model names.

## Validation / QA Plan

- `PYTHONPATH=src python -c "import agentrules"`
- `PYTHONPATH=src pytest tests/unit -q`
- `ruff check src tests`
- Confirm the persisted config file contains a `codex` section and does not misuse `providers.<name>.api_key`.

## Changelog

- 2026-03-08: Milestone created.
- 2026-03-08: Implemented the Codex provider/configuration foundation, added the Codex runtime settings flow, and validated with import smoke, targeted tests, `pytest tests/unit -q`, `ruff check src tests`, and `pyright`.
