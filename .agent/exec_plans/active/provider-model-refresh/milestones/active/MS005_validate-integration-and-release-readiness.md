---
id: EP-20260829-001/MS005
execplan_id: EP-20260829-001
ms: 5
title: "Validate Integration and Release Readiness"
status: planned
domain: cross-cutting
owner: "@codex"
created: 2026-08-29
updated: 2026-08-29
tags: [providers, validation, documentation, release]
risk: med
links:
  issue: ""
  docs: ""
  pr: ""
---

# Validate Integration and Release Readiness

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Integrate the provider slices into one release-ready, auditable change. The lifecycle guide, picker experience, compatibility registry, offline test suite, lint, type checks, import smoke, ExecPlan registry, and final diff must agree with the approved plan. This milestone produces the evidence needed for review; it does not broaden scope or use paid APIs by default.

## Definition of Done

- [ ] Anthropic, Gemini, xAI, DeepSeek, OpenAI lifecycle, and Codex runtime targeted suites all pass together.
- [ ] Full `ruff`, `pyright`, `pytest`, and import-smoke gates pass.
- [ ] `docs/provider-model-lifecycle.md` matches shipped keys, constraints, migrations, fallbacks, and exclusions.
- [ ] Model picker labels are accurate, lifecycle-aware, and free of unsupported variants.
- [ ] The final diff contains no phase-default, dependency, pricing, prompt, auth, transport, or modality changes outside the approved plan.
- [ ] Optional live-smoke status is stated accurately as run, skipped, or not requested; no raw response or secret is retained.
- [ ] ExecPlan registry and milestone discovery checks pass; planning documents contain final evidence.
- [ ] Each milestone and the parent ExecPlan is completed through the CLI only after all applicable acceptance criteria pass.

## Scope

### In Scope

- Consolidated lifecycle and operator documentation.
- Integrated targeted tests and full repository quality gates.
- Final model-picker, compatibility-key, default, and exclusion audit.
- Diff review for accidental scope expansion and stale docs.
- Optional, deliberately gated provider live smokes when the operator supplies credentials and flags.
- ExecPlan/milestone evidence updates and registry validation.

### Out of Scope

- No new model family, preset, transport, modality, SDK upgrade, or refactor discovered during final QA without a plan amendment.
- No paid request by default and no attempt to bypass provider account/region/quota restrictions.
- No version bump, release publication, commit, push, or pull request unless separately requested.
- No unrelated cleanup, formatting sweep, or baseline-failure remediation.

## Current Health Snapshot

| Area | Starting state | Milestone target |
| --- | --- | --- |
| Targeted baseline | 166 passed plus 8 subtests before implementation | Expanded integrated provider suite passes |
| Lifecycle docs | Current through July 2026 refresh | Current through this implementation, with dated constraints |
| Full quality gates | Not rerun for planned changes | ruff, pyright, pytest, import all green |
| Picker audit | Existing labels cover prior families | New/replaced/deprecated choices accurately disclosed |
| Local runtimes | Codex/Claude Code ownership documented | No static catalog regression |
| ExecPlan registry | Plan and milestones created | Registry check passes; completion state matches evidence |

## Documentation Design

Update `docs/provider-model-lifecycle.md` by provider, keeping direct API and local runtime sections distinct. Each changed direct provider section must state the recommended current model, valid reasoning/thinking choices, context limit, fallback, and important exclusions. Lifecycle mappings must name both the saved compatibility key and the canonical active target.

Document the DeepSeek 32K output limit as an AgentRules application safety cap, not as the provider's maximum. Document that Gemini 3.7 has no disabled/minimal choice and that Grok 4.6 cannot disable reasoning. Document why Grok Multi-Agent, DeepSeek Vision Experimental, GPT-5.5 Pro, and GPT-5.6 Pro mode were not added, so a later catalog refresh does not repeat the same investigation.

Keep the local runtime section authoritative: Codex models/efforts come from `model/list`; Claude Code moving aliases come from the resolved runtime. The docs must not imply that a direct API release guarantees local runtime availability.

## Workstreams & Tasks

### Workstream A - Consolidate operator documentation

- [ ] Update the Direct OpenAI section with o4-mini and deprecated Codex compatibility redirects; state that GPT-5.6 direct presets were already present.
- [ ] Update Anthropic with Opus 5, adaptive/disabled behavior, generic-key move, and Opus 4.8 fallback.
- [ ] Update Gemini with 3.7/3.6/3.5 Flash-Lite level sets, 3.7 fail-fast restriction, and older explicit selection policy.
- [ ] Update xAI with Grok 4.6 as current/default, its exact effort set, Grok 4.5 fallback, and Multi-Agent exclusion.
- [ ] Update DeepSeek with low/high/max, disabled thinking, legacy redirects, 32K application cap, V4 Flash fallback, and Vision exclusion.
- [ ] Preserve and review the local-runtime section and optional-live-smoke gates.
- [ ] Update the rollback/fallback summary table to Opus 4.8, Gemini 3.5 Flash, Grok 4.5, DeepSeek V4 Flash, GPT-5.5 direct, Codex runtime default, and Claude Code runtime default.

### Workstream B - Run integrated offline validation

- [ ] Run the combined provider/picker/runtime targeted command from the parent plan.
- [ ] Run all provider-specific tests affected by the final diff, even if a previous milestone ran them independently.
- [ ] Run `ruff`, `pyright`, full `pytest`, and import smoke.
- [ ] Record exact commands, pass counts, skips, elapsed times, and any warnings in the milestone changelog and parent Outcomes.
- [ ] If a failure is unrelated and pre-existing, prove it against `main` before labeling it unrelated; do not suppress it.

### Workstream C - Audit registry and user experience

- [ ] Enumerate new preset keys by provider and compare them to the approved tables in MS002-MS004.
- [ ] Verify every changed deprecation mapping has both keys registered and resolves to the canonical config.
- [ ] Verify `MODEL_PRESET_DEFAULTS` still contains only `gpt56-sol-default` for all phases.
- [ ] Verify negative exclusions: no static `codex-gpt-5.6*`, Grok Multi-Agent, DeepSeek Vision Experimental, GPT-5.5 Pro, or Pro-mode pseudo-preset.
- [ ] Exercise CLI model-picker filtering/labels through tests or a non-mutating local invocation.
- [ ] Review request payload tests to ensure contract coverage validates wire fields, not only labels and constants.

### Workstream D - Review final diff and planning state

- [ ] Run `git diff --check`, `git diff --stat`, and a focused diff review against `main`.
- [ ] Confirm no dependency/lockfile changes; if dependencies changed unexpectedly, stop and amend the plan.
- [ ] Run `agentrules snapshot sync` only if implementation added, removed, or moved files; review the resulting `SNAPSHOT.md` diff.
- [ ] Update parent Progress, Surprises & Discoveries, Decision Log, and Outcomes & Retrospective with final evidence.
- [ ] Complete MS001-MS005 through `agentrules execplan milestone complete` only when each document's definition of done is satisfied.
- [ ] Complete EP-20260829-001 through `agentrules execplan complete` only after the registry check and all required quality gates pass.

### Workstream E - Optional live evidence

- [ ] Decide explicitly whether live smokes are requested and credentials/flags are available.
- [ ] If requested, run one provider at a time with `pytest --run-live` plus `AGENTRULES_RUN_<PROVIDER>_LIVE=1` and the provider key.
- [ ] Preserve only pass/skip/fail identifiers and bounded diagnostic categories; never save credentials or raw responses.
- [ ] Treat account/region/quota skips as availability evidence, not contract success. Unit/contract tests remain required regardless.

## Dependencies

- MS001-MS004 must be implemented and green.
- The repository's existing dev dependencies provide ruff, pyright, and pytest.
- Live smokes additionally depend on explicit operator intent, provider flags, credentials, and account access; they are optional.

## Risks & Mitigations

- Risk: Individually green provider slices conflict in the shared registry or picker.
  Mitigation: Run the combined matrix/picker suite and enumerate keys against milestone tables.

- Risk: Documentation describes planned rather than shipped behavior.
  Mitigation: Update docs from final configs and prepared-payload tests, then verify every named key exists.

- Risk: A full-suite failure is dismissed as unrelated without evidence.
  Mitigation: Reproduce against `main` before recording it as pre-existing; otherwise treat it as a regression.

- Risk: Optional live tests incur cost or expose secrets.
  Mitigation: Require all documented gates, run only when deliberately requested, cap output, and retain no raw response.

- Risk: Completing the ExecPlan hides incomplete milestone work.
  Mitigation: Complete milestones in sequence through the CLI and run the registry check before parent completion.

- Risk: Final QA expands scope with an attractive newly discovered model.
  Mitigation: Record it as deferred and require a plan amendment/review before implementation.

## Validation / QA Plan

Run from the repository root:

    uv run pytest -q tests/unit/test_provider_model_compatibility_matrix.py tests/unit/test_model_overrides.py tests/unit/test_cli_model_picker_ui.py tests/unit/agents/test_anthropic_capabilities.py tests/unit/agents/test_anthropic_request_builder.py tests/unit/agents/test_gemini_capabilities.py tests/unit/agents/test_xai_helpers.py tests/unit/agents/test_deepseek_helpers.py tests/unit/agents/test_openai_helpers.py tests/unit/agents/test_codex_architect.py tests/unit/agents/test_codex_request_builder.py tests/unit/test_cli_codex_settings.py tests/unit/test_codex_runtime_service.py
    uv run ruff check src tests
    uv run pyright
    uv run pytest -q
    uv run python -c "import agentrules"
    uv run agentrules execplan-registry check
    uv run agentrules execplan list
    uv run agentrules execplan milestone list EP-20260829-001
    git diff --check
    git diff --stat

Expected outcomes:

- All required commands exit 0.
- Full test output has no unexpected failures; exact pass/skip counts are recorded.
- Registry check recognizes the parent and all milestones.
- The final diff contains only approved provider configs/capabilities, tests, lifecycle docs, and planning artifacts.
- No provider network access occurs during required validation.

Optional live-smoke pattern, only when explicitly requested:

    AGENTRULES_RUN_OPENAI_LIVE=1 uv run pytest --run-live -q tests/live/test_provider_model_live_smoke.py -k openai

Use the equivalent documented provider flag for Anthropic, Gemini, DeepSeek, or xAI. Never combine credentials or raw output into the ExecPlan.

## Release Readiness Checklist

- [ ] Public keys are additive or compatibility-preserved.
- [ ] Lifecycle redirects are explicit and tested.
- [ ] Context and effort values match the implementation-day source snapshot.
- [ ] Direct and runtime-provider ownership boundaries remain intact.
- [ ] Rollback choices remain registered.
- [ ] No config/data migration command is required.
- [ ] No dependency or lockfile update is required.
- [ ] No security-sensitive logging or response capture was added.
- [ ] Reviewer can reproduce all required validation without API credentials.

## Deferred Work

- Model-specific Pro transports/modes, specialized multi-agent models, multimodal DeepSeek support, and output-cap expansion stay in separate future plans.
- Version bump, commit, push, PR creation, and release publication require separate user requests.

## Rollout / Recovery

This change is a registry/capability release with no destructive data migration. Existing saved keys remain valid through direct definitions or redirects. If a new recommended model is unavailable, retain its key and revert only the recommendation/generic alias to the documented fallback. If a request contract fails after release, fail closed for the affected model and preserve other providers. Never recover by restoring a retired wire endpoint or deleting a published saved key.

## Changelog

- 2026-08-29: Milestone created.
- 2026-08-29: Added integrated quality gates, documentation matrix, picker/default/exclusion audit, optional live-test boundaries, and release recovery criteria.
