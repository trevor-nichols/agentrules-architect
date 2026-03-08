"""Deterministic fake Codex app-server used by unit tests."""

from __future__ import annotations

import json
import sys
from typing import Any

MODELS = [
    {
        "id": "gpt-5.3-codex",
        "model": "gpt-5.3-codex",
        "displayName": "gpt-5.3-codex",
        "description": "Frontier agentic coding model.",
        "hidden": False,
        "defaultReasoningEffort": "medium",
        "supportedReasoningEfforts": [
            {"reasoningEffort": "low", "description": "Lower latency"},
            {"reasoningEffort": "medium", "description": "Balanced"},
        ],
        "inputModalities": ["text", "image"],
        "supportsPersonality": True,
        "isDefault": True,
        "availabilityNux": {"message": "Available on ChatGPT Pro"},
    },
    {
        "id": "gpt-5.4",
        "model": "gpt-5.4",
        "displayName": "gpt-5.4",
        "description": "General frontier model.",
        "hidden": False,
        "defaultReasoningEffort": "high",
        "supportedReasoningEfforts": [
            {"reasoningEffort": "medium", "description": "Balanced"},
            {"reasoningEffort": "high", "description": "Deep analysis"},
        ],
        "inputModalities": ["text", "image"],
        "supportsPersonality": True,
        "isDefault": False,
    },
    {
        "id": "gpt-5.2-codex",
        "model": "gpt-5.2-codex",
        "displayName": "gpt-5.2-codex",
        "description": "Previous coding tier.",
        "hidden": True,
        "defaultReasoningEffort": "low",
        "supportedReasoningEfforts": [
            {"reasoningEffort": "low", "description": "Lower latency"},
        ],
        "inputModalities": ["text"],
        "supportsPersonality": False,
        "isDefault": False,
    },
]

state: dict[str, Any] = {
    "initialized": False,
    "account": None,
    "login_counter": 0,
}


def send(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def send_error(request_id: int | str | None, message: str, *, code: int = -32000) -> None:
    send({"id": request_id, "error": {"code": code, "message": message}})


def current_account_payload() -> dict[str, Any]:
    account = state["account"]
    return {
        "account": account,
        "requiresOpenaiAuth": True,
        "authMode": account["type"].lower() if isinstance(account, dict) and account.get("type") == "apiKey" else (
            "chatgpt" if isinstance(account, dict) and account.get("type") == "chatgpt" else None
        ),
    }


def handle_request(message: dict[str, Any]) -> None:
    method = message.get("method")
    request_id = message.get("id")
    raw_params = message.get("params")
    params: dict[str, Any] = raw_params if isinstance(raw_params, dict) else {}

    if method == "initialize":
        if state["initialized"]:
            send_error(request_id, "Already initialized", code=-32002)
            return
        state["initialized"] = True
        send({"id": request_id, "result": {"userAgent": "codex-fake/1.0"}})
        return

    if not state["initialized"]:
        send_error(request_id, "Not initialized", code=-32001)
        return

    if method == "account/read":
        send({"id": request_id, "result": current_account_payload()})
        return

    if method == "account/login/start":
        login_type = params.get("type")
        if login_type != "chatgpt":
            send_error(request_id, f"Unsupported login type: {login_type}")
            return

        state["login_counter"] += 1
        login_id = f"login-{state['login_counter']}"
        send(
            {
                "id": request_id,
                "result": {
                    "type": "chatgpt",
                    "loginId": login_id,
                    "authUrl": f"https://chatgpt.com/fake-auth/{login_id}",
                },
            }
        )
        state["account"] = {
            "type": "chatgpt",
            "email": "codex-user@example.com",
            "planType": "pro",
        }
        send(
            {
                "method": "account/login/completed",
                "params": {"loginId": login_id, "success": True, "error": None},
            }
        )
        send(
            {
                "method": "account/updated",
                "params": {"authMode": "chatgpt", "planType": "pro"},
            }
        )
        return

    if method == "account/logout":
        state["account"] = None
        send({"id": request_id, "result": {}})
        send({"method": "account/updated", "params": {"authMode": None}})
        return

    if method == "model/list":
        include_hidden = bool(params.get("includeHidden"))
        limit = int(params.get("limit") or len(MODELS))
        cursor = params.get("cursor")
        start_index = int(cursor) if isinstance(cursor, str) and cursor.isdigit() else 0
        visible_models = MODELS if include_hidden else [entry for entry in MODELS if not entry.get("hidden")]
        page = visible_models[start_index : start_index + limit]
        next_cursor = start_index + limit
        send(
            {
                "method": "server/heartbeat",
                "params": {"cursor": cursor or "0", "count": len(page)},
            }
        )
        send(
            {
                "id": request_id,
                "result": {
                    "data": page,
                    "nextCursor": str(next_cursor) if next_cursor < len(visible_models) else None,
                },
            }
        )
        return

    send_error(request_id, f"Unknown method: {method}", code=-32601)


def handle_notification(message: dict[str, Any]) -> None:
    method = message.get("method")
    if method == "initialized":
        return


def main() -> None:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        message = json.loads(line)
        if "id" in message:
            handle_request(message)
        else:
            handle_notification(message)


if __name__ == "__main__":
    main()
