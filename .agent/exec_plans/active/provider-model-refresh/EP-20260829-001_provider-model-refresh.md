---
id: EP-20260829-001
title: "Refresh Provider Model Registry and Capabilities"
status: active
kind: refactor
domain: cross-cutting
owner: "@codex"
created: 2026-08-29
updated: 2026-08-29
tags: [providers, models, capabilities, lifecycle, compatibility]
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
  issue: ""
  pr: ""
  docs: "docs/provider-model-lifecycle.md"
depends_on: []
supersedes: []
---

# EP-20260829-001 - Refresh Provider Model Registry and Capabilities

This ExecPlan is a living document. Keep `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` up to date as work proceeds.

Maintain this plan in accordance with `.agent/PLANS.md`. The user approved this revision on 2026-08-29; milestone execution is active.

## Purpose / Big Picture

AgentRules has a reviewed static registry for direct API providers and runtime-owned discovery for local providers. The static registry was last substantially refreshed in July 2026, and several upstream catalogs have moved since then. After this plan is implemented, operators will be able to choose Claude Opus 5, Gemini 3.7 Flash, Gemini 3.6 Flash, Gemini 3.5 Flash-Lite, Grok 4.6, and the documented DeepSeek V4 effort levels without constructing unsupported payloads by hand.

The change also closes lifecycle gaps for model keys already exposed by AgentRules. Saved keys remain loadable, but retired OpenAI Codex and o4-mini choices resolve through the centralized deprecation map to active direct-API presets. Codex itself continues to discover models and effort values from app-server `model/list`; this plan deliberately does not turn a moving local runtime catalog into a hard-coded API registry.

An operator can verify the result by opening the model picker, filtering each direct provider, and observing the new model families and effort-specific labels. Automated contract tests will prove that every new preset resolves to the intended provider, wire model, context limit, and provider-native thinking value. Lifecycle tests will prove that compatibility keys redirect to registered canonical presets. Existing project defaults remain GPT-5.6 Sol and existing explicit saved keys continue to load.

## Scope

### In Scope

- Add direct Anthropic presets for `claude-opus-5`, including an explicit non-thinking choice and adaptive-thinking choices at low, medium, high, xhigh, and max effort.
- Move the generic direct Anthropic keys `claude-opus` and `claude-opus-reasoning` to Opus 5 while preserving all pinned Opus 4.8 keys as rollback choices.
- Add direct Gemini presets for `gemini-3.7-flash`, `gemini-3.6-flash`, and `gemini-3.5-flash-lite`, with only the thinking levels each family accepts.
- Add direct xAI presets for `grok-4.6` at low, medium, high/default, and xhigh effort; make Grok 4.6 the default model used by a directly constructed `XaiArchitect`.
- Add DeepSeek V4 low-effort support for Flash and Pro, max support for Flash, and explicit fail-fast handling for unsupported effort values.
- Preserve DeepSeek's 32,000-token application output safety cap while documenting that it is intentionally lower than the current upstream maximum.
- Add deprecation redirects for exposed OpenAI `o4-mini`, `gpt-5.1-codex`, and `gpt-5.2-codex` compatibility keys, including their static Codex-derived counterparts where applicable.
- Add GPT-5 Mini low and medium presets so the low/medium/high o4-mini compatibility keys can migrate without collapsing their workload role.
- Update model-picker labels, lifecycle documentation, unit tests, cross-provider contract tests, and optional live-smoke model selection.
- Reconfirm upstream facts at the start of implementation and record any catalog drift in this plan before changing code.

### Out of Scope

- Do not add static GPT-5.6 Codex presets. Codex models and efforts remain app-server catalog data.
- Do not add a pinned Claude Code Opus 5 preset until the exact resolved Claude Code executable has a documented minimum-version gate. The moving `opus` alias remains runtime-owned.
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
| OpenAI | GPT-5.6 Sol/Terra/Luna are already represented. `o4-mini` is deprecated and succeeded by GPT-5 Mini. `gpt-5.1-codex` and `gpt-5.2-codex` are deprecated while `gpt-5.3-codex` remains the active compatibility target. | Add lifecycle redirects only; do not synthesize new static Codex models. |

## Progress

- [x] (2026-08-29) Created branch `codex/provider-model-refresh-2026-08` from a clean `main` worktree.
- [x] (2026-08-29) Captured the upstream catalog audit and baseline test result: 166 tests plus 8 subtests passed across the targeted provider suite.
- [x] (2026-08-29) Created this ExecPlan and five milestone documents through the AgentRules CLI.
- [x] (2026-08-29) User reviewed and approved this plan and authorized sequential milestone execution.
- [x] (2026-08-29) MS001 locked the implementation-day source snapshot and migration contract; targeted baseline passed with 166 tests and 8 subtests.
- [x] (2026-08-29) MS002 added Opus 5 and current Gemini Flash families with exact capability validation; 232 tests and 5 subtests passed with lint, types, and import smoke green.
- [x] (2026-08-29) MS003 added Grok 4.6 and completed DeepSeek V4 effort handling; 204 tests and 10 subtests passed with lint, types, and import smoke green.
- [x] (2026-08-29) MS004 added effort-preserving OpenAI lifecycle redirects and hardened the Codex ownership boundary; 260 tests and 43 subtests passed with lint, types, and import smoke green.
- [ ] MS005 completes integrated validation and release documentation.
- [ ] ExecPlan and milestones are completed through the CLI after all acceptance criteria pass.

## Surprises & Discoveries

- The repository already contains GPT-5.6 Sol, Terra, and Luna direct-API presets and robust dynamic Codex model discovery. The OpenAI work is lifecycle maintenance, not a GPT-5.6 registry addition.
- Gemini capability profiles use prefix matching. `gemini-3.5-flash-lite` must be declared before `gemini-3.5-flash`, or the more specific family will inherit the wrong thinking contract.
- DeepSeek's request helper currently reduces every enabled mode except xhigh/max to `high`. Adding low support therefore requires request validation, not only new constants and labels.
- xAI's current direct-architect default is `grok-4.5`, and its context-limit logic names that family explicitly. Adding only a preset would leave constructor behavior and token packing stale.
- Existing static Codex-derived presets predate runtime catalog discovery. They are compatibility surfaces; new runtime models must continue to come from `model/list`.
- Official OpenAI documentation now marks o4-mini as deprecated and identifies GPT-5 Mini as its successor. Preserving low/medium/high intent requires two new GPT-5 Mini configurations rather than redirecting all three old keys to one high-effort preset.
- DeepSeek's current Thinking Mode guide documents compatibility mappings that were not captured in the planning draft: requested `medium` and `xhigh` both map to actual `high`, while only `max` maps to `max`. MS003 was amended to implement and test that provider-defined behavior; only `minimal` remains unsupported.
- Exact Gemini thinking contracts also require exact SDK enum support. The initial implementation still inherited the older nearest-enum fallback; the MS002 audit caught this and changed current Flash families to fail closed when the installed SDK lacks a required level.
- Moving the xAI constructor default is not sufficient by itself: the previous Grok 4.5 picker label also claimed to be recommended. MS003 now labels Grok 4.6 as recommended and Grok 4.5 as the explicit fallback.
- The pre-existing static Codex GPT-5.6 negative test inspected `BASE_MODEL_PRESETS`, which never contains Codex-derived entries. MS004 changed it to inspect the combined `MODEL_PRESETS` registry, so it can fail if a static Codex GPT-5.6 key is actually introduced.

## Decision Log

- Decision: Treat direct API providers and local runtime providers as separate ownership domains.
  Rationale: Anthropic, Gemini, xAI, DeepSeek, and direct OpenAI have reviewed static registries. Codex and Claude Code resolve moving models from installed runtimes and account policy.
  Date/Author: 2026-08-29 / @codex

- Decision: Preserve every existing saved preset key and route retired endpoints through `DEPRECATED_PRESETS`.
  Rationale: Preset keys are public compatibility IDs. Removing or silently invalidating them would break stored configuration before the operator can select a replacement.
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

## Outcomes & Retrospective

Planning outcome: the work is divided into five bounded milestones with explicit model contracts, compatibility migrations, non-goals, validation commands, and recovery behavior. No provider implementation has been changed yet.

When implementation is complete, replace this paragraph with the shipped preset keys, final test counts, any upstream drift, rollback notes, and deferred follow-up issues. Record whether optional live smokes were run; never imply live coverage when only mocked/unit coverage ran.

## Context and Orientation

`src/agentrules/core/types/models.py` defines immutable `ModelConfig` values. A config carries provider identity, wire model name, generic `ReasoningMode`, optional provider-specific effort, and context-estimation metadata. New public configurations start here.

`src/agentrules/config/agents.py` turns configs into labeled `BASE_MODEL_PRESETS`, attaches conservative input limits in `_apply_model_limits`, derives compatibility presets for Codex and Claude Code, and defines phase defaults. The direct-provider picker consumes these entries. Phase defaults must remain `gpt56-sol-default` throughout this plan.

`src/agentrules/core/configuration/model_presets.py` is the compatibility boundary. `DEPRECATED_PRESETS` maps a saved public key to a registered canonical replacement, and `resolve_runtime_preset_key()` performs that redirect before config lookup. A redirect is valid only when both old and replacement keys remain present in `MODEL_PRESETS`.

Provider-native capability metadata lives near each adapter: Anthropic and Gemini use immutable profile tuples, while xAI and DeepSeek use immutable `ModelDefaults` maps. Request builders translate a generic reasoning mode immediately before dispatch. The static registry and request-time translation must agree; a model must never appear in the picker if the adapter cannot construct its supported payload.

`tests/unit/test_provider_model_compatibility_matrix.py` is the end-to-end static contract. Each row checks preset key, provider, model name, generic reasoning mode, context window, and provider-native wire reasoning. Provider-specific tests cover edge cases and invalid combinations. `tests/live/test_provider_model_live_smoke.py` is optional and gated; it is not part of the default acceptance path.

`docs/provider-model-lifecycle.md` records behavior that a model ID alone cannot communicate: moving aliases, retired compatibility keys, fallback rules, thinking constraints, local-runtime ownership, and live-smoke gates.

## Plan of Work

First, execute MS001. Reopen the official source pages listed in Artifacts and Notes, confirm that the dated contract table is still correct, run the targeted baseline, and update this plan's Decision Log if any fact moved. This milestone does not expose new models; it prevents implementation against a stale catalog.

Second, execute MS002 as a complete direct-provider slice. Add Opus 5 and the three Gemini families to immutable configs, capability profiles, labels, input-limit classification, and tests in one milestone. Ensure specific Gemini prefixes precede broader ones. Update generic Opus keys only after pinned Opus 5 presets and request tests pass. Do not create pinned Claude Code Opus 5 presets.

Third, execute MS003. Add Grok 4.6 to config defaults, preset labels, constructor defaults, context limits, and request validation. Add DeepSeek low/max configurations and replace the current implicit effort coercion with explicit supported mappings and errors. Leave the DeepSeek wire model IDs and 32K application output cap unchanged.

Fourth, execute MS004. Add GPT-5 Mini low/medium configurations and use them as effort-preserving replacements for o4-mini saved keys. Register direct and static-Codex compatibility redirects for deprecated Codex model IDs. Add regression tests proving that Codex runtime catalog entries—including unknown future effort tokens—remain dynamic and that no static GPT-5.6 Codex preset is introduced.

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
- Grok 4.6 resolves to a 500,000-token context, accepts exactly low/medium/high/xhigh, rejects disabled/minimal, and is the default for direct `XaiArchitect` construction.
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

- `.agent/exec_plans/active/provider-model-refresh/EP-20260829-001_provider-model-refresh.md`
- `.agent/exec_plans/active/provider-model-refresh/milestones/complete/MS001_lock-model-contracts-and-lifecycle-policy.md`
- `.agent/exec_plans/active/provider-model-refresh/milestones/complete/MS002_refresh-anthropic-and-gemini-model-families.md`
- `.agent/exec_plans/active/provider-model-refresh/milestones/complete/MS003_refresh-xai-and-deepseek-capabilities.md`
- `.agent/exec_plans/active/provider-model-refresh/milestones/complete/MS004_harden-openai-lifecycle-and-codex-runtime-boundaries.md`
- `.agent/exec_plans/active/provider-model-refresh/milestones/active/MS005_validate-integration-and-release-readiness.md`

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
