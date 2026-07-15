# Provider Model Lifecycle

This guide records model-selection and lifecycle constraints that affect AgentRules operators. It complements the preset labels shown by `agentrules configure --models` and focuses on behavior that cannot be inferred safely from a model ID alone.

## Direct Anthropic API

### Claude Sonnet 5

`claude-sonnet-5` has a 1,000,000-token context and uses adaptive thinking by default. AgentRules offers an explicit non-thinking preset that sends `thinking: {"type": "disabled"}` plus adaptive presets at low, medium, high, xhigh, and max effort. Manual thinking budgets are not supported. Sonnet 5 remains compatible with zero-data-retention arrangements.

### Claude Fable 5

`claude-fable-5` always uses adaptive thinking, so AgentRules does not offer a disabled-thinking preset and rejects a programmatic `ReasoningMode.DISABLED` configuration before network dispatch. Effort presets range from low through max.

Fable 5 is a Covered Model: it requires 30-day data retention and is unavailable to a workspace that remains under zero data retention. Operators must enable the documented 30-day workspace retention policy before selecting it. AgentRules does not change retention settings or automatically fall back to another model.

Fable 5 and Sonnet 5 can return HTTP 200 with `stop_reason="refusal"`. AgentRules treats that as an error result, includes only the provider's bounded category/explanation summary when present, and never treats empty refusal content as successful analysis. Streaming refusals terminate the stream with the same typed error. Automatic fallback is intentionally not configured because it would change model behavior and cost.

### Opus compatibility keys

The generic `claude-opus` and `claude-opus-reasoning` preset keys now resolve to Claude Opus 4.8. Claude Opus 4.1 retires from the Claude API on August 5, 2026, and Anthropic recommends Opus 4.8 as its replacement.

Official references:

- [Claude Sonnet 5 changes](https://platform.claude.com/docs/en/about-claude/models/whats-new-sonnet-5)
- [Claude Fable 5 introduction](https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5)
- [Adaptive thinking](https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking)
- [Refusals and fallback](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback)
- [API and data retention](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)
- [Model deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations)

## Direct xAI API

### Grok 4.5

`grok-4.5` is the recommended direct xAI model and the default for a directly constructed
`XaiArchitect`. It has a 500,000-token context and accepts only low, medium, or high reasoning effort;
high is the provider default. Reasoning cannot be disabled. AgentRules rejects disabled, minimal,
xhigh, and max configurations before network dispatch rather than translating them to an unsupported
wire value.

### Grok 4.20 pinned variants

AgentRules exposes `grok-4.20-0309-reasoning` and `grok-4.20-0309-non-reasoning` as specialized,
pinned Chat Completions choices with 1,000,000-token contexts. Their reasoning behavior is selected by
the model ID, so AgentRules does not add a `reasoning_effort` field that xAI has not documented for
those variants.

Grok 4.20 Multi-Agent is not exposed. xAI explicitly states that it does not work with Chat
Completions and requires the xAI SDK or Responses API. AgentRules' current xAI adapter intentionally
remains Chat-Completions-only, so adding a Multi-Agent preset would guarantee a runtime failure.

Official references:

- [Grok 4.5](https://docs.x.ai/developers/grok-4-5)
- [xAI reasoning controls](https://docs.x.ai/developers/model-capabilities/text/reasoning)
- [Grok 4.20 reasoning model](https://docs.x.ai/developers/models/grok-4.20-0309-reasoning)
- [Grok 4.20 non-reasoning model](https://docs.x.ai/developers/models/grok-4.20-0309-non-reasoning)
- [Multi-Agent endpoint limitations](https://docs.x.ai/developers/model-capabilities/text/multi-agent)

## Google Gemini API

`gemini-3.5-flash` is already AgentRules' stable current Flash choice and retains medium thinking.
Gemini 2.5 Flash and Gemini 2.5 Pro remain selectable until their documented October 16, 2026
shutdown because silently changing an explicit active selection could alter behavior or cost. Their picker
labels disclose the date and recommend Gemini 3.5 Flash or Gemini 3.1 Pro Preview respectively.

The saved keys `gemini-3-pro-preview` and `gemini-3.1-flash-lite-preview` remain loadable for backwards
compatibility, but runtime resolution sends `gemini-3.1-pro-preview` and `gemini-3.1-flash-lite`. The
picker labels disclose those redirects so operators do not mistake compatibility keys for live endpoints.

Official reference:

- [Gemini model deprecations](https://ai.google.dev/gemini-api/docs/deprecations)
