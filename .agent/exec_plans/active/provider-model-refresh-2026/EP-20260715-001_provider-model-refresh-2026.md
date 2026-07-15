---
id: EP-20260715-001
title: "Refresh AI provider models for 2026"
status: active
kind: migration
domain: cross-cutting
owner: "@codex"
created: 2026-07-15
updated: 2026-07-15
tags: [providers, models, lifecycle, compatibility]
touches: [api, cli, agents, tests, docs]
risk: high
breaking: false
migration: true
links:
  issue: ""
  pr: ""
  docs: ".agent/exec_plans/active/provider-model-refresh-2026/milestones/active"
depends_on: []
supersedes: []
---

# EP-20260715-001 - Refresh AI provider models for 2026

This ExecPlan is a living document. Keep `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` up to date as work proceeds. Maintain this document in accordance with `.agent/PLANS.md`.

## Purpose / Big Picture

AgentRules users should be able to select the current generally available models from OpenAI, Anthropic, DeepSeek, Google, and xAI without sending invalid request fields, underestimating context limits, or depending on provider aliases that have already retired. Users of the local Codex and Claude Code runtimes should also be able to choose deliberately between runtime-managed model selection, which follows the installed runtime and account, and pinned model identifiers, which favor reproducibility.

After this plan is implemented, new configurations will default to OpenAI GPT-5.6 Sol instead of GPT-5.5, DeepSeek configurations will use V4 before the legacy aliases are removed, Claude Sonnet 5 and Fable 5 will honor their thinking and refusal contracts, xAI users will have Grok 4.5 and the specialized Grok 4.20 variants, Gemini users will see accurate lifecycle guidance, and Codex will retain model-list options it does not yet know by name. A reviewer can verify the result in the interactive model picker, in provider request-builder tests, through the offline pipeline smoke test, and with optional explicitly gated live smokes.

This plan intentionally stops at planning until the user approves it. No provider implementation work begins merely because this document exists.

## Scope

In scope are the active providers represented by `ModelProvider`: direct Anthropic, Claude Code, direct OpenAI, Codex, DeepSeek, Gemini, and xAI. The work includes model constants, preset definitions, default phase selections, context-window metadata, provider capability metadata, request construction, response/refusal parsing where a new model changes the response contract, local-runtime discovery and version gating, dependency and lockfile updates required by those contracts, migration behavior for saved preset keys, focused and integration tests, operator documentation, and snapshot synchronization.

The direct-provider additions are `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`, `claude-sonnet-5`, `claude-fable-5`, `deepseek-v4-pro`, `deepseek-v4-flash`, `grok-4.5`, `grok-4.20-0309-reasoning`, `grok-4.20-0309-non-reasoning`, and `grok-4.20-multi-agent-0309`. Gemini 3.5 Flash is already implemented and is not re-added.

Out of scope are image, audio, video, embedding, translation, and realtime-only model families; Anthropic's invitation-only Mythos models; OpenAI GPT-5.6 pro mode; server-side web/search tool integrations that AgentRules does not currently expose; a generic provider catalog service; changes to API-key storage; and unrelated provider refactors. Optional live smokes must remain opt-in and must never make default CI depend on credentials or paid provider calls.

## Context and Orientation

`src/agentrules/core/types/models.py` defines immutable `ModelConfig` values and the shared `ReasoningMode` enum is in `src/agentrules/core/agents/base.py`. `src/agentrules/config/agents.py` turns model configs into user-facing presets, attaches context limits, and selects the default preset for every analysis phase. Saved CLI configuration stores preset keys, so deleting or silently invalidating an existing key can break an existing installation even when the Python code still imports.

Each direct API provider has a thin adapter under `src/agentrules/core/agents/<provider>/`. The provider's `config.py` resolves model-family defaults, `request_builder.py` converts AgentRules configuration into the provider's wire payload, `response_parser.py` extracts text and tool calls, and `architect.py` orchestrates the request. Capability differences should be centralized in provider capability metadata rather than scattered string checks.

Codex is different from the direct OpenAI provider. `src/agentrules/core/agents/codex/client.py` asks the installed app-server for `model/list`, and `src/agentrules/core/configuration/model_presets.py` builds model choices from that runtime response. Claude Code is also a local runtime, but the current implementation builds a static preset list and explicitly sends `options["model"]`; `src/agentrules/core/configuration/services/claude_code.py` prefers the Claude Agent SDK's bundled executable over a `claude` command found on `PATH`.

The provider audit performed on 2026-07-15 established these upstream contracts, which are repeated here so implementation does not depend on conversational context:

- DeepSeek's `deepseek-chat` and `deepseek-reasoner` aliases become inaccessible after 2026-07-24 15:59 UTC. `deepseek-v4-pro` and `deepseek-v4-flash` both have a 1,000,000-token context, support thinking and non-thinking modes on the same model identifier, default to thinking enabled, accept `reasoning_effort` values `high` and `max`, and support tool calls in thinking mode. The OpenAI-compatible SDK carries the thinking toggle in `extra_body={"thinking": {"type": "enabled" | "disabled"}}`.
- OpenAI GPT-5.6 has three explicit tiers. `gpt-5.6-sol` is the flagship and the `gpt-5.6` alias routes to it; `gpt-5.6-terra` is the balanced cost tier; and `gpt-5.6-luna` is the high-volume tier. The direct provider uses the Responses API. GPT-5.6 supports reasoning through `max`, while the repository currently models efforts only through `xhigh` and assumes a 400,000-token GPT-5 context.
- Anthropic's current public additions are `claude-sonnet-5` and `claude-fable-5`. Both use a 1,000,000-token context and adaptive thinking. Fable thinking cannot be disabled, supports effort values through `max`, and can return HTTP 200 with `stop_reason="refusal"`; Fable is unavailable under zero-data-retention arrangements and has a 30-day retention requirement. Sonnet 5 no longer accepts fixed manual thinking budgets and must be explicitly disabled if a non-thinking request is desired. Claude Opus 4.1 is deprecated and retires on 2026-08-05; the generic existing Opus preset should no longer select it.
- Claude Code can follow moving model aliases such as `default`, `best`, `sonnet`, `opus`, and `fable`, but full model identifiers remain pinned. Fable 5 requires Claude Code 2.1.170 or newer and Sonnet 5 requires 2.1.197 or newer. The currently locked Claude Agent SDK bundles Claude Code 2.1.161 in this workspace, while a newer global CLI does not take precedence. The two-second version-probe timeout has already returned `None` locally and can bypass version gates.
- Gemini 3.5 Flash already exists as the stable `gemini-3.5-flash` preset. Gemini 2.5 Flash and Pro are scheduled to shut down on 2026-10-16. The Gemini 3.1 Flash-Lite preview endpoint is already shut down, so it must not remain an apparently selectable dead endpoint even though its saved preset key should continue to load.
- xAI's recommended general and coding model is `grok-4.5`, with a 500,000-token context and only `low`, `medium`, and `high` reasoning efforts, defaulting to `high`. The Grok 4.20 reasoning, non-reasoning, and multi-agent variants use a 1,000,000-token context and remain specialized choices. Grok 4.3 remains available and is not removed.
- The local Codex runtime already returned GPT-5.6 Sol, Terra, and Luna from `model/list`; therefore Codex model identifiers must remain runtime-owned. The same catalog returned effort labels `max` and `ultra`, which the current closed literal silently normalizes to `None`.

## Compatibility and Migration Policy

Existing preset keys remain resolvable. When an upstream wire identifier is retired, a compatibility preset key may be redirected to its documented replacement if the old and new behavior can be represented explicitly. In particular, `deepseek-chat` should resolve to V4 Flash with thinking disabled, `deepseek-reasoner` should resolve to V4 Flash with thinking enabled at high effort, the generic Claude Opus key should advance from Opus 4.1 to Opus 4.8, and the retired Gemini 3.1 Flash-Lite preview key should resolve to the stable Flash-Lite model. The label and description must disclose every such redirect.

Canonical, explicit model presets are preferred for direct API providers because they make behavior and billing auditable. Runtime providers additionally expose runtime-managed choices. Claude Code will keep pinned full-ID presets and add alias-based presets for users who deliberately want automatic model movement. Codex will continue to consume the live catalog and will not gain duplicated static GPT-5.6 entries.

Changing `MODEL_PRESET_DEFAULTS` to GPT-5.6 Sol affects only new/default configurations and phases without an explicit override. Existing explicit preset selections continue to resolve. Legacy GPT-5.5 presets remain available until a separate deprecation plan supplies evidence for removal.

## Milestones

Milestone 1, `EP-20260715-001/MS001 Migrate DeepSeek to V4 before legacy retirement`, is the time-critical slice. It adds V4 Pro and Flash, explicit thinking and effort payloads, 1M context metadata, thinking-mode tool support, and compatibility redirects for the two retiring preset keys. It must land first because the legacy wire identifiers stop working on 2026-07-24.

Milestone 2, `EP-20260715-001/MS002 Add OpenAI GPT-5.6 model family`, adds Sol, Terra, and Luna to the direct OpenAI Responses path, adds `max` as a first-class direct reasoning effort, corrects context metadata, updates the OpenAI SDK lock if required by the typed request contract, and advances new/default AgentRules phases to the Sol preset without removing GPT-5.5.

Milestone 3, `EP-20260715-001/MS003 Add Claude Sonnet 5 and Fable 5 safely`, adds the direct Anthropic model families with capability-driven thinking policy, explicit non-thinking behavior where allowed, structured-output support, typed refusal handling, retention guidance, and an Opus 4.1 migration. It must prove that Fable can never be configured as a fake non-thinking preset.

Milestone 4, `EP-20260715-001/MS004 Modernize Claude Code model selection and runtime gating`, adds pinned Sonnet 5 and Fable 5 choices plus runtime-managed aliases, upgrades the Claude Agent SDK to a release whose bundled executable meets the Sonnet 5 minimum, fixes the unreliable version probe, and documents when user-installed Claude Code does and does not control AgentRules behavior.

Milestone 5, `EP-20260715-001/MS005 Add xAI Grok 4.5 and 4.20 model families`, adds Grok 4.5 as the recommended general xAI preset, adds explicit specialized Grok 4.20 variants, replaces the boolean xAI reasoning-support flag with model-specific accepted efforts, and assigns exact 500k/1M context limits without removing Grok 4.3.

Milestone 6, `EP-20260715-001/MS006 Preserve dynamic Codex compatibility and update Gemini lifecycle`, keeps Codex runtime-owned while preventing new catalog effort labels from being silently discarded, adds fixtures for `max`, `ultra`, and a future unknown-but-safe effort token, and updates Gemini labels and compatibility redirects without reimplementing Gemini 3.5 Flash.

Milestone 7, `EP-20260715-001/MS007 Complete cross-provider validation documentation and rollout`, performs the cross-provider regression pass, refreshes dependency locks and documentation coherently, adds or updates opt-in live smokes, runs the complete quality gates, synchronizes `SNAPSHOT.md`, updates the ExecPlan registry, and records final rollout and rollback evidence.

Each milestone has a detailed file under `.agent/exec_plans/active/provider-model-refresh-2026/milestones/active/`. Complete milestone files with `agentrules execplan milestone complete EP-20260715-001 --ms <N>` only after their Definition of Done is satisfied.

## Progress

- [x] (2026-07-15 America/New_York) Audited the repository's active model registry, provider adapters, runtime discovery paths, dependency lock, and focused provider tests.
- [x] (2026-07-15 America/New_York) Verified current model identifiers, capabilities, runtime minimums, and retirement dates against official provider documentation.
- [x] (2026-07-15 America/New_York) Created branch `codex/provider-model-refresh-2026` from a clean `main` worktree.
- [x] (2026-07-15 America/New_York) Created this ExecPlan and seven milestone files with the repository CLI.
- [x] (2026-07-15 America/New_York) Drafted the implementation, compatibility, validation, rollout, and recovery strategy for review.
- [x] (2026-07-15 America/New_York) User approved the full ExecPlan and directed sequential milestone implementation, validation, archival, and commits.
- [x] (2026-07-15 America/New_York) MS001 completed: DeepSeek V4 migration, compatibility redirects, and focused validation are green.
- [x] (2026-07-15 America/New_York) MS002 completed: GPT-5.6 direct presets, max effort, 1.05M context, Sol defaults, and SDK 2.45.0 are validated.
- [x] (2026-07-15 America/New_York) MS003 completed: direct Claude 5 capability policies, safe refusal handling, Opus 4.8 migration, and lifecycle guidance are validated.
- [ ] Complete MS001 through MS007 in order, keeping this plan and each milestone current.
- [ ] Complete full validation and record exact evidence.
- [ ] Mark the ExecPlan done only after every acceptance condition is met.

## Surprises & Discoveries

- Observation: The highest-risk deadline was not one of the initially named providers.
  Evidence: DeepSeek states that the only two identifiers currently present in AgentRules become inaccessible on 2026-07-24, nine days after this plan was created.
- Observation: Codex already discovers the OpenAI GPT-5.6 family correctly without a registry change.
  Evidence: A local app-server `model/list` diagnostic returned GPT-5.6 Sol, Terra, and Luna and marked Sol as the runtime default.
- Observation: Codex discovery is model-dynamic but not fully capability-dynamic.
  Evidence: The live catalog returned `max` and `ultra`, while `CodexRuntimeReasoningEffort` accepts only `none`, `minimal`, `low`, `medium`, `high`, and `xhigh`, causing the newer values to be dropped.
- Observation: AgentRules does not necessarily use the Claude Code version installed by the user.
  Evidence: executable resolution prefers the SDK-bundled binary; this workspace resolves version 2.1.161 even though the global command reports 2.1.207.
- Observation: The Claude Code version probe can fail open.
  Evidence: the bundled binary took longer than the hard-coded two-second timeout locally, the probe returned `None`, and model support validation treats an unknown version as allowed.
- Observation: Gemini 3.5 Flash was already added in an earlier model refresh.
  Evidence: both the `GEMINI_3_5_FLASH` config and the stable `gemini-3.5-flash` preset are present and their focused capability tests pass.
- Observation: The existing provider baseline is healthy.
  Evidence: 129 focused OpenAI, Anthropic, Claude Code, Codex, DeepSeek, Gemini, xAI, and model-override tests passed before planning changes.
- Observation: DeepSeek tool iterations do not replay provider-native assistant messages.
  Evidence: Phase 1 reconstructs each follow-up from `base_context` plus normalized `tool_feedback`; therefore V4 `reasoning_content` is parsed for reporting but is not required as continuation history.
- Observation: GPT-5.6 support required an SDK floor, not only registry changes.
  Evidence: OpenAI SDK 2.21.0 typed reasoning efforts only through `xhigh`; SDK 2.45.0 includes `max` and remains compatible with the DeepSeek and xAI regression suites.
- Observation: Fable 5's canonical request shape differs from Sonnet 5 even though both always use adaptive thinking in normal operation.
  Evidence: Anthropic documents omission of `thinking` as the canonical Fable request; Sonnet 5 requires an explicit disabled payload when reasoning is turned off.
- Observation: The locked Anthropic SDK already exposes refusal stop reasons but does not type every refusal detail field.
  Evidence: SDK 0.83.0 types `stop_reason="refusal"`; the implementation safely duck-types bounded `stop_details` fields without requiring a dependency update.

## Decision Log

- Decision: Implement DeepSeek as the first milestone.
  Rationale: its existing identifiers have the only near-term hard shutdown and require request-shape changes, not just new constants.
  Date/Author: 2026-07-15 / @codex
- Decision: Preserve saved preset keys and redirect retired identifiers when semantics can be represented explicitly.
  Rationale: configuration compatibility is more useful than preserving a wire slug that will fail, provided the UI clearly discloses the redirect.
  Date/Author: 2026-07-15 / @codex
- Decision: Use explicit direct-provider model IDs but expose both pinned and moving aliases for Claude Code.
  Rationale: direct API behavior should be auditable, while local-runtime users need an intentional way to follow account- and runtime-specific recommendations.
  Date/Author: 2026-07-15 / @codex
- Decision: Keep Codex model discovery runtime-owned and make its effort parsing forward-compatible.
  Rationale: duplicating GPT-5.6 in the static registry would drift from the installed runtime and account, but silently dropping catalog capabilities is also incorrect.
  Date/Author: 2026-07-15 / @codex
- Decision: Change new/default phase selection to GPT-5.6 Sol while retaining GPT-5.5 presets.
  Rationale: new users should receive the current flagship, while existing explicit configuration must continue to load and behave predictably.
  Date/Author: 2026-07-15 / @codex
- Decision: Model provider capability contracts explicitly instead of relying on prefix-wide fallbacks or booleans.
  Rationale: Fable thinking, xAI reasoning efforts, DeepSeek dual thinking modes, and per-model context windows differ in ways that a single provider-wide default cannot safely express.
  Date/Author: 2026-07-15 / @codex
- Decision: Do not add Mythos, OpenAI pro mode, or non-text model families in this plan.
  Rationale: they are invitation-only, optional request modes, or outside AgentRules' text-analysis architecture and would expand the migration without helping the agreed provider refresh.
  Date/Author: 2026-07-15 / @codex
- Decision: Execute milestones sequentially and commit only after each milestone is validated and archived.
  Rationale: The user explicitly approved this delivery workflow so every provider slice remains independently reviewable and recoverable.
  Date/Author: 2026-07-15 / @codex
- Decision: Represent Anthropic thinking behavior with an explicit provider-local policy and reject impossible Fable configurations before dispatch.
  Rationale: Sonnet 5, Fable 5, and older Claude families require materially different omission, disable, adaptive, and manual-budget wire shapes that booleans cannot express safely.
  Date/Author: 2026-07-15 / @codex

## Outcomes & Retrospective

Planning is complete and implementation is active under the user's approved sequential-milestone workflow. No outcome is claimed until each milestone's validation evidence is recorded. When the plan is complete, replace this paragraph with a comparison of shipped behavior against the Purpose section, exact test and live-smoke evidence, dependency versions chosen, compatibility redirects applied, remaining model-lifecycle risks, and any follow-up work intentionally deferred.

## Plan of Work

Implement MS001 first and keep it isolated enough to release before the DeepSeek retirement deadline. Add V4 model configs and canonical presets, redirect legacy DeepSeek preset keys, update `ModelDefaults` so thinking mode and accepted efforts are explicit, construct the documented `extra_body.thinking` payload, permit tools in V4 thinking mode, and add request/response/config/preset tests before touching another provider.

Implement MS002 and MS003 as separate direct-provider changes. OpenAI work updates the shared direct reasoning enum only as needed for `max`, then adds GPT-5.6-specific request support, context limits, presets, and the new default. Anthropic work evolves `CapabilityProfile` to encode default thinking and whether it can be disabled, adds Sonnet 5 and Fable 5, handles HTTP-200 refusals explicitly, and updates generic Opus selections away from the retiring model. Do not conflate these SDK contracts merely because both use reasoning labels.

Implement MS004 after the direct Anthropic capability matrix is stable so Claude Code can reuse it where the wire semantics match. Keep pinned presets, add runtime alias presets, upgrade and verify the SDK-bundled CLI, and make version detection fail closed for model gates when an explicit minimum is known. Do not assume a global `claude update` changes the bundled runtime.

Implement MS005 independently in the xAI adapter. Replace `reasoning_effort_supported: bool` with an immutable set of accepted values or an equivalent explicit representation, so Grok 4.5 can reject `none` while Grok 4.3 keeps its existing behavior. Add exact context metadata and specialized 4.20 presets without making the beta multi-agent model the default.

Implement MS006 as a compatibility maintenance slice. Allow safe runtime-supplied Codex effort tokens, order known labels predictably, preserve unknown safe values instead of dropping them, and add catalog fixtures. Update Gemini's user-facing lifecycle state and redirect only endpoints that are already shut down; keep still-operational 2.5 IDs selectable but visibly deprecated until their scheduled shutdown.

Finish with MS007. Search the entire repository for stale model names, update docs and `AGENTS.md` where the provider architecture guidance materially changed, refresh the lock once after all dependency decisions are known, add gated live coverage without changing offline CI, run every quality gate, synchronize snapshots, update plan documents and registry metadata, and prepare a concise rollback record.

## Concrete Steps

All commands run from `/Volumes/AGENAI/Coding/public-github/agentrules-architect`.

Before each milestone, confirm scope and cleanliness:

    git status --short --branch
    .venv/bin/agentrules execplan milestone list EP-20260715-001 --active-only

Run focused tests during the relevant milestones:

    .venv/bin/python -m pytest -q tests/unit/agents/test_deepseek_helpers.py tests/unit/test_agents_deepseek.py tests/unit/agents/test_deepseek_agent_parsing.py tests/unit/test_model_overrides.py
    .venv/bin/python -m pytest -q tests/test_openai_responses.py tests/unit/agents/test_openai_helpers.py tests/unit/test_agents_openai_params.py tests/unit/test_model_overrides.py
    .venv/bin/python -m pytest -q tests/unit/agents/test_anthropic_capabilities.py tests/unit/agents/test_anthropic_request_builder.py tests/unit/agents/test_anthropic_agent_parsing.py tests/unit/test_model_overrides.py
    .venv/bin/python -m pytest -q tests/unit/agents/test_claude_code_request_builder.py tests/unit/agents/test_claude_code_response_parser.py tests/unit/test_cli_claude_code_settings.py
    .venv/bin/python -m pytest -q tests/unit/agents/test_xai_helpers.py tests/unit/test_model_overrides.py
    .venv/bin/python -m pytest -q tests/unit/agents/test_codex_client.py tests/unit/test_codex_runtime_service.py tests/unit/test_cli_codex_settings.py tests/unit/agents/test_gemini_capabilities.py tests/unit/test_model_overrides.py

After dependency changes, regenerate rather than hand-edit the lock and resynchronize the environment:

    uv lock
    uv sync --extra dev

At integration, run the repository-wide gates:

    .venv/bin/python -c "import agentrules; print(agentrules.__file__)"
    .venv/bin/python -m pytest -q
    .venv/bin/ruff check src tests
    .venv/bin/pyright
    .venv/bin/agentrules snapshot sync
    .venv/bin/agentrules execplan-registry update

The expected result is a successful import, a zero-exit full test suite, no Ruff or Pyright findings, an idempotent second snapshot sync with no further diff, and a registry entry whose status and paths match this active plan. Optional live smokes run only when their documented environment flags and credentials are explicitly present; skips are the correct default result.

## Validation and Acceptance

The interactive model picker must show canonical new direct-provider presets, preserve documented legacy keys, label deprecated choices accurately, and show Claude Code runtime-managed aliases separately from pinned model IDs. A fresh/default configuration must select GPT-5.6 Sol, while a configuration explicitly using GPT-5.5 must still load.

Request-builder tests must assert exact wire payloads. DeepSeek V4 thinking requests contain `extra_body.thinking.type="enabled"` and an accepted effort, non-thinking requests contain `type="disabled"`, and both can carry tools. GPT-5.6 requests use the Responses path and preserve `max` rather than reducing it to `high`. Fable requests always use adaptive thinking and reject a disabled-thinking configuration before network I/O. Sonnet 5 sends explicit disabled thinking when requested. Grok 4.5 never sends `reasoning_effort="none"`. Codex catalog tests retain `max`, `ultra`, and a future safe token.

Response tests must prove that an Anthropic `stop_reason="refusal"` becomes an actionable AgentRules error result rather than empty findings or false success. Existing non-refusal Claude responses, older model families, structured outputs, tool calls, and streaming behavior must remain green.

Context-limit tests must prove exact model-specific limits: 1,000,000 for DeepSeek V4 and current Claude 5 families, 500,000 for Grok 4.5, 1,000,000 for the selected Grok 4.20 variants, and the official GPT-5.6 value captured during MS002. No new model may fall through to a smaller provider-wide default silently.

Claude Code diagnostics must report the executable actually used and its parsed version. A bundled executable below a model's minimum must make that pinned model unavailable with an actionable explanation; a probe failure must not silently claim support. Alias presets must be documented as moving choices and pinned presets as reproducible choices.

No acceptance condition requires live credentials. When maintainers opt into live smokes, each request must use a minimal prompt and token cap, report only model/contract evidence without logging credentials or full provider responses, and skip cleanly when the provider is unavailable to the account or region.

## Idempotence and Recovery

Model and preset additions are declarative and safe to reapply. Registry and snapshot commands must be idempotent. Lockfile changes must be produced by `uv lock`, never manually edited, so rerunning the resolver recovers from an interrupted update.

Each milestone should be committed separately after its own tests pass. If a milestone regresses another provider, revert only that milestone's commit and leave earlier verified milestones intact. Do not use destructive worktree commands; preserve unrelated user changes if they appear.

If the GPT-5.6 SDK contract requires a dependency version that conflicts with DeepSeek's OpenAI-compatible client, keep the shared SDK at the newer compatible version and validate both builders before proceeding. If no compatible version exists, pause MS002, record the exact signature conflict, and keep MS001 releasable rather than blocking the DeepSeek deadline.

If the Claude Agent SDK cannot provide a bundled Claude Code version new enough for Sonnet 5, retain the runtime aliases and existing pinned presets, hide unsupported pinned Claude 5 choices with an explicit diagnostic, and record the external dependency as a blocker. Do not bypass the minimum-version gate or assume the global binary is used.

If an upstream live smoke rejects a documented model for account, region, or retention-policy reasons, distinguish availability from request-shape failure. Keep offline contract tests authoritative, document the availability condition, and do not weaken Fable safety or retention checks to force a smoke to pass.

## Artifacts and Notes

The pre-implementation focused baseline was:

    129 passed in 3.23s

The local runtime audit observed:

    Codex: gpt-5.6-sol (default), gpt-5.6-terra, gpt-5.6-luna
    Codex efforts included: low, medium, high, xhigh, max, ultra
    Claude Code SDK-bundled executable: 2.1.161
    Claude Code global executable: 2.1.207

These observations are diagnostics, not hard-coded production defaults. Runtime catalogs and installed versions remain environment-specific.

## Interfaces and Dependencies

In `src/agentrules/core/agents/base.py`, extend `ReasoningMode` with a direct `MAX = "max"` member only if MS002 confirms it is needed by shared preset configuration. Do not add `ultra` to this provider-neutral enum; Codex owns that runtime-specific label.

In `src/agentrules/core/agents/deepseek/config.py`, `ModelDefaults` must describe whether a model supports the explicit thinking toggle, its default reasoning mode, accepted effort values, output-token policy, and tools. `prepare_request()` in `deepseek/request_builder.py` must remain a pure payload builder and place the thinking toggle in `extra_body`.

In `src/agentrules/core/agents/anthropic/capabilities.py`, evolve `CapabilityProfile` so callers can distinguish a family whose default is non-thinking, a family that defaults to adaptive but permits explicit disable, and Fable's always-adaptive policy. Keep effort and structured-output capabilities in the same centralized profile. Define a provider-specific error type under `src/agentrules/core/agents/anthropic/errors.py` if refusal handling needs an exception boundary; the error message must include the stop reason and safe stop-detail summary without exposing hidden reasoning.

In `src/agentrules/core/agents/xai/config.py`, replace the boolean reasoning-effort flag with an immutable set such as `accepted_reasoning_efforts: frozenset[str]`. `xai/request_builder.py` must validate the mapped value against that set before adding it to the payload.

In `src/agentrules/core/configuration/model_presets.py`, Codex runtime effort values must remain normalized strings sourced from the live catalog. Accept only a short lowercase ASCII token with letters, numbers, `_`, or `-`; reject malformed values, order known values predictably, and preserve safe unknown catalog values after the known values. Static AgentRules reasoning modes continue to map only to values they understand.

The committed dependency constraints in `pyproject.toml` and resolved versions in `uv.lock` must agree. The OpenAI SDK selected in MS002 must accept the final GPT-5.6 request fields used by AgentRules. The Claude Agent SDK selected in MS004 must be verified by executing its bundled binary with `--version`; package version alone is not sufficient evidence.

## Revision Note

2026-07-15: Replaced the generated skeleton with the initial review-ready plan. The revision records the provider audit, compatibility policy, seven ordered milestones, exact validation gates, runtime-specific recovery paths, and the explicit approval boundary requested by the user.
