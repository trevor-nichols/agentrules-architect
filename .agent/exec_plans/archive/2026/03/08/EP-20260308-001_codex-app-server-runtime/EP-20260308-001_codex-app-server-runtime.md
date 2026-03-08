---
id: EP-20260308-001
title: Integrate Codex app-server runtime
status: archived
kind: feature
domain: cross-cutting
owner: '@codex'
created: 2026-03-08
updated: '2026-03-08'
tags:
- codex
- app-server
- cli
- providers
touches:
- cli
- agents
- tests
- docs
risk: med
breaking: false
migration: false
links:
  issue: ''
  pr: ''
  docs: internal-docs/integrations/codex/app-server
depends_on: []
supersedes: []
---

# Integrate Codex app-server runtime

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan must be maintained in accordance with `.agent/PLANS.md`.

## Purpose / Big Picture

After this change, AgentRules users will be able to choose Codex-backed models for pipeline phases without supplying provider API keys to AgentRules itself. Instead, AgentRules will launch the locally installed `codex` runtime, reuse the user's Codex login state from `CODEX_HOME`, and ask Codex to analyze the repository from the filesystem directly. The user-visible outcome is simple: in AgentRules settings they can configure a Codex runtime, pick `codex-*` model presets for phases, log in with ChatGPT when needed, and run the normal multi-phase pipeline with structured outputs still enforced for the phases that already depend on schemas.

This work matters because Codex is not just another stateless chat API. It is a stateful coding runtime with repository navigation, shell access, web search, approvals, session history, and ChatGPT-managed authentication. Treating it like a plain API provider would produce a brittle implementation that duplicates file contents into prompts, ignores the runtime's tool model, and prevents users from taking advantage of ChatGPT-managed access. The goal of this plan is to integrate Codex in a way that matches how the runtime actually works while preserving AgentRules' current provider abstraction.

## Repository Orientation

The existing provider abstraction lives under `src/agentrules/core/agents/`. `BaseArchitect` in `src/agentrules/core/agents/base.py` defines the methods that each provider must implement. `ArchitectFactory` in `src/agentrules/core/agents/factory/factory.py` chooses the provider implementation from `ModelConfig.provider`. Model presets live in `src/agentrules/config/agents.py`, and phase-specific prompt construction lives in `src/agentrules/config/prompts/` plus the phase runners under `src/agentrules/core/analysis/`.

The current CLI configuration model is split across `src/agentrules/core/configuration/models.py`, `manager.py`, `serde.py`, and the interactive settings flows under `src/agentrules/cli/ui/settings/`. Today those settings assume a provider is primarily an API key plus a static preset list. Codex breaks that assumption because availability depends on a local CLI binary, a resolved `CODEX_HOME`, and a live JSON-RPC session that can report auth state and the model catalog.

The local Codex integration reference is in `internal-docs/integrations/codex/app-server`. The important documents for this plan are:

- `guides/00-overview.md`: Codex app-server is the rich-client integration surface.
- `guides/01-protocol.md` and `guides/02-message-schema.md`: JSON-RPC over JSONL/stdin/stdout.
- `guides/05-lifecycle.md`, `reference/threads.md`, `reference/turns.md`, `reference/events.md`: thread/turn/item lifecycle and streamed events.
- `reference/auth.md`: ChatGPT login, logout, account state, and rate limits.
- `reference/models.md`: `model/list` for dynamic model discovery.
- `guides/13-prompt-precedence.md`: how `developer_instructions`, `AGENTS.md`, and per-run overrides interact.
- `configurations/advanced.md`: `CODEX_HOME` layout and state files.

The official OpenAI docs add one important comparison point: the SDK is described as more flexible than non-interactive mode, and `codex exec` is positioned primarily for one-shot automation. That makes `codex exec` a useful fallback or smoke surface, but not the right primary control plane for a Python CLI that needs login, model discovery, and structured multi-step request handling.

## Architecture Summary

The implementation will add a dedicated `ModelProvider.CODEX` pathway rather than pretending Codex is OpenAI API traffic. This is the cleanest boundary because the execution semantics are different: AgentRules will talk to a local JSON-RPC process, not directly to a provider SDK. The shared `ModelConfig` shape remains useful because Codex still needs a model name, reasoning effort, and context metadata, but the provider adapter will be a runtime bridge instead of an HTTP request builder.

### 1. Provider and preset model

Add `ModelProvider.CODEX` to `src/agentrules/core/agents/base.py` and teach the preset and factory layers to handle it. In `src/agentrules/core/types/models.py`, add a helper that derives a Codex runtime config from an existing OpenAI-family config so we can reuse existing model names and reasoning defaults instead of duplicating them by hand. The preset keys should be stable and explicit, for example `codex-gpt-5.1-codex`, `codex-gpt-5.2-codex`, `codex-gpt-5.3-codex`, and `codex-gpt-5.4`, but the underlying `model_name` values should continue coming from the already-defined model constants.

This keeps `src/agentrules/config/agents.py` as the single preset source of truth while avoiding a second copy of the same model string literals. The `MODEL_PRESET_DEFAULTS` map does not have to switch to Codex by default; Codex becomes an opt-in preset family.

### 2. Codex runtime configuration

Add a dedicated `codex` section to the AgentRules CLI configuration model instead of trying to squeeze Codex into the API-key provider store. The configuration should answer three questions:

- Which `codex` executable should AgentRules launch? Default: `codex` from `PATH`.
- Which `CODEX_HOME` should the runtime use? Strategy: `managed` or `inherit`.
- If the strategy is `managed`, where should that managed home live? Default: under AgentRules' config directory, for example `<AGENTRULES_CONFIG_DIR>/codex`.

`inherit` means AgentRules points Codex at the user's existing home and therefore sees the same auth state, config, skills, and cached state the user already has in their own CLI. `managed` means AgentRules owns a separate Codex home for isolated login/config. The config manager should resolve the effective Codex home but must not set `CODEX_HOME` globally for the whole Python process; it should only inject that environment variable when launching Codex subprocesses.

### 3. App-server transport and service layer

Create a dedicated Codex package under `src/agentrules/core/agents/codex/`. This package should contain a small, typed transport and a thin service layer:

- `process.py`: spawn `codex app-server`, set `CODEX_HOME`, pass process-level `-c key=value` overrides, and shut down cleanly.
- `protocol.py`: request IDs, JSONL read/write helpers, and JSON-RPC envelope normalization.
- `client.py`: initialize the connection, send requests, wait for responses, collect notifications, and expose convenience methods such as `read_account()`, `start_login()`, `logout()`, `list_models()`, `start_thread()`, and `start_turn()`.
- `response_parser.py`: reconstruct the final agent output from `turn/*` and `item/*` events, including final `agentMessage` text and structured-output JSON extraction.

The key design choice is process scope. We will not build a shared multiplexed daemon as the initial implementation. Instead, each Codex architect instance will own one app-server process, and each CLI settings interaction will use a short-lived process. This is intentionally simpler and safer because the app-server protocol is bidirectional and eventful. A single shared connection would require concurrent thread routing, notification fan-out, approval handling, reconnect behavior, and cancellation semantics. That complexity is unnecessary for the first production implementation.

### 4. Prompt and instruction mapping

Do not rely on undocumented or schema-absent `turn/start.collaborationMode` fields for production behavior. Local documentation discusses `collaborationMode.settings.developer_instructions`, but the generated `codex-cli 0.111.0` JSON schema does not expose a `collaborationMode` property on `TurnStartParams`. The implementation should instead use the supported app-server startup override surface:

- launch `codex app-server` with `-c developer_instructions=<system prompt>`
- launch with any other process-level overrides that should apply for the full session, such as `web_search="cached"`
- continue to send the actual task payload in `turn/start.input`

This gives us a stable mapping from AgentRules' `system_prompt` to Codex `developer_instructions` without mutating the user's persisted Codex config and without depending on a request field that is not present in the generated runtime schema.

### 5. Architect behavior

`CodexArchitect` will implement the same `BaseArchitect` methods as the other providers. Each call should use a fresh thread (`thread/start`) and then one turn (`turn/start`). The request should set:

- `cwd` to the analysis target directory.
- `approvalPolicy` to `never` so the runtime does not block on interactive approvals.
- `sandboxPolicy` to a read-only policy for analysis phases.
- `model`, `effort`, and `summary` from the active `ModelConfig`.
- `outputSchema` for the phases that already use structured outputs (`phase2`, `phase4`, `phase5`, `final`).

The adapter must parse both streamed notifications and the terminal `turn/completed` event. If `outputSchema` is in use, the adapter should validate and parse the final message as JSON before returning the same response contract the rest of AgentRules expects.

### 6. Phase-specific Codex exceptions

Codex should not receive large raw source blobs when it can inspect the repository directly. The exceptions belong in the phase orchestration layer, not scattered across unrelated helpers.

For Phase 3, add a provider-aware path that skips `_get_file_contents()` and `pack_files_for_phase3()` when the assigned architect uses `ModelProvider.CODEX`. The Codex-specific phase-3 prompt should include the tree, the assigned file paths, the prior batch summary, and explicit instructions to inspect only those files from the repository rooted at `cwd`. This bypasses the current token packer entirely for Codex runs. The existing file-embedding path remains unchanged for the other providers.

For the Phase 1 researcher, a Codex-backed researcher must not be wired through the Tavily tool loop. Codex already has built-in web search. The researcher logic should therefore become provider-aware:

- If the researcher provider is not Codex, keep the existing Tavily tool loop.
- If the researcher provider is Codex, call `analyze()` directly and allow Codex to use its own web search tool.
- Researcher enablement must no longer depend solely on Tavily credentials. If the researcher preset resolves to Codex, researcher mode should be allowed without a Tavily API key.

### 7. CLI and settings UX

Add a dedicated settings entry such as `Codex runtime` instead of mixing Codex into `Provider API keys`. The flow should show:

- detected `codex` CLI version or an installation warning
- effective `CODEX_HOME` strategy and path
- current account state from `account/read`
- ChatGPT login / logout actions
- the dynamic model catalog from `model/list`

Model preset selection remains in the existing phase-model menu, but provider availability logic must be generalized so a preset can become available because a runtime is usable, not just because an environment variable exists. Codex preset availability should be based on a probe such as: executable exists, app-server can initialize, and either authentication is already valid or the user can enter the login flow from settings.

## Milestones

### Milestone EP-20260308-001/MS001 - Establish Codex runtime foundations

This milestone introduces the new provider identity and the configuration surface that tells AgentRules how to find and launch Codex. At the end of this milestone, the repository will understand what a Codex-backed preset is, how to persist Codex runtime settings, and how to decide whether Codex presets should appear in the UI. No live model requests are required yet.

Acceptance is visible by running the unit tests for configuration and preset selection, then using the CLI settings flow to confirm the new Codex runtime category appears and persists its values correctly.

### Milestone EP-20260308-001/MS002 - Add app-server process, auth, and model catalog services

This milestone adds the JSON-RPC transport and the service methods needed by the CLI and architect layers. At the end of the milestone, AgentRules can launch `codex app-server`, complete `initialize` / `initialized`, query account state, start a ChatGPT login flow, logout, and fetch the model catalog. The milestone also adds fake app-server tests so the integration is not tied to a live Codex account during normal CI.

Acceptance is visible by running the fake transport test suite and a small manual probe that prints account state and accessible models from the configured `CODEX_HOME`.

### Milestone EP-20260308-001/MS003 - Implement Codex architect request adapter

This milestone makes Codex usable as an actual phase provider. `ArchitectFactory` can create `CodexArchitect`, structured phases can send `outputSchema`, and the adapter returns the same result envelopes as the existing providers. At the end of this milestone, a Codex architect can complete one-shot phase requests in isolation using a fresh thread and turn.

Acceptance is visible by running unit tests around request construction, final-message parsing, schema-constrained responses, and provider factory selection.

### Milestone EP-20260308-001/MS004 - Apply phase-specific Codex pipeline exceptions

This milestone teaches the pipeline how to use Codex like a repository runtime instead of a prompt-only API. At the end of the milestone, Phase 3 stops embedding source file contents for Codex agents, the researcher path stops requiring Tavily when Codex is selected, and the provider-aware logic is centralized so later phases do not accrete ad hoc special cases.

Acceptance is visible by running targeted Phase 1 and Phase 3 tests that prove the Codex path references files without reading them into prompts and that the researcher can run without Tavily credentials when the preset provider is Codex.

### Milestone EP-20260308-001/MS005 - Finish CLI workflows, tests, and rollout validation

This milestone closes the loop on user experience and regression coverage. At the end of the milestone, the settings menus and configuration helpers are coherent, the test suite covers the new provider path, optional live smoke tests exist for local verification, and the docs/operational notes explain how managed versus inherited `CODEX_HOME` works.

Acceptance is visible by running the full validation command set and, when a logged-in Codex CLI is available, a gated live smoke that executes at least one structured phase through the Codex provider.

## Validation Strategy

The minimum validation bar for the completed plan is:

1. Import smoke:
   `PYTHONPATH=src python -c "import agentrules"`
2. Lint:
   `ruff check src tests`
3. Type checking:
   `pyright`
4. Targeted tests for new Codex configuration, transport, architect, and phase exceptions:
   `PYTHONPATH=src pytest tests/unit tests/offline tests/phase_1_test tests/phase_3_test -q`
5. Optional live verification when `codex` is installed and authenticated:
   a new gated smoke command documented by the implementation, expected to be skipped in normal CI unless its env flag is set.

The completed implementation should also support a manual end-to-end demo from the repository root:

1. Configure `Settings -> Codex runtime` and choose `inherit` or `managed` `CODEX_HOME`.
2. Log in with ChatGPT if `account/read` reports no account.
3. Select a `codex-*` preset for at least one phase.
4. Run AgentRules on a repository.
5. Observe that Codex-backed phases succeed without any API key configured in AgentRules and that structured phases still return parseable JSON.

## Out of Scope

The following are intentionally excluded from this plan:

- Using the TypeScript SDK from Python.
- Making `codex exec` the primary provider path.
- Implementing a shared multi-threaded app-server daemon inside AgentRules.
- Supporting Codex sub-agent orchestration as a first-class AgentRules feature.
- Exposing the full Apps, MCP, skills, or plugins management surface beyond what is needed to preserve a user's existing Codex home.
- Allowing Codex analysis phases to modify repository files. This integration is read-oriented.

## Progress

- [x] (2026-03-08 18:39Z) Audited the local Codex app-server integration docs, the current AgentRules provider/configuration architecture, and the locally installed `codex-cli 0.111.0` command surface.
- [x] (2026-03-08 18:39Z) Reviewed official OpenAI Codex docs for non-interactive mode and the Codex SDK to choose the primary integration surface.
- [x] (2026-03-08 18:39Z) Created ExecPlan `EP-20260308-001` and milestone scaffolds `MS001` through `MS005`.
- [x] (2026-03-08 20:02Z) Implemented `ModelProvider.CODEX`, derived `codex-*` presets, Codex runtime configuration persistence, provider-aware preset availability, managed/inherited `CODEX_HOME` handling, and the initial Codex settings UI.
- [x] (2026-03-08 22:10Z) Implemented the Codex app-server process/client/auth/model-catalog layer, added a configuration-backed runtime factory plus CLI diagnostics/login/logout service, and validated the flow against both a fake app-server and the locally installed `codex app-server`.
- [x] (2026-03-09 00:08Z) Implemented `CodexArchitect`, Codex-specific request/response helpers, factory wiring, and structured `outputSchema` handling for phase2/phase4/phase5/final.
- [x] (2026-03-08) Applied provider-aware Phase 1/Phase 3 Codex exceptions, including runtime-native researcher handling, Codex Phase 3 repo prompts, and shared capability helpers.
- [x] (2026-03-08) Finished Codex CLI workflow polish, added operator docs and gated live smoke coverage, and completed the milestone validation matrix.

## Surprises & Discoveries

- The local `codex-cli 0.111.0` help confirms both `codex exec` and `codex app-server` are available in this environment.
- The generated `codex app-server` JSON schema for `TurnStartParams` includes `outputSchema`, `approvalPolicy`, `sandboxPolicy`, and model overrides, but it does not expose a `collaborationMode` property even though the internal docs discuss that field. The implementation should therefore avoid depending on `collaborationMode` for critical behavior.
- `codex exec` is good enough for one-shot automation and supports JSON output plus `--output-schema`, but it does not expose the account/auth/model-catalog flows that AgentRules needs for a clean runtime integration.
- The first MS001 validation exposed a stale-import bug for the default managed `CODEX_HOME` path. The fix was to resolve `CONFIG_DIR` dynamically inside the Codex config service instead of binding the constant at import time.
- While starting MS002, an unexpected untracked `src/agentrules/core/agents/codex/` directory was present in the worktree. After explicit user confirmation, the implementation treated it as incomplete prior work, audited it, and replaced it with a cleaned tracked version before proceeding.
- A live smoke against the locally installed `codex` binary confirmed the new runtime diagnostics path can initialize app-server and fetch the model catalog even when no ChatGPT account is currently authenticated.
- The generated `codex app-server` schema on this machine does expose `turn/start.outputSchema` and `CollaborationMode`, but keeping `developer_instructions` request-scoped still required a short-lived process strategy because the stable, explicit override surface is the process launch config.
- A live `CodexArchitect.analyze()` smoke against the installed runtime reached the upstream Responses API but failed with `401 Unauthorized` because the local Codex runtime was not authenticated. That confirms the adapter path is wired correctly through the runtime even though a fully authenticated live turn could not be validated on this machine.
- Researcher gating had a second dependency on Tavily beyond runtime execution: the config manager auto-disabled researcher mode when the Tavily key was removed, and the model settings UI blocked entry to the researcher flow when Tavily was absent. Both code paths needed to become provider-aware for Codex to be a real replacement instead of just a hidden runtime path.
- The generic `tests/live/test_live_smoke.py` still assumed API-key providers only. Once Codex became a selectable final-phase preset, that test needed an explicit Codex skip path and xAI env-key coverage to avoid false failures during manual live runs.

## Decision Log

- 2026-03-08: Use Codex app-server as the primary integration surface instead of `codex exec`. Rationale: AgentRules needs programmatic login state, model discovery, and a structured bidirectional protocol, all of which are first-class in app-server and either missing or awkward in `codex exec`.
- 2026-03-08: Model Codex as a dedicated provider (`ModelProvider.CODEX`) rather than overloading the existing OpenAI provider path. Rationale: the transport, auth model, and prompt/file-handling semantics are materially different.
- 2026-03-08: Inject request-scoped system behavior with `codex app-server -c developer_instructions=...` instead of relying on `turn/start.collaborationMode`. Rationale: the startup override is explicitly supported by the CLI, while `collaborationMode` is not present in the generated 0.111.0 schema.
- 2026-03-08: Use short-lived app-server processes for settings actions and Codex architect requests rather than a shared multiplexed daemon. Rationale: request-scoped `developer_instructions` must not bleed between runs, and a process-per-request lifecycle avoids concurrent notification routing and config mutation while keeping the first implementation auditable.
- 2026-03-08: Keep Codex runtime availability separate from provider API-key presence. Rationale: Codex preset visibility should depend on a usable local runtime, not on misusing the `providers.<name>.api_key` configuration store.

## Outcomes & Retrospective

MS001 is complete. AgentRules now has a first-class `ModelProvider.CODEX`, a derived `codex-*` preset family, a dedicated persisted `codex` runtime config section, managed versus inherited `CODEX_HOME` handling, provider-aware preset gating, and a minimal `Settings -> Codex runtime` flow. The remaining risk is intentionally scoped: Codex presets are now selectable, but running analysis with them still fails fast in the factory until the app-server client and `CodexArchitect` land in MS002 and MS003. Validation for MS001 is green with import smoke, `pytest tests/unit -q`, `ruff check src tests`, and `pyright`.

MS002 is now complete as well. AgentRules has a typed `core/agents/codex` transport package, centralized launch-config construction through `ConfigManager.build_codex_launch_config()`, a synchronous CLI runtime service for diagnostics/login/logout/model discovery, and a richer `Settings -> Codex runtime` dashboard that shows live app-server, account, and model-catalog state. Validation is green with `PYTHONPATH=src pytest tests/unit -q -k codex`, `PYTHONPATH=src pytest tests/unit -q`, `PYTHONPATH=src python -c "import agentrules"`, `ruff check src tests`, `pyright`, and a live smoke that initialized the installed `codex app-server` and returned five models from the local runtime.

MS003 is complete. AgentRules can now construct `CodexArchitect` instances from the factory, launch a short-lived Codex app-server per request with request-scoped `developer_instructions`, start ephemeral threads/turns, collect streamed `item/*` and `turn/completed` events, and enforce structured outputs through `turn/start.outputSchema` for the structured phases. Validation is green with `PYTHONPATH=src pytest tests/unit -q -k "codex or architect"`, `PYTHONPATH=src pytest tests/unit -q`, `PYTHONPATH=src python -c "import agentrules"`, `ruff check src tests`, and `pyright`. A live architect smoke reached the installed runtime and failed only because the local Codex account was unauthenticated, which is consistent with the current environment.

MS004 is complete. AgentRules now centralizes Codex-specific runtime branching through shared provider capability helpers, bypasses the Tavily tool loop for Codex-backed researchers, treats Codex researcher presets as valid without Tavily credentials, and routes Phase 3 Codex agents through a repository-runtime prompt path that references assigned files and `cwd` instead of embedding file bodies or invoking the token packer. Validation is green with `PYTHONPATH=src pytest tests/phase_1_test tests/phase_3_test tests/unit -q`, `PYTHONPATH=src pytest tests/phase_1_test/test_phase1_researcher_guards.py tests/unit/analysis/test_phase3_packing.py tests/unit/test_config_service.py tests/unit/utils/test_provider_capabilities.py -q`, `PYTHONPATH=src python -c "import agentrules"`, `ruff check src tests`, and `pyright`.

MS005 is complete. The CLI now exposes testable settings/menu copy that keeps API-key providers separate from the Codex runtime, the researcher status text accurately explains Tavily versus Codex runtime requirements, and the Codex runtime screen includes operator guidance for managed versus inherited `CODEX_HOME` plus next-step hints after sign-in. Operator-facing rollout instructions now live in `docs/codex-runtime.md`, and the repository has a gated live Codex smoke in `tests/live/test_codex_live_smoke.py` that requires both `pytest --run-live` and `AGENTRULES_RUN_CODEX_LIVE=1`. Final validation is green with `PYTHONPATH=src python -c "import agentrules"`, `ruff check src tests`, `pyright`, `PYTHONPATH=src pytest tests/unit tests/offline tests/phase_1_test tests/phase_3_test -q`, `PYTHONPATH=src pytest tests/unit/test_cli_codex_settings.py tests/unit/test_config_service.py tests/unit/test_codex_runtime_service.py tests/live/test_codex_live_smoke.py -q`, `PYTHONPATH=src pytest tests/live/test_codex_live_smoke.py -q --run-live`, and `PYTHONPATH=src python -m agentrules execplan-registry update`.
