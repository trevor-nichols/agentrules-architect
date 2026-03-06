# Provider System Prompt Mapping

Last updated: 2026-03-04

This document records how each model provider expects high-priority
system/developer instructions and where this repository maps that behavior.

## Provider API fields

| Provider | API field for system instructions | Notes |
| --- | --- | --- |
| OpenAI | Responses API: `instructions` | Used for Responses API requests. |
| OpenAI | Chat Completions API: `messages` with `role: "developer"` | Prepended before the user message. |
| Anthropic | Top-level `system` | Anthropic Messages API expects `system` outside `messages`. |
| Gemini | `config.system_instruction` | Sent in `GenerateContentConfig`. |
| DeepSeek | First message: `{"role": "system", ...}` | OpenAI-compatible Chat Completions shape. |
| xAI | First message: `{"role": "system", ...}` | OpenAI-compatible Chat Completions shape (`developer` alias supported by docs). |

## Shared implementation in this repo

Default prompt construction and context override resolution are centralized in:

- `src/agentrules/core/utils/system_prompt.py`

Key behavior:

1. Build a default agent system prompt from architect identity:
   - `name`
   - `role`
   - `responsibilities`
2. Allow per-request overrides using context keys:
   - `system_prompt`
   - `developer_instructions`
   - `instructions`
3. Map the resolved prompt into the provider-native field listed above.

## Phase Prompt Separation

Behavioral instructions are now separated from user payload templates and
stored with their respective phase prompt modules:

- `src/agentrules/config/prompts/phase_1_prompts.py`
- `src/agentrules/config/prompts/phase_2_prompts.py`
- `src/agentrules/config/prompts/phase_3_prompts.py`
- `src/agentrules/config/prompts/phase_4_prompts.py`
- `src/agentrules/config/prompts/phase_5_prompts.py`
- `src/agentrules/config/prompts/final_analysis_prompt.py`

The pipeline now builds each phase/agent with a phase-appropriate system prompt
and keeps user prompts focused on repository data and task payload.

## System Prompt Requirement

System prompts are always required in this pipeline.

Architect construction enforces a resolved system prompt for every agent,
using either:

- explicit phase/system templates, or
- fallback generation from agent name/role/responsibilities.

## Code locations

- OpenAI:
  - `src/agentrules/core/agents/openai/architect.py`
  - `src/agentrules/core/agents/openai/request_builder.py`
- Anthropic:
  - `src/agentrules/core/agents/anthropic/architect.py`
  - `src/agentrules/core/agents/anthropic/request_builder.py`
- Gemini:
  - `src/agentrules/core/agents/gemini/architect.py`
- DeepSeek:
  - `src/agentrules/core/agents/deepseek/architect.py`
  - `src/agentrules/core/agents/deepseek/request_builder.py`
- xAI:
  - `src/agentrules/core/agents/xai/architect.py`
  - `src/agentrules/core/agents/xai/request_builder.py`
