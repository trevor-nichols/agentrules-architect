---
id: EP-20260829-001
title: Refresh Provider Model Registry and Capabilities
status: done
kind: refactor
domain: cross-cutting
owner: '@codex'
created: 2026-08-29
updated: '2026-08-29'
tags:
- providers
- models
- capabilities
- lifecycle
- compatibility
touches:
- agents
- backend
- cli
- docs
- tests
risk: med
breaking: false
migration: true
links:
  issue: ''
  pr: ''
  docs: docs/provider-model-lifecycle.md
depends_on: []
supersedes: []
---

# EP-20260829-001 - Refresh Provider Model Registry and Capabilities

This ExecPlan is a living document. Keep `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` up to date as work proceeds.

Maintain this plan in accordance with `.agent/PLANS.md`. The user approved this revision on 2026-08-29; all milestones and this ExecPlan were completed and archived on 2026-08-29.

## Purpose / Big Picture

AgentRules has a reviewed static registry for direct API providers and runtime-owned discovery for local providers. The static registry was last substantially refreshed in July 2026, and several upstream catalogs have moved since then. After this plan is implemented, operators will be able to choose Claude Opus 5, Gemini 3.7 Flash, Gemini 3.6 Flash, Gemini 3.5 Flash-Lite, Grok 4.6, and the documented DeepSeek V4 effort levels without constructing unsupported payloads by hand.

The change also closes lifecycle gaps for model keys already exposed by AgentRules. Saved keys remain loadable; deprecated-but-live o4-mini and GPT-5 Mini choices stay bound to their selected model and recommend effort-matched GPT-5.6 Terra choices. Retired direct GPT-5.1/5.2 Codex keys resolve to medium-effort GPT-5.6 Sol, while static Codex compatibility selections retain their runtime identity and remain app-server catalog-gated. Codex continues to discover models and effort values from `model/list`; this plan deliberately does not turn a moving local runtime catalog into a hard-coded API registry.

An operator can verify the result by opening the model picker, filtering each direct provider, and observing the new model families and effort-specific labels. Automated contract tests prove that every new preset resolves to the intended provider, wire model, context limit, and provider-native thinking value. Lifecycle tests prove both states: deprecated-but-live keys preserve their configured endpoint, while retired keys redirect to registered canonical presets. Existing project defaults remain GPT-5.6 Sol and existing explicit saved keys continue to load.

## Scope

### In Scope

- Add direct Anthropic presets for `claude-opus-5`, including an explicit non-thinking choice and adaptive-thinking choices at low, medium, high, xhigh, and max effort.
- Move the generic direct Anthropic keys `claude-opus` and `claude-opus-reasoning` to Opus 5 while preserving all pinned Opus 4.8 keys as rollback choices.
- Add direct Gemini presets for `gemini-3.7-flash`, `gemini-3.6-flash`, and `gemini-3.5-flash-lite`, with only the thinking levels each family accepts.
- Add direct xAI presets for `grok-4.6` at low, medium, high/default, and xhigh effort; make Grok 4.6 the default model used by a directly constructed `XaiArchitect`.
- Add DeepSeek V4 low-effort support for Flash and Pro, max support for Flash, and explicit fail-fast handling for unsupported effort values.
- Preserve DeepSeek's 32,000-token application output safety cap while documenting that it is intentionally lower than the current upstream maximum.
- Add lifecycle metadata for exposed OpenAI o4-mini, GPT-5 Mini, retired direct Codex, and static Codex compatibility keys; redirect only retired direct endpoints.
- Add GPT-5 Mini low/medium saved presets and GPT-5.6 Terra low so preserved low/medium/high workloads have effort-matched Terra migration choices.
- Update model-picker labels, lifecycle documentation, unit tests, cross-provider contract tests, and optional live-smoke model selection.
- Reconfirm upstream facts at the start of implementation and record any catalog drift in this plan before changing code.

### Out of Scope

- Do not add static GPT-5.6 Codex presets. Codex models and efforts remain app-server catalog data.
- Do not add a static Claude Code Opus 5 picker preset in this refresh. Programmatic full-model-ID
  configurations remain allowed behind the documented Claude Code 2.1.219 exact-runtime gate; the moving
  `opus` alias remains runtime-owned.
- Do not add `gpt-5.5-pro` in this refresh. The current architect assumes streaming while that model's transport contract requires model-specific handling.
- Do not model GPT-5.6 Pro mode. Pro mode is an execution capability orthogonal to model identity and needs a separate design rather than another preset suffix.
- Do not add `grok-4.20-multi-agent-0309`; the existing xAI adapter is Chat-Completions-oriented and does not model multi-agent Responses/xAI-SDK semantics.
- Do not add `deepseek-v4-flash-vision-exp`; the current DeepSeek adapter is text-oriented and does not expose a reviewed multimodal input contract.
- Do not add restricted or account-gated Anthropic Mythos 5, OpenAI cyber/Daybreak, preview-only, or undocumented models.
- Do not raise the global or provider output-token limits, change pricing metadata, change phase defaults, upgrade provider SDKs, or redesign the model registry.
- Do not make paid live API requests as part of the default validation path.

## Upstream Contract Snapshot

The implementation must begin by revalidating this dated snapshot. If a model has been renamed, retired, or had its capability contract changed after 2026-08-29, stop that provider slice, record the discovery, and amend the plan before proceeding.

| Provider | Target contract as of 2026-08-29 | Product decision |
| --- | --- | --- |
| Anthropic | `claude-opus-5`; 1,000,000-token context; 128,000-token output ceiling; adaptive thinking is the default; adaptive effort accepts low, medium, high, xhigh, and max; an explicit disabled-thinking request remains available. | Add direct presets, make generic Opus keys point to Opus 5, keep pinned 4.8 choices. |
| Gemini | `gemini-3.7-flash` accepts low/medium/high and defaults to medium; `gemini-3.6-flash` accepts minimal/low/medium/high and defaults to medium; `gemini-3.5-flash-lite` accepts minimal/low/medium/high and defaults to minimal. Each advertises a 1,048,576-token input window and supports tools plus structured output. | Add explicit stable-family presets. Do not silently map disabled/minimal to 3.7 low. |
| xAI | `grok-4.6`; 500,000-token context; low/medium/high/xhigh reasoning; reasoning cannot be disabled; Chat Completions and Responses support the ordinary tool/structured-output path. | Make it the recommended direct xAI model and direct-architect default. |
| DeepSeek | `deepseek-v4-flash` and `deepseek-v4-pro` remain canonical; native thinking efforts are low/high/max; compatibility mapping sends medium and xhigh to high; thinking can be disabled; the provider advertises a 1M context and 384K output ceiling. | Expose low and missing Flash max; honor documented medium/xhigh compatibility mapping; reject minimal; retain the 32K application safety cap. |
| OpenAI | GPT-5.6 Sol/Terra/Luna are active. o4-mini remains deprecated-but-live and GPT-5 Mini is also deprecated-but-live; both recommend Terra. Direct `gpt-5.1-codex` and `gpt-5.2-codex` are retired with Sol as the documented replacement. | Preserve live endpoint identity, redirect retired direct Codex keys to medium-effort Sol, keep static Codex choices catalog-gated, and add Terra low for effort-preserving migration. |

## Progress

- [x] (2026-08-29) Created branch `codex/provider-model-refresh-2026-08` from a clean `main` worktree.
- [x] (2026-08-29) Captured the upstream catalog audit and baseline test result: 166 tests plus 8 subtests passed across the targeted provider suite.
- [x] (2026-08-29) Created this ExecPlan and five milestone documents through the AgentRules CLI.
- [x] (2026-08-29) User reviewed and approved this plan and authorized sequential milestone execution.
- [x] (2026-08-29) MS001 locked the implementation-day source snapshot and migration contract; targeted baseline passed with 166 tests and 8 subtests.
- [x] (2026-08-29) MS002 added Opus 5 and current Gemini Flash families with exact capability validation; 232 tests and 5 subtests passed with lint, types, and import smoke green.
- [x] (2026-08-29) MS003 added Grok 4.6 and completed DeepSeek V4 effort handling; 204 tests and 10 subtests passed with lint, types, and import smoke green.
- [x] (2026-08-29) MS004 added effort-preserving OpenAI lifecycle states and hardened the Codex ownership boundary; 260 tests and 43 subtests passed with lint, types, and import smoke green.
- [x] (2026-08-29) MS005 completed lifecycle documentation, registry/default/exclusion audits, integrated provider validation, and full repository quality gates.
- [x] (2026-08-29) MS001-MS005 and this ExecPlan were completed and archived through the CLI after all acceptance criteria passed.
- [x] (2026-08-29) Post-completion review removed premature OpenAI runtime redirects and raised the Google Gen AI SDK floor to the first release with exact minimal/medium thinking enums.
- [x] (2026-08-29) Post-completion lifecycle review added Terra low, redirected retired direct Codex keys to Sol, preserved catalog-gated static Codex identity, and reconciled archived planning artifacts with shipped behavior.
- [x] (2026-08-29) Post-completion xAI review centralized the Grok 4.6 default and aligned the optional live-smoke default and payload contract while retaining Grok 4.5 fallback coverage.

## Surprises & Discoveries

- The repository already contains GPT-5.6 Sol, Terra, and Luna direct-API presets and robust dynamic Codex model discovery. The OpenAI work is lifecycle maintenance, not a GPT-5.6 registry addition.
- Gemini capability profiles use prefix matching. `gemini-3.5-flash-lite` must be declared before `gemini-3.5-flash`, or the more specific family will inherit the wrong thinking contract.
- DeepSeek's request helper currently reduces every enabled mode except xhigh/max to `high`. Adding low support therefore requires request validation, not only new constants and labels.
- At implementation start, xAI's direct-architect default and optional live smoke still used `grok-4.5`, and context-limit logic named that family explicitly. The final implementation centralizes the `grok-4.6` default across the architect and live smoke while retaining 4.5 as fallback coverage.
- Existing static Codex-derived presets predate runtime catalog discovery. They are compatibility surfaces; new runtime models must continue to come from `model/list`.
- OpenAI lifecycle facts changed during review: o4-mini and GPT-5 Mini remain callable but now recommend GPT-5.6 Terra, while direct GPT-5.1/5.2 Codex endpoints are retired and name GPT-5.6 Sol as their replacement. This requires warning-only metadata for live keys, redirects only for retired direct keys, and a Terra low preset to preserve low/medium/high intent.
- DeepSeek's current Thinking Mode guide documents compatibility mappings that were not captured in the planning draft: requested `medium` and `xhigh` both map to actual `high`, while only `max` maps to `max`. MS003 was amended to implement and test that provider-defined behavior; only `minimal` remains unsupported.
- Exact Gemini thinking contracts also require exact SDK enum support. The initial implementation still inherited the older nearest-enum fallback; the MS002 audit caught this and changed current Flash families to fail closed when the installed SDK lacks a required level.
- Moving the xAI constructor default is not sufficient by itself: the previous Grok 4.5 picker label also claimed to be recommended. MS003 now labels Grok 4.6 as recommended and Grok 4.5 as the explicit fallback.
- The pre-existing static Codex GPT-5.6 negative test inspected `BASE_MODEL_PRESETS`, which never contains Codex-derived entries. MS004 changed it to inspect the combined `MODEL_PRESETS` registry, so it can fail if a static Codex GPT-5.6 key is actually introduced.
- The full repository suite is green but reports four pathspec deprecation warnings from `tests/unit/test_file_retriever.py`. They do not affect this provider refresh, and no warning was suppressed or reclassified as a passing contract check.
- A post-completion review found that Claude Code v2.1.219 is the documented introduction point for
  `claude-opus-5`. The public `create_claude_code_config(CLAUDE_OPUS)` path therefore remains supported,
  but now fails closed when the exact resolved executable is older or cannot be versioned.

## Decision Log

- Decision: Treat direct API providers and local runtime providers as separate ownership domains.
  Rationale: Anthropic, Gemini, xAI, DeepSeek, and direct OpenAI have reviewed static registries. Codex and Claude Code resolve moving models from installed runtimes and account policy.
  Date/Author: 2026-08-29 / @codex

- Decision: Preserve every existing saved preset key and route retired endpoints through `DEPRECATED_PRESETS`.
  Rationale: Preset keys are public compatibility IDs. Removing or silently invalidating them would break stored configuration before the operator can select a replacement.
  Date/Author: 2026-08-29 / @codex

- Decision: Treat deprecation metadata and retirement redirects as distinct lifecycle states.
  Rationale: A deprecated endpoint may remain callable with different behavior and cost from its successor. Its saved key stays bound to the original model until retirement; warning metadata can still hide it from new selections and recommend an operator-controlled migration.
  Date/Author: 2026-08-29 / @codex

- Decision: Keep explicit older pinned models available unless the upstream endpoint is retired.
  Rationale: A current recommended model and a deliberate rollback model serve different cost, latency, and behavior roles. This refresh should not erase working choices.
  Date/Author: 2026-08-29 / @codex

- Decision: Retain DeepSeek's 32,000-token `max_tokens` application cap.
  Rationale: Raising the cap would materially change memory, latency, cost, and phase-output behavior. The registry refresh will document the conservative cap; output expansion belongs in a separately measured change.
  Date/Author: 2026-08-29 / @codex

- Decision: Use fail-fast capability validation for unsupported effort values.
  Rationale: The project rejects undocumented coercion. Gemini 3.7 must not translate disabled/minimal to low, xAI 4.6 must not accept disabled/minimal, and DeepSeek must reject minimal while preserving its explicitly documented medium-to-high and xhigh-to-high compatibility mappings.
  Date/Author: 2026-08-29 / @codex

- Decision: Follow DeepSeek's documented compatibility mapping for generic medium and xhigh modes.
  Rationale: The official Thinking Mode table maps requested medium and xhigh to actual high for both V4 Flash and V4 Pro. Canonical max presets use `ReasoningMode.MAX`; programmatic `ReasoningMode.XHIGH` must no longer be treated as max.
  Date/Author: 2026-08-29 / @codex

- Decision: Defer specialized transport and modality models.
  Rationale: Grok Multi-Agent, DeepSeek Vision Experimental, GPT-5.5 Pro, and GPT-5.6 Pro mode require request/response semantics not represented by the current direct adapters. A picker entry without transport support would create a guaranteed runtime failure.
  Date/Author: 2026-08-29 / @codex

- Decision: Do not run optional paid live smokes without an explicit operator request.
  Rationale: The offline capability, request-payload, picker, lifecycle, and runtime tests provide reproducible contract coverage without credentials. Live availability also depends on account, region, and quota state and was not requested for this execution.
  Date/Author: 2026-08-29 / @codex

- Decision: Allow pinned Opus 5 through Claude Code only on an exactly versioned compatible runtime.
  Rationale: Claude Code v2.1.219 documents support for `claude-opus-5`. Reusing the centralized runtime
  gate preserves the public programmatic path while preventing dispatch to older or unverified executables.
  Moving aliases remain runtime-owned and are not inferred to resolve to Opus 5.
  Date/Author: 2026-08-29 / @codex

## Outcomes & Retrospective

The refresh shipped 27 exact direct-provider preset keys across Anthropic (6), Gemini (11), xAI (4), DeepSeek (3), and OpenAI (3). Opus 5 now owns the generic direct Opus aliases while pinned Opus 4.8 remains available. Gemini exposes exact 3.7 Flash, 3.6 Flash, and 3.5 Flash-Lite thinking contracts. Grok 4.6 is the recommended direct xAI model and shared architect/live-smoke default with Grok 4.5 retained as fallback. DeepSeek V4 handles disabled, low, documented medium/high/xhigh-to-high compatibility, and max explicitly while retaining the 32K application output cap. GPT-5 Mini low/medium/high remain available only for saved compatibility, while Terra low/medium/high are the current effort-matched migration choices.

Retired lifecycle mappings continue to resolve from registered saved keys to registered canonical presets. Eight deprecated-but-live OpenAI/Codex entries carry warning metadata without runtime replacements: three o4-mini keys, three GPT-5 Mini keys, and two static Codex selections. The two retired direct GPT-5.1/5.2 Codex keys redirect to `gpt56-sol-default`. Existing phase defaults remain `gpt56-sol-default`. Codex model and effort discovery remains runtime-owned, accepts future catalog effort tokens, and has no new static GPT-5.6 preset. The planned exclusions remain absent: Grok Multi-Agent, DeepSeek Vision Experimental, GPT-5.5 Pro, and a GPT-5.6 Pro-mode pseudo-preset.

Claude Code continues to own moving aliases. Programmatic requests that pin `claude-opus-5` remain
allowed when the exact resolved runtime is version 2.1.219 or newer; older and unversionable runtimes fail
before SDK dispatch. No static Claude Code Opus 5 picker preset was introduced.

The Opus 5 runtime-gate review passed 159 focused tests plus 21 subtests and the full suite with 993
passed, 11 expected live-test skips, and 57 subtests. Ruff, Pyright, import smoke, lockfile validation,
ExecPlan registry/discovery, source-reference, and diff checks also passed.

The final xAI reasoning review removed the generic `None` fallback for effort-controlled profiles, so
programmatic temperature mode can no longer silently select Grok 4.6's provider-default high effort. The
model remains available for every documented mode. Validation passed 180 focused tests plus 21 subtests
and the full suite with 995 passed, 11 expected live-test skips, and 57 subtests; Ruff, Pyright, import,
lockfile, ExecPlan registry/discovery, official-reference, audit, and diff checks also passed.

Final offline validation passed. The expanded provider, picker, and runtime suite completed with 427 tests and 48 subtests in 8.94 seconds. `ruff check src tests`, `pyright` with zero errors and warnings, and import smoke passed. Full `pytest -q` completed with 968 passed, 10 expected live-test skips, 48 subtests passed, and four pathspec deprecation warnings in 11.74 seconds. ExecPlan registry/discovery, registry key/default/exclusion diagnostics, `git diff --check`, and focused scope review also passed.

Post-completion review raised the declared `google-genai` floor from 1.51.0 to 1.56.0, the first SDK release with the required `MINIMAL` and `MEDIUM` thinking enums; the lockfile's resolved SDK remains 1.64.0. The review fix passed 186 focused tests plus 12 subtests, an isolated 1.56.0 minimum-version run with 42 tests, and the full suite with 963 passed, 10 expected live-test skips, and 48 subtests. Ruff, Pyright, import, lockfile, registry, and diff checks also passed.

Subsequent lifecycle and request-contract reviews preserved live OpenAI endpoint identity, redirected retired direct Codex keys to Sol, added effort-matched Terra low, and centralized Anthropic thinking/effort validation across direct and Claude Code transports. The resulting full suite passed with 990 tests, 10 expected live-test skips, and 57 subtests; Ruff, Pyright, import, lockfile, and diff checks passed. A final audit then aligned the optional xAI smoke with the provider-owned Grok 4.6 default and reconciled every lifecycle-bearing ExecPlan artifact with this final matrix. Its offline smoke-contract run passed four payload cases and skipped five disabled provider calls; the full suite passed with 990 tests, 11 expected live-test skips, and 57 subtests. Ruff, Pyright, import, lockfile, ExecPlan registry, and diff checks remained green.

The final implementation requires no configuration-data migration, phase-default, pricing, prompt, authentication, or transport change. No source files were added, removed, or moved, so snapshot synchronization was not applicable. Optional live smokes were not requested and were not run; no provider credentials, paid requests, raw responses, or secrets were used or retained. Rollback choices remain Opus 4.8, Gemini 3.5 Flash, Grok 4.5, DeepSeek V4 Flash, GPT-5.5 direct, and runtime defaults for Codex and Claude Code. Specialized transports, modalities, and output-cap expansion remain deliberately deferred.

## Context and Orientation

`src/agentrules/core/types/models.py` defines immutable `ModelConfig` values. A config carries provider identity, wire model name, generic `ReasoningMode`, optional provider-specific effort, and context-estimation metadata. New public configurations start here.

`src/agentrules/config/agents.py` turns configs into labeled `BASE_MODEL_PRESETS`, attaches conservative input limits in `_apply_model_limits`, derives compatibility presets for Codex and Claude Code, and defines phase defaults. The direct-provider picker consumes these entries. Phase defaults must remain `gpt56-sol-default` throughout this plan.

`src/agentrules/core/configuration/model_presets.py` is the compatibility boundary. `DEPRECATED_PRESETS` records both warning-only deprecations and retired-endpoint redirects. `resolve_runtime_preset_key()` preserves the saved key when `replacement_key` is unset and redirects only when a registered canonical replacement exists. Tests cover both states.

Provider-native capability metadata lives near each adapter: Anthropic and Gemini use immutable profile tuples, while xAI and DeepSeek use immutable `ModelDefaults` maps. Request builders translate a generic reasoning mode immediately before dispatch. The static registry and request-time translation must agree; a model must never appear in the picker if the adapter cannot construct its supported payload.

`tests/unit/test_provider_model_compatibility_matrix.py` is the end-to-end static contract. Each row checks preset key, provider, model name, generic reasoning mode, context window, and provider-native wire reasoning. Provider-specific tests cover edge cases and invalid combinations. `tests/live/test_provider_model_live_smoke.py` is optional and gated; it is not part of the default acceptance path.

`docs/provider-model-lifecycle.md` records behavior that a model ID alone cannot communicate: moving aliases, retired compatibility keys, fallback rules, thinking constraints, local-runtime ownership, and live-smoke gates.

## Plan of Work

First, execute MS001. Reopen the official source pages listed in Artifacts and Notes, confirm that the dated contract table is still correct, run the targeted baseline, and update this plan's Decision Log if any fact moved. This milestone does not expose new models; it prevents implementation against a stale catalog.

Second, execute MS002 as a complete direct-provider slice. Add Opus 5 and the three Gemini families to immutable configs, capability profiles, labels, input-limit classification, and tests in one milestone. Ensure specific Gemini prefixes precede broader ones. Update generic Opus keys only after pinned Opus 5 presets and request tests pass. Do not create pinned Claude Code Opus 5 presets.

Third, execute MS003. Add Grok 4.6 to config defaults, preset labels, constructor defaults, context limits, and request validation. Add DeepSeek low/max configurations and replace the current implicit effort coercion with explicit supported mappings and errors. Leave the DeepSeek wire model IDs and 32K application output cap unchanged.

Fourth, execute MS004. Add GPT-5 Mini low/medium saved configurations, mark Mini and o4-mini as deprecated-but-live without runtime redirects, and add Terra low to complete the effort-matched migration matrix. Redirect retired direct GPT-5.1/5.2 Codex keys to medium-effort Sol while preserving static Codex identity behind app-server catalog filtering. Add regression tests proving both lifecycle states and that future Codex models/efforts remain dynamic without a static GPT-5.6 Codex preset.

Finally, execute MS005. Update lifecycle prose and fallback tables, run targeted and full quality gates, review picker labels for lifecycle disclosure, and inspect the final diff for accidental phase-default, SDK, pricing, or transport changes. Sync `SNAPSHOT.md` only if implementation adds, removes, or moves files. Complete milestones and the ExecPlan through the CLI only after their validation evidence is recorded.

## Concrete Steps

Run all commands from `/Volumes/AGENAI/Coding/public-github/agentrules-architect` on branch `codex/provider-model-refresh-2026-08`.

1. Before implementation, confirm branch and baseline:

       git status --short --branch
       uv run python -c "import agentrules"
       uv run pytest -q tests/unit/test_provider_model_compatibility_matrix.py tests/unit/agents/test_anthropic_capabilities.py tests/unit/agents/test_gemini_capabilities.py tests/unit/agents/test_xai_helpers.py tests/unit/agents/test_deepseek_helpers.py tests/unit/test_model_overrides.py

   Expected: the branch name is correct, only approved planning changes are present, import succeeds, and the current targeted suite passes. The planning baseline observed on 2026-08-29 was `166 passed, 8 subtests passed`.

2. Implement and validate each milestone in numeric order. Update that milestone's checkboxes, health snapshot, changelog, risks, and validation evidence before starting the next milestone. Do not mark a milestone complete while its targeted tests fail.

3. After the provider slices, run the integrated test group:

       uv run pytest -q tests/unit/test_provider_model_compatibility_matrix.py tests/unit/test_model_overrides.py tests/unit/test_cli_model_picker_ui.py tests/unit/agents/test_anthropic_capabilities.py tests/unit/agents/test_anthropic_request_builder.py tests/unit/agents/test_gemini_capabilities.py tests/unit/agents/test_xai_helpers.py tests/unit/agents/test_deepseek_helpers.py tests/unit/agents/test_openai_helpers.py tests/unit/agents/test_codex_architect.py tests/unit/test_cli_codex_settings.py

   Expected: all tests pass without network access. New negative cases must assert actionable errors before a client dispatch is attempted.

4. Run repository quality gates:

       uv run ruff check src tests
       uv run pyright
       uv run pytest -q
       uv run python -c "import agentrules"

   Expected: no lint, type, test, or import failures. If the full suite has a known unrelated failure, capture the exact command and failure in Surprises & Discoveries; do not silently claim success.

5. Review the final registry and documentation:

       uv run agentrules execplan-registry check
       uv run agentrules execplan list
       uv run agentrules execplan milestone list EP-20260829-001
       git diff --check
       git diff --stat

   Expected: registry validation succeeds, all five milestones are discoverable, no whitespace errors exist, and the diff is limited to approved provider registry/capability/tests/docs plus planning artifacts.

6. Optional direct-provider live smokes may be run only when the operator deliberately supplies `--run-live`, a provider-specific `AGENTRULES_RUN_<PROVIDER>_LIVE=1` flag, and credentials. Record skip/pass/fail evidence without raw responses or secrets. Unit and contract tests remain the required acceptance evidence.

## Validation and Acceptance

The work is acceptable only when all of the following are true:

- The model picker exposes the planned direct-provider keys with accurate, lifecycle-aware labels and no unsupported effort variants.
- `claude-opus` and `claude-opus-reasoning` resolve to Opus 5; pinned Opus 4.8 keys still resolve to Opus 4.8.
- Opus 5 adaptive requests emit only documented effort values, while the non-thinking preset emits an explicit disabled-thinking request without an incompatible effort field.
- Gemini 3.7 resolves low, medium, and high exactly and rejects disabled/minimal. Gemini 3.6 and 3.5 Flash-Lite resolve their documented minimal/low/medium/high levels. Structured output plus tools remains enabled for all three families.
- Grok 4.6 resolves to a 500,000-token context, accepts exactly low/medium/high/xhigh, rejects
  disabled/minimal/max/temperature, and is the default for direct `XaiArchitect` construction.
- DeepSeek V4 maps low to `low`, medium/enabled/dynamic/high/xhigh to `high`, and max to `max`; disabled omits effort and disables thinking; minimal fails before dispatch. Flash and Pro keep the 32K application output cap.
- Every new/changed compatibility key remains present, its replacement key is registered, and runtime resolution returns the replacement config.
- Existing phase defaults stay unchanged at `gpt56-sol-default`.
- Codex runtime model and effort discovery tests still accept future catalog values and no static Codex GPT-5.6 preset is added.
- No experimental modality, multi-agent, Pro transport, restricted-access, or undocumented model appears in the picker.
- The targeted suite, ruff, pyright, full pytest suite, import smoke, ExecPlan registry check, and `git diff --check` pass.
- `docs/provider-model-lifecycle.md` states the new preferred/fallback choices, compatibility redirects, conservative DeepSeek cap, and deferred transport/modality models.

## Idempotence and Recovery

All registry edits are deterministic Python constants and immutable metadata. Re-running tests and CLI registry updates is safe. The new saved keys are additive, and legacy keys remain present, so no destructive configuration migration or data rewrite is required.

Implement one milestone at a time. If a provider slice fails, revert only that milestone's uncommitted changes with an explicit patch; do not use `git reset --hard` or broad checkout commands. Because the work is isolated on `codex/provider-model-refresh-2026-08`, `main` remains a clean recovery point.

If an upstream model disappears during implementation, leave the existing registry behavior intact for that provider, record the discrepancy, and amend the plan. Do not guess a replacement. If a new model needs an SDK feature, transport, modality, or authentication change outside this plan, defer the model rather than adding a preset that cannot work.

For rollback after implementation, preserve all new saved keys and redirect only the recommended/generic alias to the documented fallback: Opus 4.8 for Anthropic, Gemini 3.5 Flash for Gemini, Grok 4.5 for xAI, V4 Flash for DeepSeek, GPT-5.5 for direct OpenAI, and runtime default for Codex. Removing newly published preset keys is not an acceptable rollback because saved configurations may already reference them.

## Artifacts and Notes

Planning artifacts:

- `.agent/exec_plans/complete/2026/08/29/EP-20260829-001_provider-model-refresh/EP-20260829-001_provider-model-refresh.md`
- `.agent/exec_plans/complete/2026/08/29/EP-20260829-001_provider-model-refresh/milestones/complete/MS001_lock-model-contracts-and-lifecycle-policy.md`
- `.agent/exec_plans/complete/2026/08/29/EP-20260829-001_provider-model-refresh/milestones/complete/MS002_refresh-anthropic-and-gemini-model-families.md`
- `.agent/exec_plans/complete/2026/08/29/EP-20260829-001_provider-model-refresh/milestones/complete/MS003_refresh-xai-and-deepseek-capabilities.md`
- `.agent/exec_plans/complete/2026/08/29/EP-20260829-001_provider-model-refresh/milestones/complete/MS004_harden-openai-lifecycle-and-codex-runtime-boundaries.md`
- `.agent/exec_plans/complete/2026/08/29/EP-20260829-001_provider-model-refresh/milestones/complete/MS005_validate-integration-and-release-readiness.md`

Upstream sources to revalidate at MS001:

- Anthropic model overview: `https://platform.claude.com/docs/en/models/overview`
- Anthropic adaptive thinking and effort: `https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking` and `https://platform.claude.com/docs/en/build-with-claude/effort`
- Gemini model catalog and thinking: `https://ai.google.dev/gemini-api/docs/models` and `https://ai.google.dev/gemini-api/docs/thinking`
- xAI Grok 4.6 and reasoning controls: `https://docs.x.ai/developers/grok-4-6` and `https://docs.x.ai/developers/model-capabilities/text/reasoning`
- DeepSeek updates, thinking mapping, and limits: `https://api-docs.deepseek.com/updates/`, `https://api-docs.deepseek.com/guides/thinking_mode/`, and `https://api-docs.deepseek.com/quick_start/pricing/`
- Official OpenAI model catalog, o4-mini page, GPT-5 Mini page, and latest guide: `https://developers.openai.com/api/docs/models/all`, `https://developers.openai.com/api/docs/models/o4-mini`, `https://developers.openai.com/api/docs/models/gpt-5-mini`, and `https://developers.openai.com/api/docs/guides/latest-model`

The targeted baseline was run before plan creation and passed: `166 passed, 8 subtests passed in 4.82s`. MS001 repeated it after implementation-day source revalidation: `166 passed, 8 subtests passed in 3.11s`. This is evidence of clean starting health, not evidence that later implementation milestones work.

## Interfaces and Dependencies

No dependency version change is planned. The installed Anthropic, Gemini, OpenAI-compatible, and OpenAI SDK surfaces already carry the request fields used by these model families. If implementation proves otherwise, stop and amend the plan rather than adding an undeclared SDK upgrade.

The public compatibility interfaces are preset-key strings in `MODEL_PRESETS`, saved override values resolved by `model_presets.resolve_runtime_preset_key()`, and imported `ModelConfig` constants. Existing keys and imports must remain usable.

The internal capability interfaces are `CapabilityProfile`/`ThinkingPolicy` for Anthropic, `GeminiCapabilityProfile` and thinking-level resolution for Gemini, `xai.config.ModelDefaults`, and `deepseek.config.ModelDefaults` plus `deepseek.request_builder.prepare_request()`. These remain immutable, provider-local metadata structures.

Provider-native wire behavior is constrained as follows: Anthropic uses top-level `thinking` and `output_config.effort`; Gemini uses SDK `thinking_level`; xAI Chat Completions uses `reasoning_effort`; DeepSeek uses `extra_body.thinking.type` plus `reasoning_effort`; OpenAI GPT-5 Mini uses the Responses API `reasoning.effort`. Tests must validate those request-time translations rather than only checking labels.

Codex remains dependent on the resolved local executable and app-server `model/list`. Static compatibility presets must not bypass `ConfigManager.build_codex_launch_config()`, introduce an API-key requirement, or constrain future runtime-reported effort tokens.
