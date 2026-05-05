# Claude Code Runtime

AgentRules supports Claude Code as a local runtime provider through the Anthropic Claude Agent SDK. This is separate from the direct Anthropic API-key provider: Claude Code runtime auth is Claude.ai OAuth subscription auth owned by Claude Code, while the SDK owns default runtime resolution.

## What this integration does

- Uses the Claude Agent SDK runtime through `claude-agent-sdk`; by default AgentRules does not force a specific `claude` executable path.
- Reuses Claude Code OAuth state instead of asking AgentRules for an Anthropic API key.
- Adds `Claude Code ...` model presets that route AgentRules phases through `ModelProvider.CLAUDE_CODE`.
- Keeps structured outputs enabled for schema-backed phases.
- Preserves Claude Code's default system prompt and appends AgentRules phase instructions for each request.
- Treats Claude Code as repository-aware, so Phase 3 agents can inspect files through runtime tools instead of receiving embedded file bodies.

## Configure it

Use `Settings -> Claude Code runtime`.

That menu controls:

- `Claude executable path`: defaults to SDK resolution. Leave it blank unless you need to force a specific command or binary path.
- `Strip Anthropic API-key env`: defaults to yes. This removes `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` from Claude Code child processes.
- Runtime diagnostics: SDK importability, optional explicit executable resolution, `claude --version` for explicit executables, `CLAUDE_CODE_OAUTH_TOKEN` presence, and API-key env visibility after sanitization.
- OAuth guidance: local login and automation setup commands.

## Sign in locally

Claude Code owns the Claude.ai OAuth flow. AgentRules does not perform browser login and does not store OAuth credentials.

Flow:

1. Run Claude Code's OAuth login flow outside AgentRules. If the `claude` command is available in your shell, run `claude auth login`.
2. Complete the Claude.ai OAuth subscription auth flow in Claude Code.
3. Open `Settings -> Claude Code runtime`.
4. Refresh the runtime status.
5. Choose a Claude Code preset under `Settings -> Model presets per phase`.

## Automation and CI

For prepared automation environments, use Claude Code's token setup flow:

```bash
claude setup-token
export CLAUDE_CODE_OAUTH_TOKEN="..."
```

Do not commit or print token values. The AgentRules diagnostics only report whether `CLAUDE_CODE_OAUTH_TOKEN` is present.

## API-Key Precedence

The Claude Agent SDK gives Anthropic API-key variables precedence over Claude.ai OAuth if those variables reach the Claude Code child process. AgentRules strips these variables by default for Claude Code runtime calls:

- `ANTHROPIC_API_KEY`
- `ANTHROPIC_AUTH_TOKEN`

The SDK merges `ClaudeAgentOptions.env` on top of the inherited process environment, so removing these
keys from the per-call environment is not sufficient by itself. When sanitization is enabled,
AgentRules also removes those keys from inherited `os.environ` while the SDK starts the Claude Code
subprocess, then restores the parent process values after the subprocess environment has been built.

This does not change the existing direct Anthropic provider. API-key auth remains supported there; it is intentionally not the auth path for `ModelProvider.CLAUDE_CODE`.

## Prompt behavior

AgentRules sends its phase-specific system instructions as an append block on Claude Code's built-in prompt preset. It does not replace Claude Code's default prompt and does not write prompt instructions into `CLAUDE.md`, `.claude/settings.json`, or other persistent Claude Code files.

This keeps Claude Code's tool guidance, safety instructions, and runtime context intact while making each AgentRules request carry the correct phase behavior.

## Execution guardrails

Claude Code runtime requests run with bounded execution defaults:

- `max_turns = 12`: passed to the Claude Agent SDK as the maximum number of agentic turns for one request.
- `request_timeout_seconds = 300.0`: enforced by AgentRules around the SDK query collection.
- `max_budget_usd = unset`: optional per-request SDK budget ceiling. When unset, AgentRules does not pass a budget limit.
- Token preflight stays local: Claude Code presets use `tiktoken` estimation instead of Anthropic `count_tokens`, so token logging does not depend on parent-process Anthropic credentials or incur Anthropic API usage.

These settings belong in the `[claude_code]` config section when non-default values are needed. The timeout is an AgentRules control and is not passed as a `ClaudeAgentOptions` field.

## CLI Resolution

AgentRules treats a missing `claude_code.cli_path` value as "SDK default." In that mode, `prepare_request()` omits `cli_path` from `ClaudeAgentOptions`, matching the SDK's documented `None` default. Availability checks still validate that the SDK default executable can be resolved before Claude Code presets are offered.

Configure `Claude executable path` only when you need an explicit runtime override. Existing configs
with `cli_path = "claude"` remain valid and are treated as explicit settings; AgentRules resolves
explicit commands and paths before passing them to the SDK. If the configured executable cannot be
resolved, Claude Code presets are gated off and request preparation fails fast until the path is fixed
or cleared.

## Select Claude Code presets

After the runtime is available:

1. Open `Settings -> Model presets per phase`.
2. Pick a `Claude Code ...` option for any phase you want to route through Claude Code.
3. For Phase 1 researcher, choose a Claude Code preset if you want runtime-native web search instead of Tavily.

Notes:

- Claude Code-backed researchers do not require Tavily credentials.
- Non-runtime researcher presets still require Tavily unless you are in offline mode.
- Claude Code-backed Phase 3 agents inspect files from the repository directly instead of receiving embedded file contents.
- Default phase presets are unchanged.

## Offline Validation

Useful local checks:

```bash
PYTHONPATH=src .venv/bin/python -c "import agentrules"
PYTHONPATH=src .venv/bin/pytest tests/unit/agents/test_claude_code_client.py tests/unit/agents/test_claude_code_request_builder.py tests/unit/agents/test_claude_code_response_parser.py tests/unit/agents/test_claude_code_architect.py tests/unit/test_cli_claude_code_settings.py
PYTHONPATH=src .venv/bin/pytest tests/unit/test_config_service.py tests/unit/test_cli_model_picker_ui.py tests/unit/utils/test_provider_capabilities.py tests/unit/utils/test_structured_outputs.py tests/unit/analysis/test_phase3_packing.py
PYTHONPATH=src .venv/bin/ruff check .
PYTHONPATH=src .venv/bin/pyright
```

The offline unit tests use fakes and do not require a live Claude Code login.

## Optional Live Smoke

The repository includes an opt-in live Claude Code smoke test.

Run it only when:

- the Claude Agent SDK is installed, and any explicit `AGENTRULES_CLAUDE_CODE_CLI` override points to a resolvable executable
- Claude Code is authenticated through Claude.ai OAuth or `CLAUDE_CODE_OAUTH_TOKEN`
- you explicitly want to validate a live structured-output request

Command:

```bash
AGENTRULES_RUN_CLAUDE_CODE_LIVE=1 PYTHONPATH=src .venv/bin/pytest --run-live tests/live/test_claude_code_live_smoke.py
```

Environment variables:

- `AGENTRULES_RUN_CLAUDE_CODE_LIVE=1`: required to run the live smoke.
- `AGENTRULES_CLAUDE_CODE_CLI`: optional override for the Claude executable path.
- `AGENTRULES_CLAUDE_CODE_MODEL`: optional explicit live-smoke model override.
- `CLAUDE_CODE_OAUTH_TOKEN`: optional token for automation environments.

The live smoke skips itself if the runtime is unavailable or if Claude Code reports an authentication-related failure.

## Troubleshooting

- Missing Claude executable: install a resolvable Claude Code runtime, clear a broken explicit path to use SDK default resolution, or set `Claude executable path` to the correct command.
- Missing SDK package: install dependencies so `claude-agent-sdk` is available in the AgentRules environment.
- Auth failure: run `claude auth login` locally, or use `claude setup-token` and export `CLAUDE_CODE_OAUTH_TOKEN` for automation.
- API-key precedence: keep `Strip Anthropic API-key env` enabled unless you intentionally want API-key variables to reach Claude Code.
- Permission denial: AgentRules uses non-interactive, read-oriented runtime permissions by default. Confirm the selected preset and runtime have access to the repository path.
- Structured output failure: retry with a current Claude Code preset and inspect the provider result error; schema-backed phases expect valid JSON matching the phase schema.
