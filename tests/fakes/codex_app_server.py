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
    "thread_counter": 0,
    "turn_counter": 0,
    "item_counter": 0,
    "threads": {},
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


def next_thread_id() -> str:
    state["thread_counter"] += 1
    return f"thr-{state['thread_counter']}"


def next_turn_id() -> str:
    state["turn_counter"] += 1
    return f"turn-{state['turn_counter']}"


def next_item_id() -> str:
    state["item_counter"] += 1
    return f"item-{state['item_counter']}"


def _extract_text_input(params: dict[str, Any]) -> str:
    inputs = params.get("input")
    if not isinstance(inputs, list):
        return ""
    parts: list[str] = []
    for item in inputs:
        if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
            parts.append(item["text"])
    return "\n".join(parts)


def _build_structured_payload(output_schema: dict[str, Any]) -> dict[str, Any]:
    properties = output_schema.get("properties") if isinstance(output_schema, dict) else None
    if not isinstance(properties, dict):
        return {"analysis": "Structured output from fake Codex"}

    if "plan" in properties and "agents" in properties:
        return {
            "plan": "Analyze the repository in focused batches.",
            "agents": [
                {
                    "id": "agent_1",
                    "name": "Architecture Agent",
                    "description": "Inspect core architecture boundaries.",
                    "responsibilities": ["Review module boundaries"],
                    "file_assignments": ["src/agentrules/core/agents/codex/architect.py"],
                }
            ],
            "reasoning": "The fake runtime returned a deterministic phase 2 plan.",
        }

    if "report" in properties:
        return {
            "phase": "Consolidation",
            "report": "Codex consolidated the prior phase outputs.",
        }

    if "analysis" in properties:
        return {"analysis": "Codex produced a structured analysis response."}

    return {key: f"value-for-{key}" for key in properties}


def _build_agent_message(text_input: str, output_schema: Any) -> str:
    if "TURN_FAIL" in text_input:
        return ""
    if output_schema is not None:
        if "BAD_SCHEMA_JSON" in text_input:
            return "this is not valid json"
        return json.dumps(_build_structured_payload(output_schema), separators=(",", ":"))
    prompt_excerpt = text_input.strip().splitlines()[0] if text_input.strip() else "empty prompt"
    return f"Codex analyzed: {prompt_excerpt}"


def _handle_thread_start(request_id: int | str | None, params: dict[str, Any]) -> None:
    thread_id = next_thread_id()
    thread = {
        "id": thread_id,
        "preview": "",
        "modelProvider": "openai",
        "createdAt": 1730910000,
    }
    state["threads"][thread_id] = {
        "model": params.get("model"),
        "cwd": params.get("cwd"),
        "sandbox": params.get("sandbox"),
    }
    send({"method": "thread/started", "params": {"thread": {"id": thread_id}}})
    send(
        {
            "id": request_id,
            "result": {
                "thread": thread,
                "model": params.get("model") or "gpt-5.3-codex",
                "cwd": params.get("cwd") or "/tmp/project",
                "modelProvider": "openai",
                "approvalPolicy": params.get("approvalPolicy") or "never",
                "sandbox": {"type": "readOnly", "networkAccess": False},
            },
        }
    )


def _handle_turn_start(request_id: int | str | None, params: dict[str, Any]) -> None:
    thread_id = params.get("threadId")
    if not isinstance(thread_id, str) or thread_id not in state["threads"]:
        send_error(request_id, f"Unknown thread: {thread_id}")
        return

    turn_id = next_turn_id()
    item_id = next_item_id()
    text_input = _extract_text_input(params)
    output_schema = params.get("outputSchema") if isinstance(params.get("outputSchema"), dict) else None
    agent_message = _build_agent_message(text_input, output_schema)

    send({"id": request_id, "result": {"turn": {"id": turn_id, "status": "inProgress", "items": [], "error": None}}})
    send({"method": "turn/started", "params": {"threadId": thread_id, "turn": {"id": turn_id, "status": "inProgress", "items": [], "error": None}}})
    send({"method": "item/started", "params": {"threadId": thread_id, "turnId": turn_id, "item": {"id": item_id, "type": "agentMessage", "text": ""}}})

    if "TURN_FAIL" in text_input:
        send(
            {
                "method": "turn/completed",
                "params": {
                    "threadId": thread_id,
                    "turn": {
                        "id": turn_id,
                        "status": "failed",
                        "items": [],
                        "error": {"message": "Fake Codex turn failure", "additionalDetails": "Simulated failure"},
                    },
                },
            }
        )
        return

    midpoint = max(len(agent_message) // 2, 1)
    for delta in (agent_message[:midpoint], agent_message[midpoint:]):
        if delta:
            send(
                {
                    "method": "item/agentMessage/delta",
                    "params": {"threadId": thread_id, "turnId": turn_id, "itemId": item_id, "delta": delta},
                }
            )

    send(
        {
            "method": "item/completed",
            "params": {
                "threadId": thread_id,
                "turnId": turn_id,
                "item": {"id": item_id, "type": "agentMessage", "text": agent_message},
            },
        }
    )
    send(
        {
            "method": "turn/completed",
            "params": {
                "threadId": thread_id,
                "turn": {"id": turn_id, "status": "completed", "items": [], "error": None},
            },
        }
    )


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

    if method == "thread/start":
        _handle_thread_start(request_id, params)
        return

    if method == "turn/start":
        _handle_turn_start(request_id, params)
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
