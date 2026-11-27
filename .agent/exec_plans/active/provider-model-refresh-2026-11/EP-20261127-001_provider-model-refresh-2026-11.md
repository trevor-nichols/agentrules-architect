---
id: EP-20261127-001
title: "Refresh provider models and runtimes for November 2026"
status: active
kind: feature
domain: cross-cutting
owner: "@codex"
created: 2026-11-27
updated: 2026-11-27
tags: [providers, model-lifecycle, sdk, runtime]
touches: [api, cli, agents, tests, docs]
risk: high
breaking: false
migration: true
links:
  docs: "docs/provider-model-lifecycle.md"
depends_on: [EP-20261023-001]
supersedes: []
---

# EP-20261127-001 — Refresh provider models and runtimes for November 2026

Maintain this plan under the repository's ExecPlan guidance. Keep Progress, Surprises & Discoveries, Decision Log, and Outcomes & Retrospective current. After approval, update the YAML status and dates as work progresses. Use the workspace layout detected by the branch's CLI.

## Purpose / Big Picture

People with saved analysis or researcher settings should still be able to run AgentRules after the selected provider retires or reroutes a model. The picker should show which model AgentRules will call, explain changes in reasoning or retention where applicable, and let people select newly supported models. A fresh locked install should support the advertised choices, including Gemini's extra-high effort and the bundled Claude Code executable for Fable 5.2.

The first release slice restores compatibility for retired models and near-term cutovers. Follow with the new model choices and targeted dependency changes. Validate each slice independently so a later SDK change cannot delay an already-needed compatibility fix.

## Scope

The plan covers the five direct providers (OpenAI, Anthropic, Google Gemini, xAI, and DeepSeek) and the two local runtime providers (Codex and Claude Code). It includes persisted selection compatibility, direct model capabilities and picker entries, Gemini and Claude Agent SDK updates, native DeepSeek researcher tool continuation, Codex discovery validation, and release evidence. Existing phase defaults remain in place pending representative evaluations. The Gemini adapter's constructor default changes because its current wire model is being rerouted with a different request contract.

This rollout uses OpenAI Responses, Anthropic Messages, Gemini GenerateContent, and the existing xAI and DeepSeek Chat Completions adapters. The xAI Responses migration gets a documented follow-up design and its own delivery decision. OpenAI Python 3.x, Anthropic SDK 2.x, Gemini Interactions, new hosted search or media features, and restricted models are outside this rollout.

## Progress

- [x] (2026-11-27) Compare the seven integrations and locked dependencies with official release notes, model contracts, and retirement schedules. Verify OpenAI 2.45.0 request serialization for the three new direct model IDs using an offline mock transport.
- [x] (2026-11-27) Create `codex/provider-model-refresh-2026-11` from the October provider refresh at `261fbb5`. Draft the ExecPlan and seven milestones.
- [x] (2026-11-27) Verify planning artifacts and establish the locked Python 3.11 baseline. The import smoke, 1,160 tests and 57 subtests, Ruff, Pyright, and lock check passed. The registry lists the plan and all seven milestones.
- [x] (2026-11-27) Operator approved the plan and authorized sequential implementation. Each milestone requires passing validation and independent review before completion, commit, and push.
- [x] (2026-11-27) MS001 ships the independent compatibility slice for past and imminent provider cutovers. Locked Python 3.11 checks passed (1,168 tests, 77 subtests, Ruff, Pyright, import smoke, lock check, and diff check). Independent review passed with no actionable findings.
- [x] (2026-11-27) MS002 adds OpenAI model contracts and finishes the December 11 routes. Locked Python 3.11 checks passed (1,176 tests, 69 subtests, Ruff, Pyright, import smoke, lock check, and diff check). Independent review passed with no actionable findings.
- [ ] MS003 adds Gemini 4 model profiles and validates the GenAI SDK upgrade.
- [ ] MS004 adds direct and local-runtime Fable 5.2 with the Claude Agent SDK upgrade.
- [ ] MS005 preserves DeepSeek reasoning across tools and records the xAI transport follow-up.
- [ ] MS006 verifies Codex runtime discovery for GPT-6.2.
- [ ] MS007 verifies release readiness, records rollout and recovery instructions, and closes the plan.

## Surprises & Discoveries

The October work is present on `codex/provider-model-api-audit-2026-10` at `261fbb5`. On November 27 the remote `main` was still `e0194e8`. The branch also carries the earlier ExecPlan workspace, which the CLI uses automatically. The separate ExecPlan directory migration would otherwise add unrelated review and merge work.

The saved preset resolver follows one replacement step. On this branch, `grok-code-fast` resolves to `grok-build-0.1`, which xAI stopped serving on November 19. Both keys need their own direct route to a live preset. Picker labels, effective wire models, and passive preservation of the configured key are three separate behaviors to verify.

Google's December 1 reroutes preserve the old API IDs while changing the supported thinking field and, where applicable, signed function-call continuation. The existing Gemini 2.5 Flash constructor default sends `thinking_budget=0`. Switching both model and reasoning policy is necessary to produce a valid request. The October refresh already contains signed tool replay and the two replacement capability profiles.

The branch locks `openai==2.45.0`, `anthropic==0.83.0`, `google-genai==2.33.0`, and `claude-agent-sdk==0.2.173`. New OpenAI IDs serialized with the first lock in an offline probe. Gemini's native `XHIGH` landed in GenAI 3.3.0. Claude Agent SDK 0.2.173 bundles Claude Code 2.1.309, below the pinned Fable 5.2 minimum of 2.1.321.

A previous local run on the October provider branch recorded two CLI picker assertions sensitive to console line wrapping. The planning baseline reproduced a passing locked Python 3.11 run. If the assertions reproduce on a different terminal during implementation, check that the displayed warning still contains the complete expected text before adjusting whitespace handling in the tests.

## Decision Log

- **2026-11-27, @codex** — Base the branch on the October provider refresh to reuse its model contracts and test fixtures. Land or carry that dependency before release. Keep the ExecPlan layout migration independent.
- **2026-11-27, @codex** — Make MS001 deployable with the October lock. Stage OpenAI's December 11 targets with the model work because GPT-6.1 Terra needs a new registry entry. If approval or merge timing slips past a cutover, run tests at the cutover boundary and ship the live endpoint mapping as the first available patch.
- **2026-11-27, @codex** — Use explicit provider capability metadata and strict reasoning validation. Preserve saved keys, put compatibility routes in one place, and disclose the few effort changes needed by upstream policy.
- **2026-11-27, @codex** — Update Gemini and Claude Agent SDKs in provider-sized commits with their lockfile changes. Reuse existing transport for new choices. Record xAI's stateful Responses tradeoffs and keep credentialed or billable validation opt-in.
- **2026-11-27, @codex** — Continue to discover Codex models from the configured executable and account. A public model release and a CLI version establish expected availability. Only the runtime catalog establishes which models that installation offers.

## Outcomes & Retrospective

MS001 restored compatibility for retired presets and installed the scheduled Gemini and Opus routes. The current SDK lock still supports the full offline suite. Authenticated model availability, quota, and output behavior remain unverified.

## Context and Orientation

`src/agentrules/config/agents.py` owns picker presets and phase defaults. A preset key is the stable string saved in configuration. The wire model is the identifier sent to the provider. Centralized deprecations in `src/agentrules/core/configuration/model_presets.py` translate saved selections at load or request time, with an injectable `as_of` date for tests. Keep that resolution separate from the provider's capability metadata. Passive loading leaves the originally saved key intact. Explicitly selecting a deprecated choice can save its canonical replacement.

`src/agentrules/core/types/models.py` holds typed configuration instances. The provider subpackages under `src/agentrules/core/agents/` assemble requests and parse SDK responses. Update the relevant provider capability table and reuse shared helpers when possible. The packer reads effective input limits and reserves generation capacity where the provider publishes a total context window. The researcher in `src/agentrules/core/analysis/phase_1.py` executes tool calls and passes tool outcomes back. Gemini already has a native continuation path there. Native continuation sends the previous assistant turn and a tool response linked to the provider's call identifier.

The October plan EP-20261023-001 records the dependency this branch was cut from. Its durable contract summary is `docs/provider-model-lifecycle.md`. Use `docs/claude-code-runtime.md` and `docs/codex-runtime.md` for operator-facing runtime behavior and `tests/live/` for opt-in smoke tests. `pyproject.toml` declares install-time dependency constraints and `uv.lock` pins the shared test and deployment environment.

## Plan of Work

**MS001 — Restore saved presets before provider cutovers.** Add centralized one-hop routes for retired o4-mini and Grok Build selections immediately. Schedule the Gemini 2.5 replacements on December 1 and the direct Anthropic Opus 4.5 replacement on January 22. Verify the existing Sonnet 4.5 November 30 routes on the branch that will ship. Update the Gemini constructor and compatibility entry points to emit current requests, and validate saved settings, warnings, and actual wire IDs with the current lock. See [MS001](milestones/complete/MS001_provider-cutovers.md).

**MS002 — Add OpenAI text models and December retirement routes.** Add GPT-6.2 Astra, GPT-6.2 Sol, and GPT-6.1 Terra to the direct registry with explicit reasoning and input budgets. Bind December 11 saved GPT-5 and o3 keys to GPT-6.1 Sol and GPT-5 Mini to GPT-6.1 Terra. Use low for the old GPT-5 minimal profile and label that change. Verify the real SDK's outbound payload with a mock transport and keep the existing OpenAI SDK major version. See [MS002](milestones/complete/MS002_openai-models.md).

**MS003 — Add Gemini 4 models and validate the GenAI SDK upgrade.** Add Carbon, Hydrogen, and Neon to the existing GenerateContent transport. Reuse Argon's shared-window and signed-turn behavior. Add exact `XHIGH` only to Hydrogen and Neon, bump `google-genai` to at least 3.3.0, and verify endpoint selection, HTTP client behavior, and stubs. Record the resolved version in the lockfile. See [MS003](milestones/active/MS003_gemini-4-and-sdk.md).

**MS004 — Add Fable 5.2 across Anthropic and Claude Code.** Add the direct model and validate its adaptive thinking, retention label, and refusal boundary. Add the pinned runtime choice in a separate change with the SDK bump to at least 0.2.180. Verify that both the picker and request use the exact resolved executable and reject old or unversionable binaries. See [MS004](milestones/active/MS004_fable-5-2.md).

**MS005 — Preserve DeepSeek tool turns and assess xAI transport.** Pass original DeepSeek reasoning and matching tool results back across researcher iterations using its existing Chat Completions contract. Verify a multi-call turn and an error outcome end to end. DeepSeek's current model IDs and xAI's Grok 4.7 are already registered. Document the xAI Responses follow-up with a storage decision, request/response mapping, and a test strategy for encrypted reasoning. See [MS005](milestones/active/MS005_deepseek-tools-and-xai-transport.md).

**MS006 — Verify Codex runtime discovery for GPT-6.2.** Exercise app-server model and effort discovery, saved round trips, and supported output schemas with the fake server. Document the upstream CLI minimum and the exact configured executable check. Keep catalog and account eligibility runtime-owned. See [MS006](milestones/active/MS006_codex-runtime-discovery.md).

**MS007 — Validate the release and document rollout and recovery.** Run the clean locked checks and collect milestone evidence. Review against the real merge base and confirm the release includes the October prerequisites and all required date-based routes. Record skipped live checks and leave defaults at their existing values. See [MS007](milestones/active/MS007_release-validation.md).

## Concrete Steps

After approval, run these commands from the repository root on the November branch. Verify the October dependency is included before editing. Record the baseline results and repeat the same checks before release.

    git status --short --branch
    git merge-base --is-ancestor 261fbb5 HEAD
    uv sync --locked --extra dev --python 3.11
    uv run --python 3.11 --no-sync python -c 'import agentrules; print(agentrules.__file__)'
    uv run --python 3.11 --no-sync pytest -q tests --ignore=tests/live
    uv run --python 3.11 --no-sync ruff check .
    uv run --python 3.11 --no-sync pyright
    uv lock --check --python 3.11
    git diff --check

The planning baseline used a temporary directory via `UV_PROJECT_ENVIRONMENT` because the existing local virtual environment pointed to an unavailable Python interpreter. Use a fresh project environment for the approved work. Run the milestone's focused tests before and after each edit. For dependency changes, use package-scoped `uv lock --upgrade-package`, then inspect the resolver's transitive changes and repeat the locked sync. Keep the dependency declaration, regenerated lock, request changes, and affected stubs together.

After each milestone passes its acceptance checks, move its record with `agentrules execplan milestone complete EP-20261127-001 --ms N` and update this progress log, including the link to the milestone's new location. Complete the parent plan with `agentrules execplan complete EP-20261127-001` only after MS007. Refresh the registry and check it. Use `agentrules snapshot sync` when tracked paths are added, removed, or moved and inspect its diff for unrelated drift.

## Validation and Acceptance

The picker and persisted configurations must resolve to the expected provider model and effort immediately, on the applicable cutover date, and afterward. Each cutover test injects the applicable date and covers the preceding day. For a legacy preset, verify the actual outgoing model and request shape plus the displayed warning. Test a fresh install and a pre-existing stored selection for every provider that changes. Dates and tests use the resolver's UTC calendar day. If a provider publishes a narrower cutoff, record it and handle it explicitly.

For newly advertised models, offline tests cover supported and rejected effort values, usable input budget, structured output and tools where applicable, refusal/error handling, and actual adapter dispatch through mocks. Run the full non-live suite and all jobs in `.github/workflows/test.yml`. The import smoke must print the working tree's package path, the lock must be current, and Ruff and Pyright must pass. New tests should exercise observed behavior and catch the target regression before the fix.

Credentialed checks require separate operator opt-in. Use the existing provider-specific environment flags and `pytest --run-live`. Record endpoint access, effort, structured response, and representative analysis results only for smokes actually run. Avoid recording credentials, full refused output, or account identifiers. If live tests are skipped, report that availability and quality are still unverified.

## Idempotence and Recovery

Compatibility redirects are read-time lookups and preserve persisted IDs. Repeated invocations with the same configured key and date resolve to the same live preset. Route both old xAI keys directly to Grok 4.7. After a cutoff, preserve the compatibility fix even if a later slice needs reverting. Use an already supported live preset when a new model is unavailable, and keep phase defaults during rollout.

Keep SDK versions and lockfile edits reversible as provider-sized changes. Roll back the corresponding model picker exposure with the SDK bump if the older lock cannot support it. Keep Gemini's December redirects and the October signed-turn path if rolling back the Gemini 4 or SDK slice. A failed runtime version probe should surface the exact executable and required version, keeping saved pinned selections available for later remediation.

## Artifacts and Notes

The planning baseline ran on Python 3.11.18 with the October lock. The offline suite passed 1,160 tests and 57 subtests. Import smoke, Ruff, Pyright, and the lock check passed. The snapshot preview showed existing path drift and the plan files are under the excluded `.agent/` directory.

Record the milestone-specific failing-before and passing-after results, Python and SDK versions, installed or bundled runtime versions, registry checks, lock changes, and live smoke status in the milestone documents. Use the docs below for implementation-time rechecks. The behaviors required by the plan are stated in the milestones so implementation can proceed from the checked-in plan.

- [OpenAI model catalog](https://developers.openai.com/api/docs/models) · [OpenAI deprecations](https://developers.openai.com/api/docs/deprecations)
- [Gemini deprecations](https://aistudio.google.com/docs/deprecations) · [Gemini Python SDK releases](https://github.com/googleapis/python-genai/releases)
- [Fable 5.2 migration](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide) · [Claude deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations) · [Claude Code model configuration](https://code.claude.com/docs/en/model-config)
- [xAI release notes](https://docs.x.ai/developers/release-notes) · [DeepSeek thinking mode](https://api-docs.deepseek.com/guides/thinking_mode/) · [Codex app-server model discovery](https://learn.chatgpt.com/docs/app-server#list-models-modellist)

## Interfaces and Dependencies

Use `resolve_runtime_preset_key(..., as_of=...)` for lifecycle policy and the existing provider capability helpers for request validation. Keep `ToolManager` tool definitions serializable and perform vendor-specific request conversion at dispatch. Retain `ConfigManager.build_codex_launch_config()` as the single entry point for Codex launch policy and the existing Claude Code service for exact executable version resolution. Keep structured-output schemas tied to supported provider capabilities. Claude Agent SDK and Gemini GenAI are the only planned direct Python dependency changes.

Revision note (2026-11-27) — Created the implementation plan and milestone sequence for operator review.
