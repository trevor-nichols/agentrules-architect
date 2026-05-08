"""Shared provider adapter utilities."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from typing import Any


def sdk_object_to_dict(value: Any) -> dict[str, Any] | None:
    """Convert provider SDK objects into plain dictionaries at adapter boundaries.

    Provider adapters should use this helper when normalizing SDK response
    objects into AgentRules' plain dict/list/scalar result shape. The helper is
    intentionally defensive: a broken conversion method is skipped so response
    parsing can continue using the next supported shape.
    """

    if value is None:
        return None

    if isinstance(value, Mapping):
        return _mapping_to_plain_dict(value)

    if _is_dataclass_instance(value):
        return _mapping_to_plain_dict(asdict(value))

    for method_name in ("model_dump", "to_dict", "dict"):
        converted = _call_mapping_method(value, method_name)
        if converted is not None:
            return converted

    return _public_attributes_to_dict(value)


def _call_mapping_method(value: Any, method_name: str) -> dict[str, Any] | None:
    method = getattr(value, method_name, None)
    if not callable(method):
        return None

    call_attempts: tuple[dict[str, Any], ...]
    if method_name == "model_dump":
        call_attempts = ({}, {"mode": "python"})
    else:
        call_attempts = ({},)

    for kwargs in call_attempts:
        try:
            result = method(**kwargs)
        except TypeError:
            continue
        except Exception:
            continue
        converted = _value_to_dict(result)
        if converted is not None:
            return converted

    return None


def _value_to_dict(value: Any) -> dict[str, Any] | None:
    if isinstance(value, Mapping):
        return _mapping_to_plain_dict(value)
    if _is_dataclass_instance(value):
        return _mapping_to_plain_dict(asdict(value))
    return _public_attributes_to_dict(value)


def _mapping_to_plain_dict(value: Mapping[Any, Any]) -> dict[str, Any]:
    return {str(key): _to_plain_value(item) for key, item in value.items()}


def _to_plain_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _mapping_to_plain_dict(value)
    if _is_dataclass_instance(value):
        return _mapping_to_plain_dict(asdict(value))
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_to_plain_value(item) for item in value]

    converted = sdk_object_to_dict(value)
    if converted is not None:
        return converted
    return value


def _public_attributes_to_dict(value: Any) -> dict[str, Any] | None:
    try:
        attributes = vars(value)
    except TypeError:
        return None

    return {
        key: _to_plain_value(item)
        for key, item in attributes.items()
        if not key.startswith("_")
    }


def _is_dataclass_instance(value: Any) -> bool:
    return is_dataclass(value) and not isinstance(value, type)


__all__ = ["sdk_object_to_dict"]
