"""
Lightweight fake response objects that mimic vendor SDK shapes used in the code.

These keep tests fully offline and stable without incurring API charges.
"""

from types import SimpleNamespace
from typing import Any

from google.genai import types as genai_types

# -------------------------------
# OpenAI / DeepSeek (OpenAI-style)
# -------------------------------

class _ToolFunctionFake:
    def __init__(self, name: str, arguments: str) -> None:
        self.name = name
        self.arguments = arguments  # JSON string per SDK


class _ToolCallFake:
    def __init__(self, call_id: str, name: str, arguments: str) -> None:
        self.id = call_id
        self.type = "function"
        self.function = _ToolFunctionFake(name=name, arguments=arguments)


class _MessageFake:
    def __init__(self, content: str | None, tool_calls: list[_ToolCallFake] | None = None, reasoning_content: str | None = None) -> None:
        self.content = content
        self.tool_calls = tool_calls or []
        # DeepSeek reasoner extension
        if reasoning_content is not None:
            self.reasoning_content = reasoning_content


class _ChoiceFake:
    def __init__(self, message: _MessageFake) -> None:
        self.message = message


class OpenAIChatCompletionFake:
    def __init__(self, content: str | None = "Hello", tool_calls: list[_ToolCallFake] | None = None) -> None:
        self.choices = [_ChoiceFake(_MessageFake(content=content, tool_calls=tool_calls))]


class DeepSeekChatCompletionFake:
    def __init__(self, content: str | None = "Hi from DeepSeek", tool_calls: list[_ToolCallFake] | None = None, reasoning: str | None = None) -> None:
        self.choices = [_ChoiceFake(_MessageFake(content=content, tool_calls=tool_calls, reasoning_content=reasoning))]


# ---------
# Anthropic
# ---------

class _AnthropicToolUse:
    def __init__(self, tool_id: str, name: str, input_data: Any) -> None:
        self.id = tool_id
        self.name = name
        self.input = input_data


class _AnthropicTextBlock:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _AnthropicToolUseBlock:
    def __init__(self, tool_id: str, name: str, input_data: Any) -> None:
        # Anthropic SDK exposes a `tool_use` content block, we emulate it
        self.type = "tool_use"
        self.id = tool_id
        self.name = name
        self.input = input_data
        self.tool_use = _AnthropicToolUse(tool_id, name, input_data)


class AnthropicMessageCreateResponseFake:
    def __init__(self, text: str | None = None, tool_call: _AnthropicToolUseBlock | None = None) -> None:
        blocks: list[Any] = []
        if text is not None:
            blocks.append(_AnthropicTextBlock(text))
        if tool_call is not None:
            blocks.append(tool_call)
        self.content = blocks


# ------
# Gemini
# ------

class _FunctionCallFake:
    def __init__(self, name: str, args: Any) -> None:
        self.name = name
        self.args = args


class GeminiGenerateContentResponseFake:
    def __init__(self, text: str | None = None, function_call: _FunctionCallFake | None = None) -> None:
        self.text = text or ""
        parts: list[genai_types.Part] = []
        if text:
            parts.append(genai_types.Part(text=text))
        if function_call:
            parts.append(
                genai_types.Part(
                    function_call=genai_types.FunctionCall(
                        name=function_call.name,
                        args=function_call.args,
                    )
                )
            )
        self.candidates = [SimpleNamespace(content=genai_types.Content(role="model", parts=parts))]
