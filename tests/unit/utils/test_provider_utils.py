from __future__ import annotations

from collections import UserDict
from dataclasses import dataclass

from agentrules.core.utils.provider_utils import sdk_object_to_dict


@dataclass(frozen=True)
class _UsageDataclass:
    input_tokens: int
    nested: object


@dataclass(frozen=True)
class _NestedDataclass:
    output_tokens: int


class _ModelDumpObject:
    def model_dump(self) -> dict[str, object]:
        return {"input_tokens": 1, "nested": _NestedDataclass(output_tokens=2)}


class _ModelDumpModeObject:
    def model_dump(self, *, mode: str) -> dict[str, object]:
        return {"mode": mode}


class _ToDictObject:
    def to_dict(self) -> dict[str, object]:
        return {"tool": {"name": "Read"}}


class _DictMethodObject:
    def dict(self) -> dict[str, object]:
        return {"total_tokens": 8}


class _PublicAttributesObject:
    def __init__(self) -> None:
        self.visible = "yes"
        self.nested = _NestedDataclass(output_tokens=4)
        self._private = "no"


class _BrokenThenFallbackObject:
    def __init__(self) -> None:
        self.visible = "fallback"

    def model_dump(self) -> dict[str, object]:
        raise RuntimeError("broken model_dump")

    def to_dict(self) -> dict[str, object]:
        raise RuntimeError("broken to_dict")


def test_sdk_object_to_dict_returns_plain_dict_for_dict() -> None:
    assert sdk_object_to_dict({"input_tokens": 1}) == {"input_tokens": 1}


def test_sdk_object_to_dict_normalizes_mapping() -> None:
    assert sdk_object_to_dict(UserDict({"input_tokens": 1})) == {"input_tokens": 1}


def test_sdk_object_to_dict_normalizes_dataclass() -> None:
    value = _UsageDataclass(input_tokens=1, nested=_NestedDataclass(output_tokens=2))

    assert sdk_object_to_dict(value) == {
        "input_tokens": 1,
        "nested": {"output_tokens": 2},
    }


def test_sdk_object_to_dict_uses_pydantic_model_dump() -> None:
    assert sdk_object_to_dict(_ModelDumpObject()) == {
        "input_tokens": 1,
        "nested": {"output_tokens": 2},
    }


def test_sdk_object_to_dict_retries_model_dump_with_python_mode() -> None:
    assert sdk_object_to_dict(_ModelDumpModeObject()) == {"mode": "python"}


def test_sdk_object_to_dict_uses_sdk_to_dict() -> None:
    assert sdk_object_to_dict(_ToDictObject()) == {"tool": {"name": "Read"}}


def test_sdk_object_to_dict_normalizes_nested_sdk_objects() -> None:
    assert sdk_object_to_dict({"tool": _ToDictObject()}) == {"tool": {"tool": {"name": "Read"}}}


def test_sdk_object_to_dict_uses_dict_method() -> None:
    assert sdk_object_to_dict(_DictMethodObject()) == {"total_tokens": 8}


def test_sdk_object_to_dict_uses_public_attribute_fallback() -> None:
    assert sdk_object_to_dict(_PublicAttributesObject()) == {
        "visible": "yes",
        "nested": {"output_tokens": 4},
    }


def test_sdk_object_to_dict_skips_broken_conversion_methods() -> None:
    assert sdk_object_to_dict(_BrokenThenFallbackObject()) == {"visible": "fallback"}


def test_sdk_object_to_dict_returns_none_for_uncoercible_value() -> None:
    assert sdk_object_to_dict("plain text") is None
