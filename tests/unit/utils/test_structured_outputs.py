from __future__ import annotations

from agentrules.core.agents.base import ModelProvider
from agentrules.core.utils.structured_outputs import (
    PROVIDER_STRUCTURED_OUTPUT_SPECS,
    augment_prompt_for_json_mode,
    build_anthropic_output_format,
    build_chat_json_object_response_format,
    build_codex_output_schema,
    build_openai_chat_response_format,
    build_openai_strict_schema,
    build_openai_text_format,
    extract_phase2_agents,
    get_phase_model_response_schema,
    get_phase_output_schema,
    parse_structured_output_text,
    resolve_phase_result_value,
    resolve_structured_output_mode,
    should_use_legacy_phase2_prompt,
)


def test_phase_output_schemas_expose_expected_phase2_fields() -> None:
    schema = get_phase_output_schema("phase2")
    assert schema["type"] == "object"
    assert "plan" in schema["properties"]
    assert "agents" in schema["properties"]


def test_phase1_schema_includes_project_profile_contract() -> None:
    schema = get_phase_output_schema("phase1")
    assert schema["type"] == "object"
    assert "project_profile" in schema["properties"]
    assert "project_profile" in schema["required"]


def test_phase_model_response_schema_none_for_unsupported_phase() -> None:
    assert get_phase_model_response_schema("phase1") is None
    assert get_phase_model_response_schema("missing") is None


def test_resolve_structured_output_mode_for_phase_and_provider() -> None:
    assert (
        resolve_structured_output_mode(
            provider=ModelProvider.OPENAI,
            model_name="gpt-5-mini",
            phase="phase2",
        )
        == "json_schema"
    )
    assert (
        resolve_structured_output_mode(
            provider=ModelProvider.CODEX,
            model_name="gpt-5.3-codex",
            phase="phase2",
        )
        == "json_schema"
    )
    assert (
        resolve_structured_output_mode(
            provider=ModelProvider.DEEPSEEK,
            model_name="deepseek-chat",
            phase="phase4",
        )
        == "json_object"
    )
    assert (
        resolve_structured_output_mode(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-opus-4-1",
            phase="phase2",
        )
        == "disabled"
    )
    assert (
        resolve_structured_output_mode(
            provider=ModelProvider.OPENAI,
            model_name="gpt-5-mini",
            phase="phase1",
        )
        == "disabled"
    )


def test_should_use_legacy_phase2_prompt_for_unsupported_model() -> None:
    assert should_use_legacy_phase2_prompt(
        provider=ModelProvider.ANTHROPIC,
        model_name="claude-opus-4-1",
    )
    assert not should_use_legacy_phase2_prompt(
        provider=ModelProvider.OPENAI,
        model_name="gpt-5-mini",
    )


def test_provider_mapping_uses_expected_docs_and_modes() -> None:
    assert PROVIDER_STRUCTURED_OUTPUT_SPECS[ModelProvider.OPENAI].doc_path.endswith(
        "integrations/openai/structured-outputs.md"
    )
    assert PROVIDER_STRUCTURED_OUTPUT_SPECS[ModelProvider.CODEX].doc_path.endswith(
        "integrations/codex/app-server/reference/turns.md"
    )
    assert PROVIDER_STRUCTURED_OUTPUT_SPECS[ModelProvider.ANTHROPIC].request_mode == "json_schema"
    assert PROVIDER_STRUCTURED_OUTPUT_SPECS[ModelProvider.DEEPSEEK].request_mode == "json_object"
    assert PROVIDER_STRUCTURED_OUTPUT_SPECS[ModelProvider.XAI].request_mode == "sdk_parse"


def test_openai_format_builders_return_phase_schema_for_phase2() -> None:
    text_format = build_openai_text_format("phase2")
    chat_format = build_openai_chat_response_format("phase2")
    assert text_format is not None
    assert chat_format is not None
    assert text_format["format"]["type"] == "json_schema"
    assert chat_format["type"] == "json_schema"
    strict_schema = text_format["format"]["schema"]
    assert strict_schema["additionalProperties"] is False
    assert "reasoning" in strict_schema["required"]
    agent_schema = strict_schema["properties"]["agents"]["items"]
    assert agent_schema["additionalProperties"] is False
    assert "responsibilities" in agent_schema["required"]


def test_anthropic_output_format_closes_object_schemas() -> None:
    output_format = build_anthropic_output_format("phase4")
    assert output_format is not None
    schema = output_format["schema"]
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["analysis"]
    assert schema["properties"]["error"]["type"] == ["string", "null"]


def test_anthropic_output_format_does_not_mutate_base_phase_schema() -> None:
    phase_schema = get_phase_model_response_schema("phase4")
    assert phase_schema is not None
    assert phase_schema["additionalProperties"] is True
    build_anthropic_output_format("phase4")
    assert phase_schema["additionalProperties"] is True


def test_codex_output_schema_is_strict_for_phase2() -> None:
    schema = build_codex_output_schema("phase2")
    assert schema is not None
    assert schema["additionalProperties"] is False
    assert "reasoning" in schema["required"]

    agent_schema = schema["properties"]["agents"]["items"]
    assert agent_schema["additionalProperties"] is False
    assert "responsibilities" in agent_schema["required"]


def test_codex_output_schema_makes_optional_phase4_error_required_with_null() -> None:
    schema = build_codex_output_schema("phase4")
    assert schema is not None
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["analysis", "error"]
    assert schema["properties"]["error"]["type"] == ["string", "null"]


def test_build_openai_strict_schema_requires_all_object_keys() -> None:
    source = {
        "type": "object",
        "properties": {
            "analysis": {"type": "string"},
            "error": {"type": ["string", "null"]},
        },
        "required": ["analysis"],
        "additionalProperties": True,
    }
    strict = build_openai_strict_schema(source)

    assert strict["additionalProperties"] is False
    assert strict["required"] == ["analysis", "error"]
    assert strict["properties"]["error"]["type"] == ["string", "null"]


def test_chat_json_object_response_format_only_for_supported_providers() -> None:
    assert build_chat_json_object_response_format(ModelProvider.DEEPSEEK, "phase2") == {
        "type": "json_object"
    }
    assert build_chat_json_object_response_format(ModelProvider.XAI, "phase4") == {
        "type": "json_object"
    }
    assert build_chat_json_object_response_format(ModelProvider.OPENAI, "phase2") is None


def test_parse_structured_output_text_handles_fenced_json() -> None:
    parsed = parse_structured_output_text("```json\n{\"plan\":\"x\",\"agents\":[]}\n```")
    assert parsed == {"plan": "x", "agents": []}


def test_parse_structured_output_text_accepts_dict_payload() -> None:
    payload = {"plan": "x", "agents": []}
    parsed = parse_structured_output_text(payload)
    assert parsed == payload


def test_parse_structured_output_text_handles_non_string_payload_without_crash() -> None:
    parsed = parse_structured_output_text([{"type": "output_text", "text": "hello"}])
    assert parsed is None


def test_resolve_phase_result_value_prefers_structured_key() -> None:
    value, payload = resolve_phase_result_value(
        phase="phase5",
        result_key="report",
        findings='{"report":"structured","phase":"Consolidation"}',
        empty_value="No report generated",
    )
    assert value == "structured"
    assert payload == {"report": "structured", "phase": "Consolidation"}


def test_resolve_phase_result_value_handles_dict_findings() -> None:
    value, payload = resolve_phase_result_value(
        phase="phase2",
        result_key="plan",
        findings={"plan": "structured plan", "agents": []},
        empty_value="No plan generated",
    )
    assert value == "structured plan"
    assert payload == {"plan": "structured plan", "agents": []}


def test_resolve_phase_result_value_serializes_non_string_fallback() -> None:
    value, payload = resolve_phase_result_value(
        phase="phase4",
        result_key="analysis",
        findings=[{"note": "a"}],
        empty_value="No analysis generated",
    )
    assert value == '[{"note": "a"}]'
    assert payload is None


def test_extract_phase2_agents_filters_non_dict_entries() -> None:
    agents = extract_phase2_agents({"agents": [{"id": "agent_1"}, "skip"]})
    assert agents == [{"id": "agent_1"}]


def test_extract_phase2_agents_preserves_explicit_empty_list() -> None:
    agents = extract_phase2_agents({"agents": []})
    assert agents == []


def test_augment_prompt_for_json_mode_adds_json_instruction() -> None:
    prompt = augment_prompt_for_json_mode("Analyze project", "phase2")
    assert "Return valid JSON only" in prompt
    assert "JSON Schema" in prompt
