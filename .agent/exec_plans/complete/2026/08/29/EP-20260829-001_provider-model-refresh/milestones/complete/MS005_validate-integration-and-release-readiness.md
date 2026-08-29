---
id: EP-20260829-001/MS005
execplan_id: EP-20260829-001
ms: 5
title: Validate Integration and Release Readiness
status: completed
domain: cross-cutting
owner: '@codex'
created: 2026-08-29
updated: '2026-08-29'
tags:
- providers
- validation
- documentation
- release
risk: med
links:
  issue: ''
  docs: ''
  pr: ''
---

# Validate Integration and Release Readiness

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Integrate the provider slices into one release-ready, auditable change. The lifecycle guide, picker experience, compatibility registry, offline test suite, lint, type checks, import smoke, ExecPlan registry, and final diff must agree with the approved plan. This milestone produces the evidence needed for review; it does not broaden scope or use paid APIs by default.

## Definition of Done

- [x] Anthropic, Gemini, xAI, DeepSeek, OpenAI lifecycle, and Codex runtime targeted suites all pass together.
- [x] Full `ruff`, `pyright`, `pytest`, and import-smoke gates pass.
- [x] `docs/provider-model-lifecycle.md` matches shipped keys, constraints, migrations, fallbacks, and exclusions.
- [x] Model picker labels are accurate, lifecycle-aware, and free of unsupported variants.
- [x] The final diff contains no phase-default, dependency, pricing, prompt, auth, transport, or modality changes outside the approved plan.
- [x] Optional live-smoke status is stated accurately as not requested; no raw response or secret was retained.
- [x] ExecPlan registry and milestone discovery checks pass; planning documents contain final evidence.
- [x] MS001-MS004 were completed through the CLI after their acceptance criteria passed; MS005 and the parent ExecPlan are ready for the same completion flow.

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

Update `docs/provider-model-lifecycle.md` by provider, keeping direct API and local runtime sections distinct. Each changed direct provider section must state the recommended current model, valid reasoning/thinking choices, context limit, fallback, and important exclusions. Every lifecycle key must disclose whether it preserves a live endpoint or redirects a retired endpoint; redirect entries must name the canonical active target.

Document the DeepSeek 32K output limit as an AgentRules application safety cap, not as the provider's maximum. Document that Gemini 3.7 has no disabled/minimal choice and that Grok 4.6 cannot disable reasoning. Document why Grok Multi-Agent, DeepSeek Vision Experimental, GPT-5.5 Pro, and GPT-5.6 Pro mode were not added, so a later catalog refresh does not repeat the same investigation.

Keep the local runtime section authoritative: Codex models/efforts come from `model/list`; Claude Code moving aliases come from the resolved runtime. The docs must not imply that a direct API release guarantees local runtime availability.

## Workstreams & Tasks

### Workstream A - Consolidate operator documentation

- [x] Update the Direct OpenAI section with preserved o4-mini/GPT-5 Mini behavior, effort-matched Terra guidance, retired direct Codex-to-Sol redirects, and runtime-owned static Codex behavior.
- [x] Update Anthropic with Opus 5, adaptive/disabled behavior, generic-key move, and Opus 4.8 fallback.
- [x] Update Gemini with 3.7/3.6/3.5 Flash-Lite level sets, 3.7 fail-fast restriction, and older explicit selection policy.
- [x] Update xAI with Grok 4.6 as current/default, its exact effort set, Grok 4.5 fallback, and Multi-Agent exclusion.
- [x] Update DeepSeek with low/high/max, disabled thinking, legacy redirects, 32K application cap, V4 Flash fallback, and Vision exclusion.
- [x] Preserve and review the local-runtime section and optional-live-smoke gates.
- [x] Verify the optional xAI live smoke shares the provider-owned Grok 4.6 default and retains Grok 4.5 fallback payload coverage.
- [x] Update the rollback/fallback summary table to Opus 4.8, Gemini 3.5 Flash, Grok 4.5, DeepSeek V4 Flash, GPT-5.5 direct, Codex runtime default, and Claude Code runtime default.

### Workstream B - Run integrated offline validation

- [x] Run the combined provider/picker/runtime targeted command from the parent plan.
- [x] Run all provider-specific tests affected by the final diff, even if a previous milestone ran them independently.
- [x] Run `ruff`, `pyright`, full `pytest`, and import smoke.
- [x] Record exact commands, pass counts, skips, elapsed times, and any warnings in the milestone changelog and parent Outcomes.
- [x] No failure required classification against `main`; all required validation completed successfully.

### Workstream C - Audit registry and user experience

- [x] Enumerate new preset keys by provider and compare them to the approved tables in MS002-MS004.
- [x] Verify every changed lifecycle entry has its saved key registered; warning-only entries preserve their config and retired entries resolve to a registered canonical config.
- [x] Verify `MODEL_PRESET_DEFAULTS` still contains only `gpt56-sol-default` for all phases.
- [x] Verify negative exclusions: no static `codex-gpt-5.6*`, Grok Multi-Agent, DeepSeek Vision Experimental, GPT-5.5 Pro, or Pro-mode pseudo-preset.
- [x] Exercise CLI model-picker filtering/labels through tests or a non-mutating local invocation.
- [x] Review request payload tests to ensure contract coverage validates wire fields, not only labels and constants.

### Workstream D - Review final diff and planning state

- [x] Run `git diff --check`, `git diff --stat`, and a focused diff review against `main`.
- [x] Confirm no dependency/lockfile changes; if dependencies changed unexpectedly, stop and amend the plan.
- [x] Snapshot synchronization is not applicable because implementation added, removed, or moved no source files.
- [x] Update parent Progress, Surprises & Discoveries, Decision Log, and Outcomes & Retrospective with final evidence.
- [x] MS001-MS004 were completed through `agentrules execplan milestone complete`; MS005 now satisfies its definition of done and is ready for CLI completion.
- [x] EP-20260829-001 has passed the registry and quality gates and is ready for CLI completion after MS005 is archived and pushed.

### Workstream E - Optional live evidence

- [x] Live smokes were not requested; no credentials or provider-specific live flags were used.
- [x] No live provider invocation was applicable, and no paid request was made.
- [x] No credentials, raw provider responses, or other sensitive response material were retained.
- [x] The current full suite's eleven expected live-test skips were not treated as contract success; the separately gated offline smoke-contract run executed the payload assertions without enabling provider calls.

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

- [x] Public keys are additive or compatibility-preserved.
- [x] Live deprecations and retired-endpoint redirects are explicit and tested.
- [x] Context and effort values match the implementation-day source snapshot.
- [x] Direct and runtime-provider ownership boundaries remain intact.
- [x] Rollback choices remain registered.
- [x] No config/data migration command is required.
- [x] No dependency or lockfile update is required.
- [x] No security-sensitive logging or response capture was added.
- [x] Reviewer can reproduce all required validation without API credentials.

## Deferred Work

- Model-specific Pro transports/modes, specialized multi-agent models, multimodal DeepSeek support, and output-cap expansion stay in separate future plans.
- Version bump, commit, push, PR creation, and release publication require separate user requests.

## Rollout / Recovery

This change is a registry/capability release with no destructive data migration. Existing saved keys remain valid through direct definitions or redirects. If a new recommended model is unavailable, retain its key and revert only the recommendation/generic alias to the documented fallback. If a request contract fails after release, fail closed for the affected model and preserve other providers. Never recover by restoring a retired wire endpoint or deleting a published saved key.

## Changelog

- 2026-08-29: Milestone created.
- 2026-08-29: Added integrated quality gates, documentation matrix, picker/default/exclusion audit, optional live-test boundaries, and release recovery criteria.
- 2026-08-29: Updated `docs/provider-model-lifecycle.md` with the shipped provider contracts, live deprecations, retired-endpoint redirects, fallbacks, ownership boundaries, safety caps, and explicitly deferred transport/modality models.
- 2026-08-29: The expanded provider/picker/runtime suite passed with 427 tests and 48 subtests in 8.94 seconds. The command covered the compatibility matrix, overrides, picker UI, all changed provider capability/request paths, Codex request/runtime behavior, and CLI Codex settings.
- 2026-08-29: Repository gates passed: `ruff check src tests`, `pyright` with zero errors and warnings, import smoke, and full `pytest -q` with 968 passed, 10 skipped, 48 subtests passed, and four pathspec deprecation warnings from the existing file-retriever tests in 11.74 seconds.
- 2026-08-29: Final registry audit validated 27 exact new preset keys across Anthropic (6), Gemini (11), xAI (4), DeepSeek (3), and OpenAI (3), plus eight warning-only live lifecycle entries and two retired direct Codex redirects. Phase defaults remain `gpt56-sol-default`, all planned exclusions remain absent, and request tests cover provider-native wire fields.
- 2026-08-29: ExecPlan registry/discovery, `git diff --check`, focused scope review, and dependency/lockfile review passed. No source topology changed, so `agentrules snapshot sync` was not applicable.
- 2026-08-29: Optional live smokes were not requested. No provider flag, credential, paid request, raw response, or secret was used or retained; the ten expected live-test skips were not counted as contract evidence.
- 2026-08-29: Post-completion audit aligned the optional xAI smoke with the centralized Grok 4.6 default, retained Grok 4.5 fallback payload coverage, and reconciled lifecycle planning artifacts with final preserve-or-redirect behavior.
- 2026-08-29: Final audit validation passed: offline smoke contract 4 passed/5 skipped, full suite 990 passed/11 skipped with 57 subtests, Ruff, Pyright, import, lockfile, ExecPlan registry, and diff checks green. No provider enable flag or credential was used.
- 2026-08-29: Post-completion review added the documented Claude Code 2.1.219 minimum gate for pinned
  `claude-opus-5` programmatic requests, exposed the gate in runtime diagnostics, and retained moving-alias
  ownership without adding a static picker preset.
- 2026-08-29: Opus 5 gate validation passed: 159 focused tests and 21 subtests, full suite with 993 passed,
  11 expected live-test skips, and 57 subtests, plus Ruff, Pyright, import, lockfile, ExecPlan registry,
  official-reference, and diff checks.
