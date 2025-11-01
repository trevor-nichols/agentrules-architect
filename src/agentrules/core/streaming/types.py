"""Common streaming event types shared across provider implementations."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from enum import Enum
from typing import Any


class StreamEventType(str, Enum):
    """Normalized event types emitted by provider streaming implementations."""

    TEXT_DELTA = "text_delta"
    REASONING_DELTA = "reasoning_delta"
    TOOL_CALL_DELTA = "tool_call_delta"
    MESSAGE_START = "message_start"
    MESSAGE_DELTA = "message_delta"
    MESSAGE_END = "message_end"
    USAGE = "usage"
    ERROR = "error"
    SYSTEM = "system"


JsonMapping = Mapping[str, Any] | MutableMapping[str, Any]


@dataclass
class StreamChunk:
    """Normalized representation of a streaming payload chunk."""

    event_type: StreamEventType
    text: str | None = None
    reasoning: str | None = None
    tool_call: JsonMapping | None = None
    finish_reason: str | None = None
    usage: JsonMapping | None = None
    raw: Any | None = None
