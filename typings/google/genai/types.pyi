from typing import Any, ClassVar

class ThinkingLevel:
    MINIMAL: ClassVar[str]
    LOW: ClassVar[str]
    MEDIUM: ClassVar[str]
    HIGH: ClassVar[str]

class ThinkingConfig:
    thinking_budget: int | None
    thinking_level: str | None
    def __init__(
        self, *, thinking_budget: int | None = ..., thinking_level: str | None = ...
    ) -> None: ...

class HttpOptions:
    timeout: int | None
    def __init__(self, *, timeout: int | None = ...) -> None: ...

class FunctionCall:
    id: str | None
    name: str | None
    args: dict[str, Any] | None
    def __init__(self, **kwargs: Any) -> None: ...

class FunctionResponse:
    id: str | None
    name: str | None
    response: dict[str, Any] | None
    def __init__(self, **kwargs: Any) -> None: ...

class Part:
    text: str | None
    thought_signature: bytes | None
    function_call: FunctionCall | None
    function_response: FunctionResponse | None
    def __init__(self, **kwargs: Any) -> None: ...

class Content:
    role: str | None
    parts: list[Part] | None
    def __init__(self, **kwargs: Any) -> None: ...
    @classmethod
    def model_validate(cls, value: dict[str, Any]) -> Content: ...
    def model_dump(self, *, mode: str = ..., exclude_none: bool = ...) -> dict[str, Any]: ...

class GenerateContentConfig:
    def __init__(self, **kwargs: Any) -> None: ...

__all__ = [
    "ThinkingLevel", "ThinkingConfig", "GenerateContentConfig", "HttpOptions", "FunctionCall",
    "FunctionResponse", "Part", "Content",
]
