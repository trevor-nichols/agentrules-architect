# Provider Model Lifecycle

This guide records model-selection and lifecycle constraints that affect AgentRules operators. It complements the preset labels shown by `agentrules configure --models` and focuses on behavior that cannot be inferred safely from a model ID alone.

## Direct OpenAI API

GPT-5.6 Sol is the default AgentRules preset. Terra and Luna remain explicit alternative tiers, and all
three use the Responses API with a 1,050,000-token context. Sol accepts `none`, `low`, `medium`, `high`,
`xhigh`, and `max` reasoning; AgentRules sends the selected value without reducing `max` to an older
effort. GPT-5.5 presets remain available as the immediate fallback when account availability or behavior
requires a conservative rollback.

GPT-5 Mini has low, medium, and high direct presets with a 400,000-token context. OpenAI identifies it as
the successor to o4-mini, but the saved keys `o4-mini-low`, `o4-mini-medium`, and `o4-mini-high` remain
bound to their original model while that endpoint is deprecated but available. The picker hides these
keys from new selections, preserves an existing selection with a deprecation warning, and recommends the
matching GPT-5 Mini effort as an operator-selected migration. AgentRules must not change a saved model's
behavior or cost until the original endpoint retires.

The direct saved keys `gpt-5.1-codex` and `gpt-5.2-codex` likewise remain bound to their original models
while the endpoints are deprecated but available. Their static Codex-derived counterparts preserve the
same identity subject to runtime availability. GPT-5.3 Codex is recommended for new configurations, but
it is not an automatic compatibility redirect before retirement. Direct API lifecycle state is not
evidence that a model is available in the local Codex runtime. GPT-5.5 Pro and a GPT-5.6 Pro-mode
pseudo-preset remain excluded because their transport or execution-mode contracts are not represented by
the current adapter.

Official references:

- [OpenAI latest model guide](https://developers.openai.com/api/docs/guides/latest-model)
- [GPT-5 Mini](https://developers.openai.com/api/docs/models/gpt-5-mini)
- [o4-mini lifecycle](https://developers.openai.com/api/docs/models/o4-mini)
- [OpenAI model catalog](https://developers.openai.com/api/docs/models/all)

## Direct DeepSeek API

DeepSeek V4 Flash and V4 Pro are the canonical direct-API choices. Both have 1,000,000-token contexts and
support disabled thinking plus native low, high, and max effort. AgentRules sends an explicit
`thinking.type`; low maps to low, medium/high/xhigh compatibility requests map to high, and max maps to
max. Minimal reasoning fails before dispatch.

Both families retain a 32,000-token AgentRules output cap. This is an application safety limit, not the
provider's advertised 384,000-token output ceiling. Expanding it requires separate cost, latency, and
memory acceptance criteria.

The saved preset keys `deepseek-chat` and `deepseek-reasoner` redirect to V4 Flash with disabled and
enabled/high thinking respectively. DeepSeek scheduled those legacy identifiers to become inaccessible
on July 24, 2026, so they are compatibility keys rather than valid rollback endpoints. If a V4 Pro issue
appears, use V4 Flash; do not restore the retired wire identifiers.

DeepSeek Vision Experimental is not exposed. The current adapter has not established the required image
input, prompt, token, and multimodal response contract.

Official references:

- [DeepSeek model updates](https://api-docs.deepseek.com/updates/)
- [DeepSeek thinking-mode mapping](https://api-docs.deepseek.com/guides/thinking_mode/)
- [DeepSeek model limits](https://api-docs.deepseek.com/quick_start/pricing/)

## Direct Anthropic API

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
are not supported. Explicit Opus 4.8 keys remain registered as the direct-API rollback path.

Direct Opus 5 availability does not establish local Claude Code availability. AgentRules does not expose a
pinned Claude Code Opus 5 preset until the exact resolved runtime can be gated against a documented minimum
version; the moving `claude-code-opus` alias remains runtime-owned.

Official references:

- [Claude Sonnet 5 changes](https://platform.claude.com/docs/en/about-claude/models/whats-new-sonnet-5)
- [Claude Fable 5 introduction](https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5)
- [Adaptive thinking](https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking)
- [Refusals and fallback](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback)
- [API and data retention](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)
- [Model deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations)
- [Claude Opus 5 changes](https://platform.claude.com/docs/en/models/opus-5/whats-new-opus-5)
- [Effort controls](https://platform.claude.com/docs/en/build-with-claude/effort)

## Direct xAI API

### Grok 4.6

`grok-4.6` is the recommended direct xAI model and the default for a directly constructed
`XaiArchitect`. It has a 500,000-token context and accepts low, medium, high, or xhigh reasoning effort;
high is the provider default. Reasoning cannot be disabled. AgentRules rejects disabled, minimal, and max
configurations before network dispatch rather than translating them to an unsupported wire value.

Grok 4.5 remains registered as the immediate direct-API fallback with low, medium, and high effort.

### Grok 4.20 pinned variants

AgentRules exposes `grok-4.20-0309-reasoning` and `grok-4.20-0309-non-reasoning` as specialized,
pinned Chat Completions choices with 1,000,000-token contexts. Their reasoning behavior is selected by
the model ID, so AgentRules does not add a `reasoning_effort` field that xAI has not documented for
those variants.

Grok 4.20 Multi-Agent is not exposed. xAI explicitly states that it does not work with Chat
Completions and requires the xAI SDK or Responses API. AgentRules' current xAI adapter intentionally
remains Chat-Completions-only, so adding a Multi-Agent preset would guarantee a runtime failure.

Official references:

- [Grok 4.6](https://docs.x.ai/developers/models/grok-4.6)
- [xAI reasoning controls](https://docs.x.ai/developers/model-capabilities/text/reasoning)
- [Grok 4.20 reasoning model](https://docs.x.ai/developers/models/grok-4.20-0309-reasoning)
- [Grok 4.20 non-reasoning model](https://docs.x.ai/developers/models/grok-4.20-0309-non-reasoning)
- [Multi-Agent endpoint limitations](https://docs.x.ai/developers/model-capabilities/text/multi-agent)

## Google Gemini API

`gemini-3.7-flash` is AgentRules' recommended current Flash choice. It has a 1,048,576-token input
context, defaults to medium thinking, and accepts exactly low, medium, or high. Disabled and minimal
requests fail before dispatch rather than being raised to low.

`gemini-3.6-flash` defaults to medium and accepts minimal, low, medium, or high. The throughput-oriented
`gemini-3.5-flash-lite` defaults to minimal and accepts the same four levels. All three families support
tools together with structured output. Their capability profiles require the installed SDK to expose the
requested exact level; AgentRules requires `google-genai>=1.56.0`, the first SDK release with `MINIMAL`
and `MEDIUM`, and does not silently select a nearby enum value.

The older explicit `gemini-3.5-flash` choice remains registered as a rollback path.
Gemini 2.5 Flash and Gemini 2.5 Pro remain selectable until their documented October 16, 2026
shutdown because silently changing an explicit active selection could alter behavior or cost. Their picker
labels disclose the date and recommend Gemini 3.5 Flash or Gemini 3.1 Pro Preview respectively.

The saved keys `gemini-3-pro-preview` and `gemini-3.1-flash-lite-preview` remain loadable for backwards
compatibility, but runtime resolution sends `gemini-3.1-pro-preview` and `gemini-3.1-flash-lite`. The
picker labels disclose those redirects so operators do not mistake compatibility keys for live endpoints.

Official references:

- [Gemini model catalog](https://ai.google.dev/gemini-api/docs/models)
- [Gemini thinking levels](https://ai.google.dev/gemini-api/docs/generate-content/thinking)
- [Gemini model deprecations](https://ai.google.dev/gemini-api/docs/deprecations)
- [Google Gen AI Python SDK changelog](https://github.com/googleapis/python-genai/blob/main/CHANGELOG.md#1560-2025-12-16)

## Local runtime providers

Codex and Claude Code are runtime providers, not static API model catalogs. Codex choices and reasoning
efforts come from app-server `model/list`; the runtime default follows the installed build and account.
AgentRules preserves new short lowercase effort values reported by that catalog, including values newer
than the application, but rejects malformed tokens. It does not add static Codex GPT-5.6 presets.

Claude Code offers a runtime-owned default and moving `best`, `sonnet`, `opus`, and `fable` aliases as
well as pinned model IDs. Moving selections intentionally have no static AgentRules context limit because
the runtime owns concrete-model resolution. Pinned Claude 5 choices fail closed when AgentRules cannot
prove that the exact resolved bundled or configured Claude Code executable meets the model's minimum
version. A newer global binary does not upgrade the SDK-bundled runtime automatically.

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
| OpenAI | GPT-5.5 | Saved GPT-5.6 configurations require the new presets to remain registered. |
| DeepSeek | V4 Flash | Never roll the wire model back to `deepseek-chat` or `deepseek-reasoner` after retirement. |
| Anthropic | Claude Opus 4.8 | Keep explicit Opus 5 keys registered; do not auto-fallback from a Fable refusal. |
| xAI | Grok 4.5 | Do not select Multi-Agent through the Chat Completions adapter. |
| Google | Gemini 3.5 Flash | Keep explicit 2.5 selections only until the documented shutdown. |
| Codex | Runtime default | Let the authenticated runtime catalog choose; do not synthesize a static model ID. |
| Claude Code | Runtime default | Use a pinned model only after the resolved runtime passes its minimum-version gate. |
