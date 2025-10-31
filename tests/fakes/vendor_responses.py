"""
Lightweight fake response objects that mimic vendor SDK shapes used in the code.

These keep tests fully offline and stable without incurring API charges.
"""

from typing import Any, List, Optional


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
    def __init__(self, content: Optional[str], tool_calls: Optional[List[_ToolCallFake]] = None, reasoning_content: Optional[str] = None) -> None:
        self.content = content
        self.tool_calls = tool_calls or []
        # DeepSeek reasoner extension
        if reasoning_content is not None:
            self.reasoning_content = reasoning_content


class _ChoiceFake:
    def __init__(self, message: _MessageFake) -> None:
        self.message = message


class OpenAIChatCompletionFake:
    def __init__(self, content: Optional[str] = "Hello", tool_calls: Optional[List[_ToolCallFake]] = None) -> None:
        self.choices = [_ChoiceFake(_MessageFake(content=content, tool_calls=tool_calls))]


class DeepSeekChatCompletionFake:
    def __init__(self, content: Optional[str] = "Hi from DeepSeek", tool_calls: Optional[List[_ToolCallFake]] = None, reasoning: Optional[str] = None) -> None:
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
        self.text = text


class _AnthropicToolUseBlock:
    def __init__(self, tool_id: str, name: str, input_data: Any) -> None:
        # Anthropic SDK exposes a `tool_use` content block, we emulate it
        self.tool_use = _AnthropicToolUse(tool_id, name, input_data)


class AnthropicMessageCreateResponseFake:
    def __init__(self, text: Optional[str] = None, tool_call: Optional[_AnthropicToolUseBlock] = None) -> None:
        blocks: List[Any] = []
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


class _PartFake:
    def __init__(self, text: Optional[str] = None, function_call: Optional[_FunctionCallFake] = None) -> None:
        self.text = text
        self.function_call = function_call


class _ContentFake:
    def __init__(self, parts: List[_PartFake]) -> None:
        self.parts = parts


class _CandidateFake:
    def __init__(self, parts: List[_PartFake]) -> None:
        self.content = _ContentFake(parts)


class GeminiGenerateContentResponseFake:
    def __init__(self, text: Optional[str] = None, function_call: Optional[_FunctionCallFake] = None) -> None:
        # Some responses provide `.text`; others require reading from parts
        self.text = text or ""
        parts = []
        if text:
            parts.append(_PartFake(text=text))
        if function_call:
            parts.append(_PartFake(function_call=function_call))
        self.candidates = [_CandidateFake(parts)]

