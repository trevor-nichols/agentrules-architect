"""Low-level JSON-RPC helpers for Codex app-server."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, cast

from .errors import CodexJsonRpcError, CodexProtocolError
from .models import CodexNotification, CodexServerRequest, RequestId

JsonObject = dict[str, Any]


def encode_message(message: Mapping[str, Any]) -> bytes:
    """Encode a JSON-RPC message as a single JSONL record."""

    return (json.dumps(message, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def decode_message(line: bytes) -> JsonObject:
    """Decode a single JSONL record from stdout."""

    try:
        payload = json.loads(line.decode("utf-8"))
    except Exception as exc:  # pragma: no cover - defensive
        raise CodexProtocolError(f"Failed to decode Codex JSON-RPC message: {exc}") from exc
    if not isinstance(payload, dict):
        raise CodexProtocolError(f"Expected JSON object from Codex app-server, got {type(payload)!r}.")
    return cast(JsonObject, payload)


def build_request(
    method: str,
    request_id: RequestId,
    params: Mapping[str, Any] | None = None,
) -> JsonObject:
    message: JsonObject = {"method": method, "id": request_id}
    if params is not None:
        message["params"] = dict(params)
    return message


def build_notification(method: str, params: Mapping[str, Any] | None = None) -> JsonObject:
    message: JsonObject = {"method": method}
    if params is not None:
        message["params"] = dict(params)
    return message


def parse_notification(payload: Mapping[str, Any]) -> CodexNotification:
    method = payload.get("method")
    if not isinstance(method, str):
        raise CodexProtocolError("Notification payload is missing a string method.")
    params = payload.get("params")
    return CodexNotification(
        method=method,
        params=cast(Mapping[str, Any], params) if isinstance(params, Mapping) else {},
    )


def parse_server_request(payload: Mapping[str, Any]) -> CodexServerRequest:
    method = payload.get("method")
    request_id = payload.get("id")
    if not isinstance(method, str) or not isinstance(request_id, (int, str)):
        raise CodexProtocolError("Server request payload is missing a valid method or id.")
    params = payload.get("params")
    return CodexServerRequest(
        id=request_id,
        method=method,
        params=cast(Mapping[str, Any], params) if isinstance(params, Mapping) else {},
    )


def parse_response_result(payload: Mapping[str, Any]) -> JsonObject:
    if "error" in payload:
        error_payload = payload.get("error")
        if isinstance(error_payload, Mapping):
            code = error_payload.get("code")
            raise CodexJsonRpcError(
                code if isinstance(code, int) else None,
                str(error_payload.get("message") or "Unknown Codex JSON-RPC error"),
                error_payload.get("data"),
            )
        raise CodexJsonRpcError(None, "Unknown Codex JSON-RPC error")

    result = payload.get("result")
    if result is None:
        return {}
    if not isinstance(result, dict):
        raise CodexProtocolError(f"Expected JSON object result, got {type(result)!r}.")
    return cast(JsonObject, result)
