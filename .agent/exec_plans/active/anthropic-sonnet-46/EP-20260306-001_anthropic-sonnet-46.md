---
id: EP-20260306-001
title: "Add Claude Sonnet 4.6 with extensible Anthropic capability metadata"
status: done
kind: refactor
domain: backend
owner: "@codex"
created: 2026-03-06
updated: 2026-03-06
tags: [anthropic, models, capabilities]
touches: [agents, tests]
risk: low
breaking: false
migration: false
links:
  issue: ""
  pr: ""
  docs: "https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-6"
depends_on: []
supersedes: []
---

# EP-20260306-001 - Add Claude Sonnet 4.6 with extensible Anthropic capability metadata

This ExecPlan is a living document. Keep `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` up to date as work proceeds.

If `.agent/PLANS.md` exists in this repository, maintain this plan in accordance with that guidance.

## Purpose / Big Picture

Users need to select Anthropic's new `claude-sonnet-4-6` model in the app with provider behavior that matches current Claude 4.6 documentation. That means the model must appear in the preset registry, support adaptive thinking plus `effort` levels that Anthropic documents for Sonnet 4.6, and reject unsupported combinations such as `effort="max"`.

The user-visible proof is straightforward: the CLI model picker exposes Claude Sonnet 4.6 options, Anthropic request-building tests show adaptive thinking and allowed effort levels for Sonnet 4.6, and unsupported combinations fail with clear errors.

## Scope

In scope:
- Add `claude-sonnet-4-6` model configs and Anthropic presets.
- Refactor Anthropic capability checks from ad hoc allowlists into a central family capability registry.
- Update request-builder validation and tests to reflect Sonnet 4.6 support for adaptive thinking, `low|medium|high` effort, and structured output mode.

Out of scope:
- Changing default phase model selections.
- Adding any other Anthropic model families not requested here.
- Reworking provider API transport behavior beyond capability validation and preset exposure.

## Progress

- [x] (2026-03-06) Created ExecPlan for the Sonnet 4.6 model-add plus capability refactor.
- [x] (2026-03-06) Replace Anthropic capability allowlists with family metadata resolution.
- [x] (2026-03-06) Add Claude Sonnet 4.6 model configs and presets.
- [x] (2026-03-06) Add and update tests for adaptive thinking, effort validation, and preset exposure.
- [x] (2026-03-06) Run targeted pytest, ruff, pyright, and import-smoke verification.

## Surprises & Discoveries

- Anthropic capability helpers already anticipated structured output support for Sonnet 4.6, but adaptive thinking and `effort` validation were still hard-coded to Opus-only families.
  - Evidence: `src/agentrules/core/agents/anthropic/capabilities.py` included Sonnet 4.6 in `supports_structured_output_format()` but not in `supports_adaptive_thinking()` or `supports_effort()`.

## Decision Log

- Decision: Represent Anthropic family features as centralized metadata instead of extending conditional logic.
  Rationale: New Claude families are arriving with overlapping but non-identical capability sets, so a profile registry is easier to audit and extend than scattered string-prefix checks.
  Date/Author: 2026-03-06 / @codex

- Decision: Model Sonnet 4.6 reasoning presets around adaptive thinking with explicit `low`, `medium`, and `high` effort levels, with no `max` preset.
  Rationale: Anthropic's 4.6 documentation recommends adaptive thinking for Sonnet 4.6 and limits `max` effort to Opus 4.6.
  Date/Author: 2026-03-06 / @codex

## Outcomes & Retrospective

Completed outcomes:
- Added a central Anthropic capability profile registry in `src/agentrules/core/agents/anthropic/capabilities.py`.
- Added `claude-sonnet-4-6` model configs and app presets with adaptive-thinking `low`, `medium`, and `high` effort variants.
- Updated Anthropic request validation to derive adaptive-thinking and effort support from capability metadata instead of provider-specific string branches.
- Added coverage for capability resolution, request-building semantics, Anthropic preset exposure, and broader Anthropic provider compatibility.
- Refreshed `.agent/exec_plans/registry.json` so the new plan is discoverable through repo tooling.

Validation executed:
- `PYTHONPATH=src pytest tests/unit/agents/test_anthropic_capabilities.py tests/unit/agents/test_anthropic_request_builder.py tests/unit/test_model_overrides.py`
- `PYTHONPATH=src pytest tests/unit/agents/test_anthropic_capabilities.py tests/unit/agents/test_anthropic_request_builder.py tests/unit/agents/test_anthropic_client_compat.py tests/unit/agents/test_anthropic_agent_parsing.py tests/unit/test_agents_anthropic_parse.py`
- `ruff check src/agentrules/core/agents/anthropic/capabilities.py src/agentrules/core/agents/anthropic/request_builder.py src/agentrules/core/types/models.py src/agentrules/config/agents.py tests/unit/agents/test_anthropic_capabilities.py tests/unit/agents/test_anthropic_request_builder.py tests/unit/test_model_overrides.py .agent/exec_plans/active/anthropic-sonnet-46/EP-20260306-001_anthropic-sonnet-46.md`
- `pyright src/agentrules/core/agents/anthropic/capabilities.py src/agentrules/core/agents/anthropic/request_builder.py src/agentrules/core/types/models.py src/agentrules/config/agents.py tests/unit/agents/test_anthropic_capabilities.py tests/unit/agents/test_anthropic_request_builder.py tests/unit/test_model_overrides.py`
- `PYTHONPATH=src python -c "import agentrules"`
