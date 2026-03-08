"""Shared schema contracts and provider mappings for structured model outputs."""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from typing import Any, Literal, cast

from agentrules.core.agents.base import ModelProvider

PhaseName = Literal["phase1", "phase2", "phase3", "phase4", "phase5", "final"]
StructuredOutputMode = Literal["json_schema", "json_object", "disabled"]

_SUPPORTED_PHASES: tuple[PhaseName, ...] = (
    "phase1",
    "phase2",
    "phase3",
    "phase4",
    "phase5",
    "final",
)


@dataclass(frozen=True)
class ProviderStructuredOutputSpec:
    """Describes provider-specific structured output behavior."""

    provider: ModelProvider
    doc_path: str
    request_mode: Literal["json_schema", "json_object", "sdk_parse"]
    schema_guarantee: Literal["strong", "moderate", "prompt_guided"]
    notes: str


PHASE_OUTPUT_SCHEMAS: dict[PhaseName, dict[str, Any]] = {
    "phase1": {
        "type": "object",
        "properties": {
            "phase": {"type": "string"},
            "initial_findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "agent": {"type": "string"},
                        "findings": {"type": ["string", "null"]},
                        "error": {"type": ["string", "null"]},
                    },
                    "required": ["agent"],
                    "additionalProperties": True,
                },
            },
            "documentation_research": {"type": "object"},
            "package_info": {"type": "object"},
        },
        "required": ["phase", "initial_findings", "documentation_research", "package_info"],
        "additionalProperties": True,
    },
    "phase2": {
        "type": "object",
        "properties": {
            "plan": {"type": "string"},
            "agents": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "pattern": "^agent_[0-9]+$"},
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "responsibilities": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "file_assignments": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["id", "name", "description", "file_assignments"],
                    "additionalProperties": False,
                },
            },
            "reasoning": {"type": ["string", "null"]},
        },
        "required": ["plan", "agents"],
        "additionalProperties": False,
    },
    "phase3": {
        "type": "object",
        "properties": {
            "phase": {"type": "string"},
            "findings": {"type": "array"},
        },
        "required": ["phase", "findings"],
        "additionalProperties": True,
    },
    "phase4": {
        "type": "object",
        "properties": {
            "analysis": {"type": "string"},
            "error": {"type": ["string", "null"]},
        },
        "required": ["analysis"],
        "additionalProperties": True,
    },
    "phase5": {
        "type": "object",
        "properties": {
            "phase": {"type": "string", "const": "Consolidation"},
            "report": {"type": "string"},
            "error": {"type": ["string", "null"]},
        },
        "required": ["phase", "report"],
        "additionalProperties": True,
    },
    "final": {
        "type": "object",
        "properties": {
            "analysis": {"type": "string"},
            "error": {"type": ["string", "null"]},
        },
        "required": ["analysis"],
        "additionalProperties": True,
    },
}


PHASE_MODEL_RESPONSE_SCHEMAS: dict[PhaseName, dict[str, Any]] = {
    "phase2": PHASE_OUTPUT_SCHEMAS["phase2"],
    "phase4": PHASE_OUTPUT_SCHEMAS["phase4"],
    "phase5": PHASE_OUTPUT_SCHEMAS["phase5"],
    "final": PHASE_OUTPUT_SCHEMAS["final"],
}


PROVIDER_STRUCTURED_OUTPUT_SPECS: dict[ModelProvider, ProviderStructuredOutputSpec] = {
    ModelProvider.OPENAI: ProviderStructuredOutputSpec(
        provider=ModelProvider.OPENAI,
        doc_path="internal-docs/integrations/openai/structured-outputs.md",
        request_mode="json_schema",
        schema_guarantee="strong",
        notes="Responses API uses text.format with strict json_schema.",
    ),
    ModelProvider.CODEX: ProviderStructuredOutputSpec(
        provider=ModelProvider.CODEX,
        doc_path="internal-docs/integrations/codex/app-server/reference/turns.md",
        request_mode="json_schema",
        schema_guarantee="strong",
        notes="Codex app-server accepts a per-turn outputSchema on turn/start.",
    ),
    ModelProvider.ANTHROPIC: ProviderStructuredOutputSpec(
        provider=ModelProvider.ANTHROPIC,
        doc_path="internal-docs/integrations/anthropic/structured-outputs.md",
        request_mode="json_schema",
        schema_guarantee="strong",
        notes="Messages API uses output_config.format json_schema.",
    ),
    ModelProvider.GEMINI: ProviderStructuredOutputSpec(
        provider=ModelProvider.GEMINI,
        doc_path="internal-docs/integrations/gemini/structured-outputs.md",
        request_mode="json_schema",
        schema_guarantee="strong",
        notes="GenerateContentConfig uses response_mime_type and response_json_schema.",
    ),
    ModelProvider.DEEPSEEK: ProviderStructuredOutputSpec(
        provider=ModelProvider.DEEPSEEK,
        doc_path="internal-docs/integrations/deepseek/structured-outputs.md",
        request_mode="json_object",
        schema_guarantee="moderate",
        notes="JSON object mode requires explicit JSON instruction in prompt.",
    ),
    ModelProvider.XAI: ProviderStructuredOutputSpec(
        provider=ModelProvider.XAI,
        doc_path="internal-docs/integrations/xai/structured-outputs.md",
        request_mode="sdk_parse",
        schema_guarantee="prompt_guided",
        notes="SDK parse path is documented; OpenAI-compatible adapter uses json_object fallback.",
    ),
}


def is_supported_phase_name(phase: str | None) -> bool:
    return phase in _SUPPORTED_PHASES


def get_phase_output_schema(phase: PhaseName) -> dict[str, Any]:
    """Return the concrete output schema for a pipeline phase."""
    return PHASE_OUTPUT_SCHEMAS[phase]


def get_phase_model_response_schema(phase: str | None) -> dict[str, Any] | None:
    """Return the model-facing response schema used for structured decoding."""
    if not isinstance(phase, str):
        return None
    if not is_supported_phase_name(phase):
        return None
    phase_name = cast(PhaseName, phase)
    return PHASE_MODEL_RESPONSE_SCHEMAS.get(phase_name)


def get_provider_structured_output_spec(provider: ModelProvider) -> ProviderStructuredOutputSpec:
    return PROVIDER_STRUCTURED_OUTPUT_SPECS[provider]


def resolve_structured_output_mode(
    *,
    provider: ModelProvider,
    model_name: str,
    phase: str | None,
) -> StructuredOutputMode:
    """
    Resolve the structured-output mode for a provider/model/phase combination.

    This is the central capability decision used by phase orchestration and
    provider adapters. If a phase has no structured schema contract, structured
    outputs are disabled regardless of provider.
    """
    if get_phase_model_response_schema(phase) is None:
        return "disabled"

    if provider == ModelProvider.ANTHROPIC:
        # Anthropic advertises model-family gating for output_config.format.
        from agentrules.core.agents.anthropic.capabilities import supports_structured_output_format

        if not supports_structured_output_format(model_name):
            return "disabled"
        return "json_schema"

    if provider in {ModelProvider.OPENAI, ModelProvider.CODEX, ModelProvider.GEMINI}:
        return "json_schema"

    if provider in {ModelProvider.DEEPSEEK, ModelProvider.XAI}:
        return "json_object"

    return "disabled"


def should_use_legacy_phase2_prompt(*, provider: ModelProvider, model_name: str) -> bool:
    """
    Return True when Phase 2 should use the legacy XML prompt fallback.
    """
    return (
        resolve_structured_output_mode(
            provider=provider,
            model_name=model_name,
            phase="phase2",
        )
        == "disabled"
    )


def build_openai_text_format(phase: str | None) -> dict[str, Any] | None:
    """Build OpenAI Responses API text.format json_schema payload."""
    schema = get_phase_model_response_schema(phase)
    if schema is None:
        return None
    openai_schema = build_openai_strict_schema(schema)
    phase_name = cast(PhaseName, phase)
    return {
        "format": {
            "type": "json_schema",
            "name": f"{phase_name}_response",
            "schema": openai_schema,
            "strict": True,
        }
    }


def build_openai_chat_response_format(phase: str | None) -> dict[str, Any] | None:
    """Build OpenAI Chat Completions response_format for JSON schema."""
    schema = get_phase_model_response_schema(phase)
    if schema is None:
        return None
    openai_schema = build_openai_strict_schema(schema)
    phase_name = cast(PhaseName, phase)
    return {
        "type": "json_schema",
        "json_schema": {
            "name": f"{phase_name}_response",
            "schema": openai_schema,
            "strict": True,
        },
    }


def build_anthropic_output_format(phase: str | None) -> dict[str, Any] | None:
    """Build Anthropic output_config.format json_schema payload."""
    schema = get_phase_model_response_schema(phase)
    if schema is None:
        return None
    anthropic_schema = build_anthropic_compatible_schema(schema)
    return {
        "type": "json_schema",
        "schema": anthropic_schema,
    }


def build_codex_output_schema(phase: str | None) -> dict[str, Any] | None:
    """Build Codex app-server `outputSchema` payload."""
    schema = get_phase_model_response_schema(phase)
    if schema is None:
        return None
    return copy.deepcopy(schema)


def build_gemini_response_schema(phase: str | None) -> dict[str, Any] | None:
    """Build Gemini response_json_schema."""
    schema = get_phase_model_response_schema(phase)
    if schema is None:
        return None
    return schema


def build_chat_json_object_response_format(provider: ModelProvider, phase: str | None) -> dict[str, Any] | None:
    """
    Build fallback json_object config for OpenAI-compatible chat providers.

    DeepSeek and xAI support JSON object mode in this codebase without schema
    validation guarantees, so schema-level validation remains in application code.
    """
    if provider not in {ModelProvider.DEEPSEEK, ModelProvider.XAI}:
        return None
    if get_phase_model_response_schema(phase) is None:
        return None
    return {"type": "json_object"}


def augment_prompt_for_json_mode(prompt: str, phase: str | None) -> str:
    """
    Append deterministic JSON instruction text for providers that need guidance.
    """
    schema = get_phase_model_response_schema(phase)
    if schema is None:
        return prompt
    schema_json = json.dumps(schema, separators=(",", ":"), ensure_ascii=False)
    return (
        f"{prompt}\n\n"
        "Return valid JSON only (no markdown fences). "
        f"The response must match this JSON Schema: {schema_json}"
    )


_JSON_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)


def _coerce_payload_to_text(payload: Any) -> str | None:
    """Best-effort conversion of provider payload variants into text."""
    if payload is None:
        return None
    if isinstance(payload, str):
        return payload
    if isinstance(payload, bytes):
        return payload.decode("utf-8", errors="replace")
    if isinstance(payload, (dict, list)):
        try:
            return json.dumps(payload, ensure_ascii=False)
        except (TypeError, ValueError):
            return None
    return str(payload)


def parse_structured_output_text(text: Any) -> dict[str, Any] | None:
    """Parse a structured JSON response payload if one is present."""
    if isinstance(text, dict):
        return text

    candidate = _coerce_payload_to_text(text)
    if not candidate:
        return None

    candidate = candidate.strip()
    if not candidate:
        return None

    fenced = _JSON_FENCE_RE.match(candidate)
    if fenced:
        candidate = fenced.group(1).strip()

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None

    if isinstance(parsed, dict):
        return parsed
    return None


def build_openai_strict_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """
    Transform a JSON schema into OpenAI strict-compatible shape.

    OpenAI strict mode requires object schemas to set `additionalProperties: false`
    and include every property in `required`. For fields that were optional in the
    logical schema, this transformer adds `null` to the field type so callers can
    preserve optional semantics while still satisfying strict requirements.
    """
    normalized = copy.deepcopy(schema)
    _normalize_openai_strict_schema_in_place(normalized)
    return normalized


def build_anthropic_compatible_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """
    Transform JSON schema into Anthropic-compatible shape.

    Anthropic structured outputs require object schemas to set
    `additionalProperties: false`.
    """
    normalized = copy.deepcopy(schema)
    _close_object_schemas_in_place(normalized)
    return normalized


def _normalize_openai_strict_schema_in_place(schema: dict[str, Any]) -> None:
    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        schema_types = set(str(item) for item in schema_type)
    elif isinstance(schema_type, str):
        schema_types = {schema_type}
    else:
        schema_types = set()

    if "object" in schema_types:
        properties = schema.get("properties")
        if isinstance(properties, dict):
            original_required = schema.get("required")
            required_keys: set[str] = set(original_required) if isinstance(original_required, list) else set()

            for key, prop_schema in list(properties.items()):
                if isinstance(prop_schema, dict):
                    _normalize_openai_strict_schema_in_place(prop_schema)
                    if key not in required_keys:
                        _allow_null_in_place(prop_schema)

            schema["required"] = list(properties.keys())

        schema["additionalProperties"] = False

    items = schema.get("items")
    if isinstance(items, dict):
        _normalize_openai_strict_schema_in_place(items)
    elif isinstance(items, list):
        for item_schema in items:
            if isinstance(item_schema, dict):
                _normalize_openai_strict_schema_in_place(item_schema)

    for keyword in ("anyOf", "oneOf", "allOf"):
        variants = schema.get(keyword)
        if isinstance(variants, list):
            for variant in variants:
                if isinstance(variant, dict):
                    _normalize_openai_strict_schema_in_place(variant)


def _allow_null_in_place(schema: dict[str, Any]) -> None:
    if "const" in schema:
        return

    schema_type = schema.get("type")
    if isinstance(schema_type, str):
        if schema_type != "null":
            schema["type"] = [schema_type, "null"]
        return

    if isinstance(schema_type, list):
        if "null" not in schema_type:
            schema["type"] = [*schema_type, "null"]


def _close_object_schemas_in_place(schema: dict[str, Any]) -> None:
    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        schema_types = {str(item) for item in schema_type}
    elif isinstance(schema_type, str):
        schema_types = {schema_type}
    else:
        schema_types = set()

    if "object" in schema_types:
        schema["additionalProperties"] = False
        properties = schema.get("properties")
        if isinstance(properties, dict):
            for prop_schema in properties.values():
                if isinstance(prop_schema, dict):
                    _close_object_schemas_in_place(prop_schema)

    items = schema.get("items")
    if isinstance(items, dict):
        _close_object_schemas_in_place(items)
    elif isinstance(items, list):
        for item_schema in items:
            if isinstance(item_schema, dict):
                _close_object_schemas_in_place(item_schema)

    for keyword in ("anyOf", "oneOf", "allOf"):
        variants = schema.get(keyword)
        if isinstance(variants, list):
            for variant in variants:
                if isinstance(variant, dict):
                    _close_object_schemas_in_place(variant)


def resolve_phase_result_value(
    *,
    phase: str | None,
    result_key: str,
    findings: Any,
    empty_value: str,
) -> tuple[str, dict[str, Any] | None]:
    """
    Resolve the canonical phase result value from structured or plain findings.
    """
    parsed = parse_structured_output_text(findings)
    findings_text = _coerce_payload_to_text(findings)
    if parsed is None:
        return findings_text or empty_value, None

    preferred_keys: list[str] = [result_key]
    if result_key == "plan":
        preferred_keys.extend(["plan_markdown", "analysis_plan"])
    elif result_key == "analysis":
        preferred_keys.extend(["summary", "report"])
    elif result_key == "report":
        preferred_keys.extend(["analysis", "summary"])

    for key in preferred_keys:
        value = parsed.get(key)
        if isinstance(value, str):
            return value, parsed

    if findings_text:
        return findings_text, parsed
    return empty_value, parsed


def extract_phase2_agents(structured_payload: dict[str, Any] | None) -> list[dict[str, Any]] | None:
    """Return Phase 2 agent assignments when present and valid.

    An explicit empty list is meaningful for Phase 2 and must be preserved so
    downstream parsing can distinguish "zero agents" from "agents missing".
    """
    if not isinstance(structured_payload, dict):
        return None

    raw_agents = structured_payload.get("agents")
    if not isinstance(raw_agents, list):
        return None
    if not raw_agents:
        return []

    agents = [agent for agent in raw_agents if isinstance(agent, dict)]
    if not agents:
        return None
    return agents
