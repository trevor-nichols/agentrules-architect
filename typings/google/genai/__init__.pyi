from typing import Any

from . import types as types

class Client:
    models: Any
    def __init__(
        self, *, api_key: str | None = ..., http_options: types.HttpOptions | None = ...
    ) -> None: ...
    def close(self) -> None: ...

class GenerativeModel: ...
class GenerationConfig: ...

__all__ = [
    "Client",
    "GenerativeModel",
    "GenerationConfig",
    "types",
]
