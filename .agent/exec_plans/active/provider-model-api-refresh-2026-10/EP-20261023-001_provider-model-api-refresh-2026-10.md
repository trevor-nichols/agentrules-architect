---
id: EP-20261023-001
title: "Refresh provider models and API contracts after October 2026 audit"
status: planned
kind: refactor
domain: cross-cutting
owner: "@codex"
created: 2026-10-23
updated: 2026-10-23
tags: [providers, models, capabilities, lifecycle]
touches: [api, cli, agents, docs, tests]
risk: high
breaking: false
migration: true
links:
  issue: ""
  pr: "https://github.com/trevor-nichols/agentrules-architect/pull/42"
  docs: "docs/provider-model-audit-2026-10.md"
depends_on: []
supersedes: []
---

# EP-20261023-001 — Refresh provider models and API contracts

This is a living plan governed by `.agent/PLANS.md`. Keep `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` accurate. This plan is **proposed for review**. Its creation does not authorize provider implementation; begin MS001 only after the user approves it. The source audit is `docs/provider-model-audit-2026-10.md`, dated 2026-10-23. Recheck official provider contracts when execution starts because model catalogs can change.

## Purpose / Big Picture

AgentRules users should be able to choose current direct API models without silently changing an existing saved selection, sending an unsupported reasoning setting, or packing more input than a model accepts. The researcher loop should complete a Gemini function call with its call identity and thought state intact. Local Codex and Claude Code choices should follow their installed runtimes. The CLI picker, configuration resolution, and actual provider request must agree about which model will run.

The observable result is a picker with reviewed GPT-6, Claude 5.5/Fable 5.1, Grok 4.7, DeepSeek V4.1 Flash, and Gemini 3.8/4 options; an old saved key still loads and either keeps its live endpoint or resolves to a documented replacement; invalid model/effort combinations fail before a network call; and deterministic provider contract tests pass. Paid, account-specific live smokes are a separate opt-in release gate.

## Scope and Contract Snapshot

Direct API providers own a reviewed static registry. Codex gets its model and effort list from app-server `model/list`; Claude Code owns moving aliases through its installed executable. A **preset key** is a public identifier saved in user configuration; a **wire model** is the model ID sent to a provider. A **one-hop redirect** means the saved key resolves directly to a canonical active preset, because `resolve_runtime_preset_key` currently replaces only once. A model is **deprecated but live** when it remains callable: show a warning and preserve its wire model until retirement. A **retired** key needs an explicit one-hop replacement. Preserve existing keys in both cases.

The dated target is precise. OpenAI candidates are `gpt-6-astra`, `gpt-6.1-sol`, `gpt-6-sol`, and `gpt-6-luna`, each with 1,050,000 total context, 922,000 maximum input, and 128,000 maximum output. Astra and 6.1 Sol accept low/medium/high/xhigh/max reasoning; 6 Sol and Luna also accept none. Add 6 Sol because it is the documented replacement for retiring GPT-5.1 and GPT-5.3-Codex keys. DeepSeek's canonical Flash wire ID is `deepseek-flash` with 1M context; existing V4 Flash keys and `deepseek-chat`/`deepseek-reasoner` become compatibility IDs. Keep V4 Pro and the application's 32K output cap. Anthropic candidates are Opus/Sonnet/Haiku 5.5 and Fable 5.1 with 1M context and 128K maximum output; thinking and refusal behavior differs by model. Fable's 30-day retention must be visible at selection time. Grok 4.7 has 500K context and only low/medium/high/xhigh reasoning. Gemini 3.8 Flash has a 1,048,576 input limit and 65,536 output cap; Gemini 4 Argon shares 1,048,576 total tokens across input, thinking, and output and normally caps a single request at 32,768 output. Both allow low/medium/high thinking, not minimal or disabled. These are planning facts from the audit, not substitutes for implementation-day source checks.

Mandatory work covers lifecycle corrections, one-hop compatibility routing, strict model capability metadata, input packing limits, provider request and parser behavior, Gemini function-call continuation, relevant SDK floors/lockfile updates, local runtime gating, docs, and offline tests. The OpenAI and Anthropic synchronous direct SDK calls should leave the asyncio event loop in their provider slices, with failure behavior covered. Keep phase defaults and older explicit rollback choices until representative project evaluations justify a replacement. Do not add restricted Mythos 5.1, unavailable Grok 4.7 Fast, DeepSeek image/search tools, static new Codex models, or unrelated modality work.

The audit's P2 API topics are a bounded evaluation in MS007. xAI Responses, Anthropic SDK 2.x/API 2026-10-21, and Gemini Interactions may affect transport, authentication, tool state, streaming, and structured output. MS007 must produce a tested go/no-go record for each; do not bundle a wholesale transport migration into a picker update without a reviewed contract and amended scope. Gemini's `google-genai>=2.30.1` floor for Argon continuation and the Claude Agent SDK version needed for bundled Claude Code are mandatory dependency changes in MS003 and MS006. OpenAI Responses and DeepSeek Chat Completions remain valid paths under this plan.

## Progress

- [x] (2026-10-23) Completed the read-only provider audit and opened PR #42 with its source report.
- [x] (2026-10-23) Created this proposed ExecPlan and eight planned milestone documents for review.
- [ ] User reviews and approves this plan before provider implementation begins.
- [ ] MS001: Revalidate sources; correct urgent DeepSeek and Gemini lifecycle routing.
- [ ] MS002: Implement OpenAI GPT-6 contracts and input-limit repair.
- [ ] MS003: Repair Gemini tool continuation; onboard Gemini 3.8 Flash and 4 Argon.
- [ ] MS004: Implement Anthropic direct-model contracts and refusal handling.
- [ ] MS005: Implement Grok 4.7 strict capabilities.
- [ ] MS006: Gate Claude Code pinned models; verify Codex dynamic boundary.
- [ ] MS007: Evaluate optional API migrations with explicit decisions.
- [ ] MS008: Run integrated validation, lifecycle review, default evaluation, and release checks.

## Surprises & Discoveries

- `resolve_runtime_preset_key` performs only one replacement. DeepSeek legacy keys therefore cannot redirect through an intermediate deprecated Flash key.
- The Gemini researcher loop sends tool feedback as fresh text, and its parser discards function-call IDs. Merely adding 3.8/4 presets would expose a broken tool path.
- The lockfile's bundled Claude Code version is below every proposed pinned 5.5/5.1 minimum. Runtime gates and the dependency update must land together.
- The audit found Gemini 2.5 Flash/Pro still active for prior users, contrary to the repository's October 16 shutdown claim. Recheck this dated upstream fact at execution.

## Decision Log

- Decision: Make capability and lifecycle correctness the prerequisite for exposing new models. Rationale: A picker entry can otherwise dispatch an unsupported request or silently change a saved workload. Date/Author: 2026-10-23 / @codex.
- Decision: Preserve deprecated-but-live saved keys; use AgentRules one-hop redirects only for verified retired endpoints and DeepSeek's temporary wire alias. Gemini upstream aliases keep their saved and wire IDs while labels disclose the effective serving model. Rationale: Users may depend on original cost and behavior, and provider-side aliasing is distinct from a local redirect. Date/Author: 2026-10-23 / @codex.
- Decision: Use explicit immutable capability records rather than infer behavior from name substrings or coerce invalid reasoning. Rationale: Families differ in limits, thinking, tools, refusals, and retention. Date/Author: 2026-10-23 / @codex.
- Decision: Keep Codex discovery and Claude Code moving aliases runtime-owned; version-gate pinned Claude Code IDs against the exact resolved executable. Rationale: Direct API announcements do not establish local availability. Date/Author: 2026-10-23 / @codex.
- Decision: Treat transport migrations as a P2 decision gate and keep defaults stable pending evaluation. Rationale: Current endpoints still serve these models; migration and default changes add independent behavior and cost risk. Date/Author: 2026-10-23 / @codex.

## Outcomes & Retrospective

Planning artifact only as of 2026-10-23. No provider behavior, dependency, default, or saved key has been changed. Record implementation outcomes, measured evaluations, remaining risks, and release decision here after the milestones run.

## Context and Orientation

Run commands from repository root `/Volumes/AGENAI/Coding/public-github/agentrules-architect`. Python source is in `src/agentrules`. `src/agentrules/config/agents.py` supplies provider/model defaults and context settings. `src/agentrules/core/configuration/model_presets.py` owns saved keys and deprecations. Provider adapters are in `src/agentrules/core/agents/{openai,anthropic,deepseek,xai,gemini,claude_code,codex}`. They construct payloads, invoke SDKs, and parse responses; `src/agentrules/core/utils/provider_capabilities.py` holds cross-provider pipeline exceptions. `src/agentrules/core/analysis/phase_1.py` owns researcher tool turns. `docs/provider-model-lifecycle.md` and `README.md` explain selection to operators. Existing provider tests are under `tests/unit/agents/`, `tests/unit/test_agents_*.py`, and `tests/live/`. `pyproject.toml`, `uv.lock`, and `typings/google/genai/types.pyi` define dependency and typing contracts. Read nearby `SNAPSHOT.md` files before moving paths; run `agentrules snapshot sync` if paths change.

The request path is: load saved preset key → resolve lifecycle mapping → obtain model capability metadata → build provider-native request → parse response → feed phase output or tool result into the next turn. Tests must assert both selected wire model and request/response behavior. A model-list test alone does not prove a usable model.

## Plan of Work and Milestone Sequence

All milestone files named below are under `.agent/exec_plans/active/provider-model-api-refresh-2026-10/milestones/active/` until the CLI marks them complete.

MS001 (`milestones/active/MS001_lock-contracts-and-correct-urgent-lifecycle-routing.md`) locks an implementation-day official-source matrix and fixes two urgent lifecycle claims. In `model_presets.py` and DeepSeek config/defaults, expose canonical `deepseek-flash` profiles and point old V4 Flash and `deepseek-chat`/`deepseek-reasoner` keys directly to them. Keep V4 Pro and its text Chat transport. In `config/agents.py`, lifecycle docs, and README, correct Gemini 2.5 Flash/Pro from “retired” to active for prior users, and disclose Gemini 3.7→3.8 and 3.5→3.6 upstream aliases. Test picker, saved-key load, one-hop resolution, and direct constructor.

MS002 (`MS002_add-openai-gpt-6-and-repair-input-limits.md`) replaces broad name-based limit selection in `config/agents.py` with explicit total/input/output metadata used by the packer. Effective input budget must respect maximum input and total context after output reservation and normal packing margin; test 272K input for GPT-5.4 Mini/Nano and GPT-5.3-Codex plus current GPT-5.5/4.1 values. Extend `openai/request_builder.py` and config with four GPT-6 families and exact accepted efforts on Responses. Preserve GPT-5.6 rollback choices. Add dated deprecation metadata for GPT-5/o3, GPT-4.1, GPT-5.1/5.3-Codex/5.4 Nano; keep live keys bound until retirement, then provide direct replacements. Replace the direct architect's `o3` default before shutdown. Move its synchronous SDK call off the event loop.

MS003 (`MS003_repair-gemini-tool-turns-and-add-current-models.md`) first proves a complete two-turn function exchange in `phase_1.py` and `gemini/response_parser.py`: retain returned model content, thought signatures, function-call ID/name/args, and send a matching structured response. Then add strict 3.8 Flash and 4 Argon capabilities, input/output budgeting, and picker entries. Raise `google-genai` floor to at least 2.30.1, regenerate `uv.lock`, and update the local type stub only for APIs used. Test invalid minimal/disabled requests before dispatch and Argon's shared token budget. Enable researcher use only once the contract test passes.

MS004 (`MS004_add-anthropic-5-5-models-and-refusal-handling.md`) adds Opus/Sonnet/Haiku 5.5 and Fable 5.1 in `anthropic/capabilities.py`, request builder, parser, and presets with model-specific adaptive-thinking rules. Extend typed stream/refusal handling so a 200 response with refusal stop reason is an explicit failure. Surface Fable retention in labels/docs. Keep deprecated Sonnet 4.5 compatibility keys on the live endpoint until November 30 retirement, then use a direct chosen Sonnet 5.5 profile. Remove retired 3.5 Sonnet ID from `final_analysis_prompt.py`. Move the direct SDK call off the event loop and verify structured output.

MS005 (`MS005_add-grok-4-7-with-strict-reasoning-contracts.md`) adds Grok 4.7 low/medium/high/xhigh presets and a strict 500K profile in xAI config/request tests. Keep 4.6 as fallback and existing 4.20, 4.3, and Build choices unless revalidation shows retirement. Do not add unavailable 4.7 Fast. Chat Completions remains the implementation transport; optional Responses migration is MS007. Prove tools and structured output payloads and reject disabled/minimal reasoning before dispatch.

MS006 (`MS006_gate-claude-code-pinned-models-and-preserve-codex-discovery.md`) keeps moving `best`/`opus`/`sonnet`/`fable` aliases, optionally exposes `haiku`, and adds pinned Fable 5.1, Opus 5.5, Sonnet 5.5, and Haiku 5.5 only if the **exact** executable used by the Claude Agent SDK can be versioned at ≥2.1.257/2.1.280/2.1.284/2.1.293 respectively. Fix longest-prefix matching in `configuration/services/claude_code.py`, update the Claude SDK/lockfile to a bundled runtime meeting the minimum, and fail closed on unversionable runtimes. Verify Codex remains driven by `codex/client.py` and `model_selection.py` `model/list` output, with no static GPT-6 Codex preset.

MS007 (`MS007_evaluate-optional-provider-api-migrations.md`) is a bounded investigation. Build small offline contract probes for xAI Responses versus Chat, Anthropic SDK 2.x/API 2026-10-21 versus current client (including gateway/auth header and `output_config`), and Gemini Interactions versus GenerateContent. Record whether each offers a required capability, exact request/stream/tool/parser changes, dependency impact, rollback, and a go/no-go. If a migration is necessary, amend this ExecPlan with a separately reviewable implementation milestone before coding it. A documented no-go with passing current-transport contracts satisfies MS007.

MS008 (`MS008_validate-integration-and-release-readiness.md`) checks all saved keys, picker labels, runtime requests, lifecycle docs, dependency lock consistency, offline pipeline smoke, and full quality gates. Evaluate any proposed default switch on representative AgentRules projects, recording task quality, latency, cost, and entitlement; if unavailable, leave defaults unchanged and say so. Run optional credentialed live smokes only when the operator enables their existing test gates, recording account/region/quota limits separately from code defects. Keep PR diffs scoped and update `AGENTS.md` for significant final architecture changes.

## Concrete Steps

After approval, use the existing checkout and first run from repository root:

    git status --short --branch
    .venv/bin/python -c 'import agentrules; print("import ok")'
    .venv/bin/pytest -q tests/unit

Expected baseline: intended branch, `import ok`, and passing offline unit tests. The audit run had 954 passing tests and 57 subtests; counts may grow, so compare failures rather than require those numbers. For each milestone, set its YAML status to `in_progress`, update this plan's Progress, edit only its provider slice, run focused tests, then shared gates. Existing focused entry points include `tests/unit/agents/test_openai_helpers.py`, `test_anthropic_capabilities.py`, `test_gemini_capabilities.py`, `test_xai_helpers.py`, `test_claude_code_client.py`, and `tests/unit/test_agents_deepseek.py`. Add behavior-level tests beside them. Complete a passing milestone with `.venv/bin/agentrules execplan milestone complete EP-20261023-001 --ms N`, substituting its sequence number; the CLI moves it to `milestones/complete/`, so update links here. After dependency changes run `uv lock` and `uv lock --check`. After file additions/moves/removals run `.venv/bin/agentrules snapshot sync`. Refresh registry with `.venv/bin/agentrules execplan-registry update` after metadata edits. Final gates:

    .venv/bin/ruff check .
    .venv/bin/pyright
    .venv/bin/pytest -q tests/unit
    .venv/bin/python -c 'import agentrules; print("import ok")'
    uv lock --check
    git diff --check

If `uv` is absent from PATH, use the executable documented by repository CI before changing the lock. Complete the ExecPlan only after mandatory milestones and acceptance criteria pass, using `.venv/bin/agentrules execplan complete EP-20261023-001`.

## Validation and Acceptance

Offline tests must demonstrate: each new picker choice resolves to its intended wire ID and accepted reasoning/thinking value; unsupported values fail before network dispatch; packed input respects per-model maximum and output reservation; Gemini researcher makes a valid two-turn function exchange; Anthropic refusal cannot become successful text; deprecated-but-live saved keys retain behavior; verified retired and DeepSeek compatibility keys resolve in one hop; Gemini upstream aliases keep their saved identity with truthful effective-model labels; old/unversionable Claude Code executable fails before launch; and Codex accepts runtime-discovered models without static GPT-6 keys. Exercise the CLI picker with existing test or interactive environment to inspect labels, and use `pytest -q tests/unit` for deterministic end-to-end coverage. Optional live tests establish actual account availability, not the static contract.

Acceptance also requires ruff, pyright, import smoke, lock check, `git diff --check`, snapshot/registry checks, lifecycle docs, and PR review. CI import smoke and prompt-template checks must stay green. If provider docs change during implementation, record URL/date and update the affected milestone before dispatching that model. A model unavailable to the test account remains gated or omitted; do not infer availability from catalog docs.

## Idempotence and Recovery

Each milestone should be additive and independently shippable. Do not delete old saved IDs. Repeatable CLI and lockfile generation should converge to the same files. If a provider slice fails, revert only its new preset exposure while retaining safe lifecycle fixes; explicit older models remain rollback choices. Do not change defaults until evaluation supports them. Preserve deprecated-but-live wire endpoints and use one-hop maps only for retired/aliased keys. On dependency upgrade failure, restore `pyproject.toml` and `uv.lock` together. Never hand-edit `uv.lock`. Live smokes use opt-in flags and must not become a default CI dependency.

## Artifacts and Notes

The source report is `docs/provider-model-audit-2026-10.md`; its official links are evidence snapshots to recheck. The eight milestone documents under this plan carry file-level tasks, dependencies, risks, and before/after checks. PR #42 currently contains the audit and this plan only. Record implementation-day source matrix, representative default evaluation, and optional API migration decisions here as execution proceeds.

## Interfaces and Dependencies

Extend existing capability types where possible instead of adding a second registry. Authoritative profiles need wire ID, total context, maximum input where separately documented, maximum output, accepted reasoning/thinking, tool and structured-output compatibility, and refusal/retention constraints. The packer consumes effective input budget; request builders consume validated provider-native values. Keep provider object coercion in `src/agentrules/core/utils/provider_utils.py`; keep Codex phase exceptions in `src/agentrules/core/utils/provider_capabilities.py`. Use `google-genai>=2.30.1` for Argon continuation and a Claude Agent SDK release whose bundled exact Claude Code version passes pinned gates, updating `uv.lock` and local stubs in the same milestone. Avoid new dependencies for optional xAI/Anthropic transports until MS007 proves need.

Plan revision note, 2026-10-23: Initial review draft derived from the dated provider audit; implementation awaits user approval.
