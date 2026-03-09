"""Utilities for collecting and parsing Codex turn event streams."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from .client import CodexAppServerClient
from .errors import CodexProtocolError
from .models import CodexNotification, CodexTurnSummary


@dataclass(frozen=True)
class ParsedResponse:
    """The canonical representation of a Codex turn result."""

    findings: str | None
    tool_calls: list[dict[str, Any]] | None
    turn: CodexTurnSummary
    error_message: str | None
    notifications: tuple[CodexNotification, ...]


async def collect_turn_notifications(
    client: CodexAppServerClient,
    *,
    thread_id: str,
    turn_id: str,
    timeout_seconds: float,
) -> tuple[CodexNotification, ...]:
    """Collect notifications until the matching `turn/completed` event arrives."""

    collected: list[CodexNotification] = []
    while True:
        notification = await client.wait_for_next_notification(timeout_seconds=timeout_seconds)
        collected.append(notification)
        if not _is_matching_turn_completed(notification, thread_id=thread_id, turn_id=turn_id):
            continue
        return tuple(collected)


def parse_turn_notifications(
    notifications: Sequence[CodexNotification],
    *,
    thread_id: str,
    turn_id: str,
) -> ParsedResponse:
    """Parse the Codex event stream for one completed turn."""

    agent_message_text: str | None = None
    agent_message_deltas: list[str] = []
    completed_turn: CodexTurnSummary | None = None

    for notification in notifications:
        method = notification.method
        params = notification.params

        if method == "item/agentMessage/delta":
            if not _notification_matches_turn(params, thread_id=thread_id, turn_id=turn_id):
                continue
            delta = params.get("delta")
            if isinstance(delta, str):
                agent_message_deltas.append(delta)
            continue

        if method == "item/completed":
            if not _notification_matches_turn(params, thread_id=thread_id, turn_id=turn_id):
                continue
            item = params.get("item")
            if not isinstance(item, dict):
                continue
            if item.get("type") != "agentMessage":
                continue
            text = item.get("text")
            if isinstance(text, str):
                agent_message_text = text
            continue

        if method == "turn/completed":
            if not _notification_matches_turn(
                params,
                thread_id=thread_id,
                turn_id=turn_id,
                require_turn_container=True,
            ):
                continue
            turn_payload = params.get("turn")
            if not isinstance(turn_payload, dict):
                raise CodexProtocolError("Codex turn/completed notification did not include a turn payload.")
            completed_turn = CodexTurnSummary.from_payload(turn_payload)

    if completed_turn is None:
        raise CodexProtocolError("Codex turn notifications did not include a matching turn/completed event.")

    findings = agent_message_text
    if not findings:
        combined = "".join(agent_message_deltas).strip()
        findings = combined or None

    error_message = _format_turn_error(completed_turn)
    return ParsedResponse(
        findings=findings,
        tool_calls=None,
        turn=completed_turn,
        error_message=error_message,
        notifications=tuple(notifications),
    )


def _is_matching_turn_completed(notification: CodexNotification, *, thread_id: str, turn_id: str) -> bool:
    return (
        notification.method == "turn/completed"
        and _notification_matches_turn(
            notification.params,
            thread_id=thread_id,
            turn_id=turn_id,
            require_turn_container=True,
        )
    )


def _notification_matches_turn(
    params: dict[str, Any] | Any,
    *,
    thread_id: str,
    turn_id: str,
    require_turn_container: bool = False,
) -> bool:
    if not isinstance(params, dict):
        return False
    if params.get("threadId") != thread_id:
        return False

    if require_turn_container:
        turn = params.get("turn")
        return isinstance(turn, dict) and turn.get("id") == turn_id

    return params.get("turnId") == turn_id


def _format_turn_error(turn: CodexTurnSummary) -> str | None:
    if turn.status != "failed" or turn.error is None:
        return None
    if turn.error.additional_details:
        return f"{turn.error.message} ({turn.error.additional_details})"
    return turn.error.message
