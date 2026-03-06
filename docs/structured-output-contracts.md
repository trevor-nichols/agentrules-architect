# Structured Output Contracts By Phase

This document defines the concrete cross-phase handoff contracts and the provider-specific structured-output request mapping used by the pipeline.

Runtime source of truth:

- `src/agentrules/core/utils/structured_outputs.py`

Pipeline handoff path:

- `src/agentrules/core/pipeline/orchestrator.py`

## Phase handoff map

1. Phase 1 (`Phase1Analysis.run`) -> Phase 2 (`Phase2Analysis.run`)
2. Phase 2 (`Phase2Analysis.run`) -> Phase 3 (`Phase3Analysis.run`)
3. Phase 3 (`Phase3Analysis.run`) -> Phase 4 (`Phase4Analysis.run`)
4. Phase 4 (`Phase4Analysis.run`) -> Phase 5 (`Phase5Analysis.run`)
5. Phase 5 (`Phase5Analysis.run`) -> Final (`FinalAnalysis.run`)

`AnalysisPipeline.run()` assembles the phase payloads and passes them forward in that order.

## Contracts by phase

The canonical schema objects are `PHASE_OUTPUT_SCHEMAS` in `src/agentrules/core/utils/structured_outputs.py`.

### Phase 1 contract

- `phase: string`
- `initial_findings: array[object]`
- `documentation_research: object`
- `package_info: object`

Producer:

- `src/agentrules/core/analysis/phase_1.py`

Consumer:

- `src/agentrules/core/analysis/phase_2.py` (input to plan creation prompt)

Structured-output mode:

- Not currently enforced at model request level (`PHASE_MODEL_RESPONSE_SCHEMAS` intentionally excludes phase 1 for now).

### Phase 2 contract (primary structured handoff)

- `plan: string`
- `agents: array[object]`
  - `id: string` (`agent_<n>`)
  - `name: string`
  - `description: string`
  - `responsibilities: array[string]` (optional in practice)
  - `file_assignments: array[string]`
- `reasoning: string | null` (optional)

Producer:

- Provider architect phase method `create_analysis_plan(...)`

Consumer:

- `src/agentrules/core/analysis/phase_2.py` parses agents from the full response object first
- `src/agentrules/core/analysis/phase_3.py` reads `analysis_plan["agents"]`

Structured-output mode:

- Enforced in `PHASE_MODEL_RESPONSE_SCHEMAS["phase2"]`

### Phase 3 contract

- `phase: string` (`"Deep Analysis"`)
- `findings: array`

Producer:

- `src/agentrules/core/analysis/phase_3.py`

Consumer:

- `src/agentrules/core/analysis/phase_4.py`

Structured-output mode:

- Not currently requested from provider in this milestone.

### Phase 4 contract

- `analysis: string`
- `error: string | null` (optional)

Producer:

- Provider architect phase method `synthesize_findings(...)`

Consumer:

- `AnalysisPipeline.run()` includes Phase 4 output inside `all_results` for Phase 5

Structured-output mode:

- Enforced in `PHASE_MODEL_RESPONSE_SCHEMAS["phase4"]`

### Phase 5 contract (Consolidation)

- `phase: string` (expected `"Consolidation"`)
- `report: string`
- `error: string | null` (optional)

Producer:

- Provider architect phase method `consolidate_results(...)`

Consumer:

- `src/agentrules/core/analysis/final_analysis.py`

Structured-output mode:

- Enforced in `PHASE_MODEL_RESPONSE_SCHEMAS["phase5"]`

### Final analysis contract

- `analysis: string`
- `error: string | null` (optional)

Producer:

- Provider architect phase method `final_analysis(...)`

Consumer:

- Output writer and AGENTS.md generation path

Structured-output mode:

- Enforced in `PHASE_MODEL_RESPONSE_SCHEMAS["final"]`

## Provider mapping

The provider map is `PROVIDER_STRUCTURED_OUTPUT_SPECS` in `src/agentrules/core/utils/structured_outputs.py`.

### OpenAI

- Request mode: `json_schema` (strong guarantee)
- Wiring:
  - Responses API: `text.format`
  - Chat API fallback path: `response_format`
  - Strict-schema normalization: logical phase schemas are transformed to OpenAI strict-compatible JSON Schema at request time (`build_openai_strict_schema`), enforcing `additionalProperties: false` and full `required` coverage for object properties.
- Internal docs reference:
  - `internal-docs/integrations/openai/structured-outputs.md`

### Anthropic

- Request mode: `json_schema` (strong guarantee)
- Wiring:
  - `output_config.format`
  - Capability-gated by model family; unsupported models fall back to plain-text phase output instead of sending `output_config.format`.
- Internal docs reference:
  - `internal-docs/integrations/anthropic/structured-outputs.md`

### Gemini

- Request mode: `json_schema` (strong guarantee)
- Wiring:
  - `response_mime_type="application/json"`
  - `response_json_schema=<schema>`
  - Schema+tools capability gate: on non-Gemini-3 models, phase schema requests automatically disable tools for that request to avoid unsupported request combinations.
  - Consolidation safeguard: phase 5 requests disable tool configuration to prevent function-call-only responses from replacing the final report body.
- Internal docs reference:
  - `internal-docs/integrations/gemini/structured-outputs.md`

### DeepSeek

- Request mode: `json_object` (moderate guarantee; prompt-guided schema match)
- Wiring:
  - `response_format={"type":"json_object"}`
  - Prompt augmentation to explicitly require JSON + schema
- Internal docs reference:
  - `internal-docs/integrations/deepseek/structured-outputs.md`

### xAI

- Request mode: `sdk_parse` in provider capability metadata, with OpenAI-compatible runtime fallback in this code path
- Wiring in current adapters:
  - `response_format={"type":"json_object"}` (fallback compatibility mode)
  - Prompt augmentation to explicitly require JSON + schema
- Internal docs reference:
  - `internal-docs/integrations/xai/structured-outputs.md`

## Implementation notes

- Structured payload extraction is centralized in:
  - `parse_structured_output_text(...)`
  - `resolve_phase_result_value(...)`
  - `extract_phase2_agents(...)`
  - `src/agentrules/core/utils/structured_outputs.py`
- Phase 2 validates model-provided `agents` before trusting them; malformed/partial agent payloads are rejected and the parser falls back to plan/XML extraction.
- Phase 2 parser normalizes non-string `plan` payloads (object/list) to safe text before markdown/XML processing to avoid type errors from provider `json_object` responses.
- Schema-valid pre-parsed agent payloads with empty `file_assignments` are accepted; empty assignment lists are not treated as structural invalidity.
