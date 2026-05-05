from __future__ import annotations

from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock, ToolUseBlock

from agentrules.core.agents.claude_code.response_parser import parse_response


def _result_message(
    *,
    result: str | None = None,
    structured_output: object | None = None,
    is_error: bool = False,
    subtype: str = "success",
    errors: list[str] | None = None,
) -> ResultMessage:
    return ResultMessage(
        subtype=subtype,
        duration_ms=10,
        duration_api_ms=8,
        is_error=is_error,
        num_turns=1,
        session_id="session-1",
        stop_reason=None,
        total_cost_usd=None,
        usage={"input_tokens": 3, "output_tokens": 5},
        result=result,
        structured_output=structured_output,
        model_usage=None,
        permission_denials=None,
        errors=errors,
        uuid=None,
    )


def test_parse_response_collects_text_tool_calls_and_usage() -> None:
    messages = (
        AssistantMessage(
            content=[
                TextBlock(text="First finding. "),
                ToolUseBlock(id="tool-1", name="Read", input={"file_path": "src/app.py"}),
                TextBlock(text="Second finding."),
            ],
            model="claude-sonnet-4-6",
            parent_tool_use_id=None,
            error=None,
            usage={"input_tokens": 1},
            message_id=None,
            stop_reason=None,
            session_id=None,
            uuid=None,
        ),
        _result_message(),
    )

    parsed = parse_response(messages)

    assert parsed.findings == "First finding. Second finding."
    assert parsed.tool_calls == [
        {
            "id": "tool-1",
            "name": "Read",
            "input": {"file_path": "src/app.py"},
        }
    ]
    assert parsed.usage == {"input_tokens": 3, "output_tokens": 5}
    assert parsed.error_message is None


def test_parse_response_coerces_sdk_object_tool_input() -> None:
    class _ToolInput:
        def to_dict(self) -> dict[str, str]:
            return {"file_path": "src/app.py"}

    class ToolUseBlock:
        def __init__(self) -> None:
            self.id = "tool-1"
            self.name = "Read"
            self.input = _ToolInput()

    class AssistantMessage:
        def __init__(self) -> None:
            self.error = None
            self.usage = None
            self.content = [ToolUseBlock()]

    parsed = parse_response((AssistantMessage(),))

    assert parsed.tool_calls == [
        {
            "id": "tool-1",
            "name": "Read",
            "input": {"file_path": "src/app.py"},
        }
    ]


def test_parse_response_prefers_result_text_and_structured_output() -> None:
    structured = {"analysis": "Structured synthesis."}
    parsed = parse_response(
        (
            AssistantMessage(
                content=[TextBlock(text="Draft text.")],
                model="claude-sonnet-4-6",
                parent_tool_use_id=None,
                error=None,
                usage=None,
                message_id=None,
                stop_reason=None,
                session_id=None,
                uuid=None,
            ),
            _result_message(result="Final text.", structured_output=structured),
        )
    )

    assert parsed.findings == "Final text."
    assert parsed.structured_output == structured


def test_parse_response_formats_result_errors() -> None:
    parsed = parse_response((_result_message(is_error=True, subtype="error_during_execution", errors=["boom"]),))

    assert parsed.error_message == "boom"
