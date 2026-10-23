# Provider Model Lifecycle

This guide records model-selection and lifecycle constraints that affect AgentRules operators. It complements the preset labels shown by `agentrules configure --models` and focuses on behavior that cannot be inferred safely from a model ID alone.

## Direct OpenAI API

GPT-6 Astra, GPT-6.1 Sol, GPT-6 Sol, and GPT-6 Luna are reviewed direct-API choices. All use the Responses
API with a 1,050,000-token total context and 128,000-token maximum output, leaving 922,000 tokens for
input before the local packing margin. Astra and 6.1 Sol accept `low`, `medium`, `high`, `xhigh`, and `max`
reasoning; Sol and Luna additionally accept `none`. `minimal` is unsupported for all four. AgentRules
rejects unsupported effort or transport combinations before dispatch and does not silently lower effort.

GPT-5.6 Sol remains the AgentRules phase default pending representative project evaluation. Its Terra and
Luna tiers, plus GPT-5.5, remain explicit rollback choices. GPT-5.6 tiers also have a 922,000-token input
ceiling before the safety margin. Direct GPT-6 availability does not add static Codex runtime models.

The input budget records each model's maximum input after reserving its maximum output from total context.
GPT-5.4 Mini/Nano and GPT-5.3-Codex therefore use 272,000 input tokens, not their 400,000-token total
window. GPT-5.5 uses 922,000 and GPT-4.1 uses 1,014,808 before the packing margin. Phase 3 file content
is JSON-escaped and the packer counts its skeleton once plus each file once.

GPT-5.6 Terra is OpenAI's supported replacement for o4-mini and accepts low, medium, and high reasoning,
so AgentRules exposes matching presets for effort-preserving migrations. The saved keys `o4-mini-low`,
`o4-mini-medium`, and `o4-mini-high` remain bound to their original model while that endpoint is deprecated
but available. The picker hides these keys from new selections, preserves an existing selection with a
deprecation warning, and recommends the matching Terra effort. AgentRules must not change a saved model's
behavior or cost until the original endpoint retires.

GPT-5 Mini's low, medium, and high direct presets follow the same deprecated-but-live policy. They remain
bound to GPT-5 Mini for saved configurations, are hidden from new picker selections, and recommend the
matching GPT-5.6 Terra effort. OpenAI schedules the pinned GPT-5 Mini snapshot to shut down on December 11,
2026; a runtime redirect should only be introduced when that endpoint retires. Its 400,000-token total
context and 128,000-token maximum output leave a 272,000-token maximum input before AgentRules' safety
margin.

Scheduled OpenAI retirement mappings preserve saved wire models until the documented shutdown date, then
resolve each saved key directly to an active preset. GPT-5/o3 route to matching GPT-5.6 Sol efforts on
December 11, 2026; GPT-4.1 routes to GPT-6 Luna on January 14, 2027; GPT-5.1 and GPT-5.3-Codex route to
GPT-6 Sol, and GPT-5.4 Nano routes to GPT-6 Luna, on April 1, 2027. GPT-4.1's temperature variants share
the recommended Luna default after retirement. Picker warnings show deprecated saved selections while
excluding them from new choices.

The direct saved keys `gpt-5.1-codex` and `gpt-5.2-codex` are retired compatibility IDs. They resolve to
the medium-reasoning GPT-5.6 Sol preset before dispatch, preserving the original effort while following
OpenAI's documented replacement. Their static Codex-derived counterparts remain runtime-owned selections:
they are shown only when the app-server catalog reports them, and direct API lifecycle state is not evidence
that a model is available in the local Codex runtime. GPT-5.5 Pro and a GPT-5.6 Pro-mode pseudo-preset remain
excluded because their transport or execution-mode contracts are not represented by the current adapter.

Official references:

- [OpenAI latest model guide](https://developers.openai.com/api/docs/guides/latest-model)
- [GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra)
- [GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
- [GPT-6 Sol](https://developers.openai.com/api/docs/models/gpt-6-sol)
- [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna)
- [OpenAI deprecations](https://developers.openai.com/api/docs/deprecations)
- [GPT-5.6 Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra)
- [GPT-5 Mini](https://developers.openai.com/api/docs/models/gpt-5-mini)
- [o4-mini lifecycle](https://developers.openai.com/api/docs/models/o4-mini)
- [OpenAI model catalog](https://developers.openai.com/api/docs/models/all)

## Direct DeepSeek API

DeepSeek V4.1 Flash (`deepseek-flash`) and V4 Pro (`deepseek-v4-pro`) are the canonical direct-API
choices. Both have 1,000,000-token contexts and
support disabled thinking plus native low, high, and max effort. AgentRules sends an explicit
`thinking.type`; low maps to low, medium/high/xhigh compatibility requests map to high, and max maps to
max. Minimal reasoning fails before dispatch.

Both families retain a 32,000-token AgentRules output cap. This is an application safety limit, not the
provider's advertised 384,000-token output ceiling. Expanding it requires separate cost, latency, and
memory acceptance criteria.

The four saved `deepseek-v4-flash*` preset keys redirect in one step to the matching canonical
`deepseek-flash*` presets. `deepseek-chat` and `deepseek-reasoner` also redirect directly to the
canonical non-thinking and high-thinking presets respectively. DeepSeek temporarily accepts the old V4
Flash wire ID, but serves and bills it as V4.1 Flash; AgentRules sends `deepseek-flash` instead. V4 Pro
remains available. These compatibility keys are not rollback endpoints.

DeepSeek Vision Experimental is not exposed. The current adapter has not established the required image
input, prompt, token, and multimodal response contract.

Official references:

- [DeepSeek model updates](https://api-docs.deepseek.com/updates/)
- [DeepSeek thinking-mode mapping](https://api-docs.deepseek.com/guides/thinking_mode/)
- [DeepSeek model limits](https://api-docs.deepseek.com/quick_start/pricing/)

## Direct Anthropic API

### Claude 5.5 and Fable 5.1

Direct presets use `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-haiku-5-5`, and
`claude-fable-5-1`. Each has a 1M-token context window and 128K maximum output. AgentRules
reserves the full output capacity and packs at most 872K input tokens before its usual safety
margin. A directly constructed `AnthropicArchitect` defaults to Sonnet 5.5 with no up-front
thinking, preserving the old direct constructor's reasoning setting. Opus 5.5 and Haiku 5.5
default to medium effort; Sonnet 5.5 and Fable 5.1 default to high. All four accept low,
medium, high, xhigh, and max effort with adaptive thinking.
Manual thinking budgets are rejected by Anthropic on these models.

Opus 5.5 and Fable 5.1 always use adaptive thinking. Sonnet 5.5 cannot use
`thinking: {"type": "disabled"}`; its **No Upfront Thinking** preset sends
`thinking: {"type": "between_tools"}` at high effort, and progress notes may still appear
between tool calls. Haiku 5.5 can disable thinking at low, medium, or high effort only.
The request builder rejects unsupported mode/effort combinations and output budgets above
128K before dispatch. Structured JSON schemas use `output_config.format`.

Fable 5.1 requires 30-day data retention and is unavailable under zero data retention
unless Anthropic expressly authorizes it. The picker displays this requirement. AgentRules
does not change workspace retention settings. All four new models may return an HTTP 200
response with `stop_reason="refusal"`; direct calls return an explicit refusal error, and
streams hold content until the final message confirms success so partial refused content
cannot be delivered. Automatic fallback is not configured.

Claude Sonnet 4.5 is deprecated but remains live until **November 30, 2026**. Saved
`claude-sonnet` and `claude-sonnet-reasoning` keys keep their Sonnet 4.5 wire model before
that date. From the retirement date, they resolve in one hop to the Sonnet 5.5 No Upfront
Thinking and default adaptive profiles respectively. Other older model choices remain
explicit rollback options where Anthropic still serves them.

### Claude Sonnet 5

`claude-sonnet-5` has a 1,000,000-token context and uses adaptive thinking by default. AgentRules offers an explicit non-thinking preset that sends `thinking: {"type": "disabled"}` plus adaptive presets at low, medium, high, xhigh, and max effort. Manual thinking budgets are not supported. Sonnet 5 remains compatible with zero-data-retention arrangements.

### Claude Fable 5

`claude-fable-5` always uses adaptive thinking, so AgentRules does not offer a disabled-thinking preset and rejects a programmatic `ReasoningMode.DISABLED` configuration before network dispatch. Effort presets range from low through max.

Fable 5 is a Covered Model: it requires 30-day data retention and is unavailable to a workspace that remains under zero data retention. Operators must enable the documented 30-day workspace retention policy before selecting it. AgentRules does not change retention settings or automatically fall back to another model.

Fable 5 can return HTTP 200 with `stop_reason="refusal"`. AgentRules treats that as an error result, includes only the provider's bounded category/explanation summary when present, and never treats empty refusal content as successful analysis. For Fable 5, direct Anthropic streams buffer response chunks until the terminal stop reason is validated, so partial refused output is never exposed; streaming refusals terminate with the same typed error. Models without this refusal capability, including Sonnet 5, continue to stream response chunks immediately. Automatic fallback is intentionally not configured because it would change model behavior and cost.

### Opus compatibility keys

The generic `claude-opus` and `claude-opus-reasoning` preset keys now resolve to Claude Opus 5. Opus 5
has a 1,000,000-token context and uses adaptive thinking by default. AgentRules provides an explicit
disabled-thinking preset and adaptive low, medium, high, xhigh, and max presets; manual thinking budgets
are not supported. When thinking is disabled, Opus 5 accepts only low, medium, or high effort; both the
direct Anthropic and Claude Code request builders reject xhigh or max before dispatch. Explicit Opus 4.8
keys remain registered as the direct-API rollback path.

Direct Opus 5 availability does not establish local Claude Code availability. Programmatic Claude Code
configurations may pin the full `claude-opus-5` model ID; AgentRules permits that path only when the exact
resolved runtime is Claude Code 2.1.219 or newer and fails closed when the version cannot be verified. The
moving `claude-code-opus` alias remains runtime-owned and is not treated as a pinned Opus 5 selection.

Official references:

- [Current Claude model comparison](https://platform.claude.com/docs/en/models/overview)
- [Thinking modes](https://platform.claude.com/docs/en/build-with-claude/thinking)
- [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
- [Stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)
- [Context window accounting](https://platform.claude.com/docs/en/build-with-claude/context-windows)
- [Claude Sonnet 5 changes](https://platform.claude.com/docs/en/about-claude/models/whats-new-sonnet-5)
- [Claude Fable 5 introduction](https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5)
- [Claude Code v2.1.219 release](https://github.com/anthropics/claude-code/releases/tag/v2.1.219)
- [Adaptive thinking](https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking)
- [Refusals and fallback](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback)
- [API and data retention](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)
- [Model deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations)
- [Claude Opus 5 changes](https://platform.claude.com/docs/en/models/opus-5/whats-new-opus-5)
- [Effort controls](https://platform.claude.com/docs/en/build-with-claude/effort)

## Direct xAI API

### Grok 4.7

`grok-4.7` is the recommended direct xAI selection. A directly constructed `XaiArchitect`
continues to default to `grok-4.6` pending the representative-project evaluation in MS008. Grok 4.7
has a 500,000-token context and accepts low, medium, high, or xhigh reasoning effort;
high is the provider default. It supports Chat Completions tool calling and JSON-schema structured
output. Reasoning cannot be disabled. AgentRules rejects disabled, minimal, max, and temperature
configurations before network dispatch rather than translating them to an unsupported wire value.

Grok 4.6 remains registered as the immediate direct-API fallback with low, medium, high, and xhigh
effort. Grok 4.5 is also retained with low, medium, and high effort. Grok 4.7 Fast is not exposed
because xAI has not made it available on the public API.

### Grok 4.20 pinned variants

AgentRules exposes `grok-4.20-0309-reasoning` and `grok-4.20-0309-non-reasoning` as specialized,
pinned Chat Completions choices with 1,000,000-token contexts. Their reasoning behavior is selected by
the model ID, so AgentRules does not add a `reasoning_effort` field that xAI has not documented for
those variants.

Grok 4.20 Multi-Agent is not exposed. xAI explicitly states that it does not work with Chat
Completions and requires the xAI SDK or Responses API. AgentRules' current xAI adapter intentionally
remains Chat-Completions-only, so adding a Multi-Agent preset would guarantee a runtime failure.

Official references:

- [Grok 4.7](https://docs.x.ai/developers/grok-4-7)
- [Grok 4.6](https://docs.x.ai/developers/models/grok-4.6)
- [xAI reasoning controls](https://docs.x.ai/developers/model-capabilities/text/reasoning)
- [xAI structured outputs](https://docs.x.ai/developers/model-capabilities/text/structured-outputs)
- [Grok 4.20 reasoning model](https://docs.x.ai/developers/models/grok-4.20-0309-reasoning)
- [Grok 4.20 non-reasoning model](https://docs.x.ai/developers/models/grok-4.20-0309-non-reasoning)
- [Multi-Agent endpoint limitations](https://docs.x.ai/developers/model-capabilities/text/multi-agent)

## Google Gemini API

Direct `gemini-3.8-flash` and `gemini-4-argon` presets expose low, medium, and high thinking.
Minimal and disabled reasoning fail before dispatch. Flash accepts 1,048,576 input tokens and requests
up to 65,536 output tokens. Argon's 1,048,576-token window includes input, thinking, and output, so
AgentRules reserves 65,536 tokens for generation and limits packed input to 983,040 before its safety
margin. Its SDK request uses automatic continuation, a 65,536-token generation limit, and a 20-minute
timeout; a single non-streaming API hop is capped at 32,768 tokens. Researcher tool turns retain the
complete model content (including thought signatures) and return matching function-call IDs and names.
AgentRules requires `google-genai>=2.30.1` for this continuation behavior.

`gemini-3.7-flash` remains an AgentRules preset and API wire ID, but Google automatically serves it as
3.8 Flash. It has a 1,048,576-token input context, defaults to medium thinking, and accepts exactly low,
medium, or high. Disabled and minimal requests fail before dispatch rather than being raised to low.

`gemini-3.6-flash` defaults to medium and accepts minimal, low, medium, or high. The throughput-oriented
`gemini-3.5-flash-lite` defaults to minimal and accepts the same four levels. All three families support
tools together with structured output. Their capability profiles require the installed SDK to expose the
requested exact level; the required SDK includes `MINIMAL` and `MEDIUM`, and AgentRules does not silently
select a nearby enum value.

The older explicit `gemini-3.5-flash` key also remains registered; Google automatically serves API
requests to that ID as 3.6 Flash. Saved keys and wire IDs stay unchanged, while picker labels disclose
the provider-side effective model.

Gemini 2.5 Flash and Pro are **not deprecated** and have no announced shutdown date. Google limits access
to users who previously used them and recommends newer models for new projects. AgentRules keeps these
explicit choices available for existing users without a premature redirect. Picker labels disclose the
access condition rather than claiming an October 16, 2026 shutdown.

The saved keys `gemini-3-pro-preview` and `gemini-3.1-flash-lite-preview` remain loadable for backwards
compatibility, but runtime resolution sends `gemini-3.1-pro-preview` and `gemini-3.1-flash-lite`. The
picker labels disclose those redirects so operators do not mistake compatibility keys for live endpoints.

Official references:

- [Gemini model catalog](https://ai.google.dev/gemini-api/docs/models)
- [Gemini 3.8 Flash model card](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash)
- [Gemini 4 Argon model card](https://ai.google.dev/gemini-api/docs/models/gemini-4-argon)
- [Argon GenerateContent and continuation guide](https://ai.google.dev/gemini-api/docs/generate-content/latest-model)
- [Gemini 3.8 function-call migration rules](https://ai.google.dev/gemini-api/docs/generate-content/whats-new-gemini-3.8)
- [Gemini thinking levels](https://ai.google.dev/gemini-api/docs/generate-content/thinking)
- [Gemini model deprecations](https://ai.google.dev/gemini-api/docs/deprecations)
- [Google Gen AI Python SDK changelog](https://github.com/googleapis/python-genai/blob/main/CHANGELOG.md#1560-2025-12-16)

## Local runtime providers

Codex and Claude Code are runtime providers, not static API model catalogs. Codex choices and reasoning
efforts come from app-server `model/list`; the runtime default follows the installed build and account.
AgentRules preserves new short lowercase effort values reported by that catalog, including values newer
than the application, but rejects malformed tokens. It does not add static Codex GPT-5.6 presets.

Claude Code offers a runtime-owned default and moving `best`, `sonnet`, `opus`, `fable`, and `haiku` aliases as
well as pinned model IDs. Moving selections intentionally have no static AgentRules context limit because
the runtime owns concrete-model resolution. Pinned Claude 5 choices fail closed when AgentRules cannot
prove that the exact resolved bundled or configured Claude Code executable meets the model's minimum
version. Fable 5.1 needs Claude Code 2.1.257+, Opus 5.5 needs 2.1.280+, Sonnet 5.5 needs 2.1.284+,
and Haiku 5.5 needs 2.1.293+. The lockfile resolves Claude Agent SDK 0.2.173, whose bundled CLI is
2.1.309. A newer global binary does not upgrade the SDK-bundled runtime automatically.

See [`codex-runtime.md`](codex-runtime.md) and [`claude-code-runtime.md`](claude-code-runtime.md) for
configuration, authentication, version diagnostics, and runtime-specific live smokes.

## Optional direct-provider live smoke

The direct-provider smoke suite is disabled unless all three gates are satisfied: `pytest --run-live`, a
provider-specific `AGENTRULES_RUN_<PROVIDER>_LIVE=1` flag, and that provider's API key. Every request is
limited to 32 output tokens, assertions retain only a response identifier or boolean evidence, and the
suite does not print credentials or raw responses. Account-, region-, or quota-specific 403/404/429
responses are recorded as skips; request-contract errors still fail.

Example for OpenAI:

```bash
AGENTRULES_RUN_OPENAI_LIVE=1 \
  .venv/bin/pytest --run-live tests/live/test_provider_model_live_smoke.py -k openai
```

Equivalent enable flags are available for `ANTHROPIC`, `GEMINI`, `DEEPSEEK`, and `XAI`. Override the
default smoke model with `AGENTRULES_<PROVIDER>_LIVE_MODEL`. Running the file without those flags must
skip every provider and make no paid request.

## Rollback and fallback summary

| Provider | Preferred fallback | Important restriction |
| --- | --- | --- |
| OpenAI | GPT-5.6 Sol, then GPT-5.5 | Keep saved GPT-6 and GPT-5.6 keys registered; leave the phase default on GPT-5.6 Sol pending evaluation. |
| DeepSeek | V4.1 Flash | Use `deepseek-flash`; old V4 Flash and Chat/Reasoner keys are compatibility selections. |
| Anthropic | Claude Opus 4.8 | Keep explicit Opus 5 keys registered; do not auto-fallback from a Fable refusal. |
| xAI | Grok 4.6, then 4.5 | Do not select Multi-Agent through the Chat Completions adapter. |
| Google | Gemini 3.5 Flash API ID (served as 3.6 Flash) | Gemini 2.5 has no announced shutdown; preserve existing selections and check prior-user access. |
| Codex | Runtime default | Let the authenticated runtime catalog choose; do not synthesize a static model ID. |
| Claude Code | Runtime default | Use a pinned model only after the resolved runtime passes its minimum-version gate. |
