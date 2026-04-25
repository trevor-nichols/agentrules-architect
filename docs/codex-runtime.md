# Codex Runtime

AgentRules supports Codex as a local runtime provider through `codex app-server`. This is separate from API-key providers such as OpenAI, Anthropic, Gemini, DeepSeek, and xAI.

## What this integration does

- Launches the local `codex` CLI in app-server mode.
- Reuses ChatGPT login state from `CODEX_HOME` instead of asking AgentRules for an OpenAI API key.
- Surfaces live `Codex: <model>` options from app-server `model/list`, while keeping older `codex-*` aliases for compatibility.
- Keeps structured outputs enabled for the phases that already depend on schemas.

## Configure it

Use `Settings -> Codex runtime`.

That menu controls:

- `Codex executable path`: defaults to `codex` from `PATH`.
- `CODEX_HOME strategy`:
  - `Managed by AgentRules`: AgentRules uses its own Codex home directory.
  - `Inherit existing`: AgentRules reuses the current `CODEX_HOME` / Codex CLI state.
- `Managed CODEX_HOME override`: optional custom path when using managed mode.
- Live runtime inspection: app-server connectivity, account state, and model catalog.

## Choose a `CODEX_HOME` mode

### Managed

Use managed mode when you want AgentRules to keep a separate Codex login and config state.

Behavior:

- Default path: `<AGENTRULES_CONFIG_DIR>/codex`
- ChatGPT login started from AgentRules only affects this managed home
- Good for isolation, testing, and clean rollouts

### Inherit

Use inherit mode when you already use the Codex CLI and want AgentRules to share that login/config state.

Behavior:

- AgentRules reads the existing `CODEX_HOME` from the environment
- If `CODEX_HOME` is unset, AgentRules does not invent one in inherit mode
- Best option when you want AgentRules to reuse your existing ChatGPT login and Codex skills

## Sign in

Codex runtime sign-in is ChatGPT-based.

Flow:

1. Open `Settings -> Codex runtime`
2. Choose `Sign in with ChatGPT`
3. Complete the browser flow
4. Refresh the runtime status
5. Confirm that the account row shows `Signed in`

This uses the Codex app-server auth flow documented in `internal-docs/integrations/codex/app-server/reference/auth.md`.

## Select Codex presets

After the runtime is available:

1. Open `Settings -> Model presets per phase`
2. Pick a `Codex: <model>` option for any phase you want to route through Codex
3. If the model exposes multiple runtime efforts, choose the desired reasoning variant (`no reasoning`, `minimal`, `low`, `medium`, `high`, or `very high`) in the variant picker
4. For Phase 1 researcher, choose a `Codex: <model>` option if you want runtime-native web search instead of Tavily

Notes:

- Codex-backed researchers do not require Tavily credentials
- Non-Codex researcher presets still require Tavily unless you are in offline mode
- Codex-backed Phase 3 agents inspect files from the repository directly instead of receiving embedded file contents
- `Codex: <model>` options come from live app-server `model/list` output and track runtime model availability directly
- Model availability is account- and runtime-dependent; current signed-in runtimes commonly expose models such as `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.3-codex`, `gpt-5.3-codex-spark`, and `gpt-5.2`

## Optional live smoke

The repository includes an opt-in live Codex smoke test.

Run it only when:

- the local `codex` CLI is installed
- you have already signed in through the Codex runtime
- you explicitly want to validate a live structured-output request

Command:

```bash
PYTHONPATH=src pytest tests/live/test_codex_live_smoke.py -q --run-live
```

Environment variables:

- `AGENTRULES_RUN_CODEX_LIVE=1`: required to run the Codex live smoke
- `AGENTRULES_CODEX_CLI`: optional override for the Codex executable path
- `AGENTRULES_CODEX_HOME_STRATEGY`: optional, `inherit` or `managed` (defaults to `inherit`)
- `AGENTRULES_CODEX_MANAGED_HOME`: optional managed-home path when using managed mode
- `AGENTRULES_CODEX_MODEL`: optional explicit live-smoke model override

The live smoke skips itself if the runtime is unavailable or the active Codex home is not authenticated.
