# Provider Model Lifecycle

This guide records model-selection and lifecycle constraints that affect AgentRules operators. It complements the preset labels shown by `agentrules configure --models` and focuses on behavior that cannot be inferred safely from a model ID alone.

## Direct OpenAI API

The direct API presets include GPT-6.2 Astra, GPT-6.2 Sol, GPT-6.1 Terra, GPT-6.1 Sol, GPT-6 Astra,
GPT-6 Sol, and GPT-6 Luna. AgentRules uses the Responses API with function calling and structured
outputs on the existing OpenAI Python SDK requirement (`openai>=2.45.0`). These models have a
1,050,000-token context and a 128,000-token output limit. AgentRules budgets 922,000 input tokens
before its packing margin.

All seven models accept `low`, `medium`, `high`, `xhigh`, and `max` reasoning. GPT-6.1 Terra,
GPT-6 Sol, and GPT-6 Luna also accept `none`. AgentRules rejects unsupported effort or transport
combinations before dispatch.

GPT-5.6 Sol remains the AgentRules phase default pending representative project evaluation. Its Terra and
Luna tiers, plus GPT-5.5, remain explicit rollback choices. GPT-5.6 tiers also have a 922,000-token input
ceiling before the safety margin. Direct GPT-6 availability does not add static Codex runtime models.

The input budget records each model's maximum input after reserving its maximum output from total context.
GPT-5.4 Mini/Nano and GPT-5.3-Codex therefore use 272,000 input tokens, not their 400,000-token total
window. GPT-5.5 uses 922,000 and GPT-4.1 uses 1,014,808 before the packing margin. Phase 3 file content
is JSON-escaped and the packer counts its skeleton once plus each file once.

OpenAI retired o4-mini on October 23, 2026. The saved keys `o4-mini-low`, `o4-mini-medium`, and
`o4-mini-high` now resolve to `gpt56-terra-low`, `gpt56-terra-default` (medium), and `gpt56-terra-high`
respectively. The picker shows the replacement for an existing selection. Loading the configuration
preserves the saved key and uses the matching Terra effort for requests.

Scheduled retirement mappings keep the original API model until the documented shutdown date, then
resolve the saved key directly to an active preset. The picker shows the effective replacement for a
deprecated saved selection and hides deprecated presets from new choices.

On December 11, 2026, saved GPT-5 and o3 presets switch to GPT-6.1 Sol, and GPT-5 Mini presets switch
to GPT-6.1 Terra. The replacement keeps the saved effort where supported. The `gpt5-minimal` preset
switches to `low` because GPT-6.1 Sol requires at least low reasoning. Before the cutover, GPT-5 Mini
uses a 272,000-token input ceiling before the packing margin.

GPT-4.1 temperature presets switch to the GPT-6 Luna default on January 14, 2027. On April 1, 2027,
GPT-5.1 and GPT-5.3-Codex switch to GPT-6 Sol, and GPT-5.4 Nano switches to GPT-6 Luna.

The direct saved keys `gpt-5.1-codex` and `gpt-5.2-codex` are retired compatibility IDs. They resolve to
the medium-reasoning GPT-5.6 Sol preset before dispatch, preserving the original effort while following
OpenAI's documented replacement. Their static Codex-derived counterparts remain runtime-owned selections:
they are shown only when the app-server catalog reports them, and direct API lifecycle state is not evidence
that a model is available in the local Codex runtime. GPT-5.5 Pro and a GPT-5.6 Pro-mode pseudo-preset remain
excluded because their transport or execution-mode contracts are not represented by the current adapter.

Official references:

- [OpenAI latest model guide](https://developers.openai.com/api/docs/guides/latest-model)
- [GPT-6.2 Astra](https://developers.openai.com/api/docs/models/gpt-6.2-astra)
- [GPT-6.2 Sol](https://developers.openai.com/api/docs/models/gpt-6.2-sol)
- [GPT-6.1 Terra](https://developers.openai.com/api/docs/models/gpt-6.1-terra)
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

### Phase 1 researcher tool turns

Phase 1 continues DeepSeek tool calls on Chat Completions. It sends the original system and user
messages, then appends each assistant turn with its original content, `reasoning_content`, and tool
calls. Each tool result uses the matching `tool_call_id`, even when two calls use the same tool or a
tool fails. In thinking mode, DeepSeek expects the original reasoning on follow-up requests that
include tools. AgentRules keeps this replay history in memory for the research run and leaves it out
of phase artifacts. [DeepSeek thinking-mode tool calls](https://api-docs.deepseek.com/guides/thinking_mode/#tool-calls)

DeepSeek Vision Experimental is not exposed. The current adapter has not established the required image
input, prompt, token, and multimodal response contract.

Official references:

- [DeepSeek model updates](https://api-docs.deepseek.com/updates/)
- [DeepSeek thinking-mode mapping](https://api-docs.deepseek.com/guides/thinking_mode/)
- [DeepSeek model limits](https://api-docs.deepseek.com/quick_start/pricing/)

## Direct Anthropic API

### Claude 5.5 and Fable 5.2

Direct presets use `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-haiku-5-5`,
`claude-fable-5-2`, and `claude-fable-5-1`. Each has a 1M-token context window and 128K
maximum output. AgentRules reserves the full output capacity and packs at most 872K input
tokens before its usual safety margin. A directly constructed `AnthropicArchitect` defaults
to Sonnet 5.5 with no up-front thinking. Opus 5.5 and Haiku 5.5 default to medium effort.
Sonnet 5.5, Fable 5.2, and Fable 5.1 default to high. All five accept `low`, `medium`,
`high`, `xhigh`, and `max` effort with adaptive thinking.

Opus 5.5 and both Fable releases always use adaptive thinking. Sonnet 5.5's **No Upfront
Thinking** preset sends `thinking: {"type": "between_tools"}` at high effort, and progress
notes may still appear between tool calls. Haiku 5.5 can disable thinking at low, medium, or
high effort only. The request builder rejects unsupported thinking and effort combinations,
manual budgets, and output budgets above 128K before dispatch. Fable 5.2 accepts `auto` and
`none` for tool choice. Forcing a tool call returns an API error.

Fable 5.2 and 5.1 are Covered Models with a 30-day retention requirement. The picker displays
that requirement. Organizations using legacy zero data retention need Anthropic's express
authorization. Eligible organizations can use Enterprise Frontier Safeguards ZDR. Structured
JSON schemas use `output_config.format`. Organizations using customer-managed encryption
keys (CMEK) need another model for schema-backed phases or strict tools with either Fable
release.

Claude can return HTTP 200 with `stop_reason="refusal"` on any of these models. AgentRules
reports the provider's refusal as a typed error with bounded details. Streams buffer output
until the terminal stop reason is checked and discard buffered content on refusal.

Claude Sonnet 4.5 is deprecated but remains live until **November 30, 2026**. Saved
`claude-sonnet` and `claude-sonnet-reasoning` keys keep their Sonnet 4.5 wire model before
that date. From the retirement date, they resolve in one hop to the Sonnet 5.5 No Upfront
Thinking and default adaptive profiles respectively. Other older model choices remain
explicit rollback options where Anthropic still serves them.

Anthropic retires **Claude Opus 4.5 on January 22, 2027**. Before then, `claude-opus-4.5` and
`claude-opus-4.5-reasoning` continue to use Opus 4.5. On that date, the saved keys resolve to
`claude-opus-5.5-reasoning-low` and `claude-opus-5.5-reasoning-high` respectively. The plain Opus
4.5 preset previously disabled thinking. Its replacement uses adaptive thinking at low effort.

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
- [Fable 5.2 migration guide](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide)
- [Claude model deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations)
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

xAI retired Grok Build 0.1 on November 19, 2026. Saved `grok-build-0.1` and `grok-code-fast` presets
both resolve directly to `grok-4.7` at high reasoning effort. The picker shows Grok 4.7 as the replacement
for either saved key.

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
- [xAI release notes](https://docs.x.ai/developers/release-notes)
- [Grok 4.6](https://docs.x.ai/developers/models/grok-4.6)
- [xAI reasoning controls](https://docs.x.ai/developers/model-capabilities/text/reasoning)
- [xAI structured outputs](https://docs.x.ai/developers/model-capabilities/text/structured-outputs)
- [Grok 4.20 reasoning model](https://docs.x.ai/developers/models/grok-4.20-0309-reasoning)
- [Grok 4.20 non-reasoning model](https://docs.x.ai/developers/models/grok-4.20-0309-non-reasoning)
- [Multi-Agent endpoint limitations](https://docs.x.ai/developers/model-capabilities/text/multi-agent)

## Google Gemini API

Choose a Gemini 4 preset in `agentrules configure --models`.

| Wire model | Supported thinking levels | Preset default | Gemini Developer API tier |
| --- | --- | --- | --- |
| `gemini-4-carbon` | `low`, `medium`, `high` | `medium` | Paid |
| `gemini-4-hydrogen` | `low`, `medium`, `high`, `xhigh` | `high` | Free or paid |
| `gemini-4-neon` | `low`, `medium`, `high`, `xhigh` | `high` | Paid |
| `gemini-4-argon` | `low`, `medium`, `high` | `medium` | Paid |

AgentRules requires `google-genai>=3.3.0` for the native `XHIGH` thinking level. The lockfile pins
3.6.1. AgentRules validates the exact level before sending the request. Gemini 4 rejects minimal
and disabled thinking.

Gemini 4 shares a 1,048,576-token window across input, thinking, and output. AgentRules reserves
65,536 tokens for generation and caps packed input at 983,040 tokens before the safety margin. The
GenerateContent adapter requests up to 65,536 output tokens with SDK automatic continuation and a
20-minute client timeout. Carbon and Argon cap each direct non-streaming REST response at 32,768
tokens. Hydrogen and Neon support up to 65,536 tokens per request. Google's long decode can continue
beyond 65,536 output tokens when a client requests a larger output budget within the shared window.

Researcher tool turns keep the complete model content, including thought signatures, and send
responses with matching function-call IDs and names. Google offers combined tool use and structured
output on Gemini 4 as a preview feature.

The Google Gen AI SDK 3 defaults the Gemini Developer API to `v1`. AgentRules chooses `v1beta` for
Developer API clients to retain access to preview models. Set `GOOGLE_GENAI_API_VERSION` to select
another API version. Managed Gemini Enterprise or Vertex AI clients use the SDK's version selection.

The direct `gemini-3.8-flash` presets expose low, medium, and high thinking. The model accepts
1,048,576 input tokens and AgentRules requests up to 65,536 output tokens.

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

Google deprecates Gemini 2.5 Flash and Pro and limits access to existing users. Starting **December 1,
2026**, Google serves their API IDs with replacement models and charges the replacement rates. AgentRules
uses the replacement IDs and their request profiles from that date so thinking and tool fields match the
effective model.

| Saved preset | Effective preset from December 1, 2026 |
| --- | --- |
| `gemini-pro` | `gemini-3.8-flash` with medium thinking |
| `gemini-flash` | `gemini-3.5-flash-lite` with minimal thinking |
| `gemini-flash-thinking` | `gemini-3.5-flash-lite-reasoning-medium` with medium thinking |

The plain `gemini-flash` preset previously disabled thinking. Its replacement uses minimal thinking.
Gemini 2.5 Flash-Lite remains available under Google's existing access policy. A `GeminiArchitect()` or
legacy `GeminiAgent()` constructed without model or reasoning overrides uses `gemini-3.5-flash-lite`
with minimal thinking.

The saved keys `gemini-3-pro-preview` and `gemini-3.1-flash-lite-preview` remain loadable for backwards
compatibility, but runtime resolution sends `gemini-3.1-pro-preview` and `gemini-3.1-flash-lite`. The
picker labels disclose those redirects so operators do not mistake compatibility keys for live endpoints.

Official references:

- [Gemini 4 model catalog](https://aistudio.google.com/docs/models#gemini-4)
- Model cards for [Carbon](https://aistudio.google.com/docs/models/gemini-4-carbon),
  [Hydrogen](https://aistudio.google.com/docs/models/gemini-4-hydrogen),
  [Neon](https://aistudio.google.com/docs/models/gemini-4-neon), and
  [Argon](https://aistudio.google.com/docs/models/gemini-4-argon)
- [Gemini thinking levels](https://aistudio.google.com/docs/thinking#understanding-thinking-levels)
- [GenerateContent long decode](https://aistudio.google.com/docs/long-decode?generate-content=true)
- [GenerateContent structured output with tools](https://aistudio.google.com/docs/structured-output?generate-content=true#structured-outputs-with-tools)
- [Gemini 3.8 Flash model card](https://aistudio.google.com/docs/models/gemini-3.8-flash)
- [Gemini 3.8 function-call migration rules](https://ai.google.dev/gemini-api/docs/generate-content/whats-new-gemini-3.8)
- [Gemini model deprecations](https://aistudio.google.com/docs/deprecations)
- [Google Gen AI Python SDK 3.0 migration notes](https://github.com/googleapis/python-genai/releases/tag/v3.0.0)
- [SDK 3.3 native `XHIGH` support](https://github.com/googleapis/python-genai/releases/tag/v3.3.0)

## Local runtime providers

Codex and Claude Code are runtime providers, not static API model catalogs. Codex choices and reasoning
efforts come from app-server `model/list`; the runtime default follows the installed build and account.
GPT-6.2 Astra and Sol require Codex CLI 0.166.0 or later. Check the exact configured executable and
refresh its account-specific catalog using the [Codex runtime guide](codex-runtime.md).
AgentRules preserves new short lowercase effort values reported by that catalog, including values newer
than the application, but rejects malformed tokens. It does not add static Codex GPT-5.6 presets.

Claude Code resolves the runtime default and moving aliases such as `best` and `fable`.
For pinned models, AgentRules verifies and launches the same bundled or configured executable.
The Fable 5.2 pin uses medium effort and requires Claude Code 2.1.321 or later. The project
requires Claude Agent SDK 0.2.180 or later. The lockfile resolves SDK 0.2.189, which bundles
CLI 2.1.332.

See [`codex-runtime.md`](codex-runtime.md) and [`claude-code-runtime.md`](claude-code-runtime.md) for
configuration, authentication, version diagnostics, and runtime-specific live smokes.

## Direct API transport status

AgentRules retains its current direct transports for this release. The October 31, 2026 offline
contract review found no model requirement that forces a production migration. A future switch needs
a separate review of request, tool, stream, parser, and retention behavior.

| Provider | Current AgentRules path | Migration consideration |
| --- | --- | --- |
| xAI | Chat Completions remains available for Grok 4.7 and fallback models. xAI marks it deprecated. | See the separate Responses proposal below. [xAI API comparison](https://docs.x.ai/developers/model-capabilities/text/comparison) |
| Anthropic | Python SDK 0.83 and Messages API version `2023-06-01`; the dependency is bounded below 2.0 | [SDK 2.x / API `2026-10-21`](https://platform.claude.com/docs/en/api/migration-2026-10-21) changes API-key transport from `X-Api-Key` to `Authorization: Bearer`, affecting gateways; it also removes sampling parameters. Current 5.5/Fable request contracts are covered offline on the existing path. |
| Gemini | GenerateContent with full signed model-turn replay for tools | [Interactions](https://ai.google.dev/gemini-api/docs/interactions-overview) introduces typed steps and optional server-side state. Its default stored requests have different retention; `store=false` cannot continue with `previous_interaction_id`. GenerateContent remains supported. |

OpenAI direct models use Responses, and [DeepSeek Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/)
remains a documented current endpoint. The dated source comparison, offline probes, rollback paths, and
revisit triggers are recorded in the provider refresh ExecPlan.

### Proposed xAI Responses migration

This release keeps the xAI Chat Completions adapter and the shared OpenAI Python SDK. Evaluate
`/v1/responses` in a separate review. xAI stores Responses API input and output for 30 days by
default. Use `store=false` as the evaluation baseline to preserve client-managed history. Reassess
retention explicitly before adopting server-managed history. [xAI migration guide](https://docs.x.ai/developers/model-capabilities/text/comparison)

- Map `messages` to `input`, `max_tokens` to `max_output_tokens`, and supported reasoning controls to
  their Responses fields. Translate function declarations to the Responses tool shape and structured
  output schemas to `text.format`. Match each `function_call_output` to the original `call_id`.
  [Request mapping](https://docs.x.ai/developers/model-capabilities/text/comparison)
  · [Schemas and tools](https://docs.x.ai/developers/model-capabilities/text/structured-outputs)
- Request `reasoning.encrypted_content` and replay the original typed output items in order before
  appending tool results. Grok 4.7 includes encrypted reasoning by default, while earlier reasoning
  models require an explicit request for it. Keep the history in the client when `store=false`.
  Use `response.output_text.delta` for display and take completed output items from
  `response.completed`. Handle `response.incomplete` as an incomplete result, and verify that partial
  output cannot pass structured-output validation.
  [Reasoning replay](https://docs.x.ai/developers/advanced-api-usage/troubleshooting-reasoning)
  · [Streaming events](https://docs.x.ai/developers/model-capabilities/text/streaming)
- Verify the provider endpoint and deployments using `XAI_API_BASE` or an explicit `base_url`.
  Some custom gateways may implement only Chat Completions. Use the locked shared SDK for an
  initial compatibility probe, and test the direct OpenAI, xAI, and DeepSeek adapters if an SDK
  change is needed.

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
| Google | Gemini 3.5 Flash API ID (served as 3.6 Flash) | Saved Gemini 2.5 Flash and Pro selections switch to their replacement request profiles on December 1, 2026. |
| Codex | Runtime default | Let the authenticated runtime catalog choose; do not synthesize a static model ID. |
| Claude Code | Runtime default | Use a pinned model only after the resolved runtime passes its minimum-version gate. |
