"""Typed result models for the Codex app-server integration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, cast

RequestId = int | str
CodexAuthMode = Literal["apikey", "chatgpt", "chatgptAuthTokens"] | None
CodexAccountType = Literal["apiKey", "chatgpt"] | None
CodexPlanType = Literal[
    "free",
    "go",
    "plus",
    "pro",
    "team",
    "business",
    "enterprise",
    "edu",
    "unknown",
] | None
CodexReasoningEffort = Literal["none", "minimal", "low", "medium", "high", "xhigh"] | None


def _as_mapping(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return cast(Mapping[str, Any], value)
    return {}


def _as_str(value: object) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def _as_bool(value: object, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    return default


def _iter_mappings(value: object) -> tuple[Mapping[str, Any], ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(_as_mapping(entry) for entry in value)
    return ()


def _iter_strings(value: object, *, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        values = tuple(item for item in (_as_str(entry) for entry in value) if item is not None)
        return values or default
    return default


@dataclass(frozen=True)
class CodexClientInfo:
    name: str
    title: str
    version: str


@dataclass(frozen=True)
class CodexNotification:
    method: str
    params: Mapping[str, Any]


@dataclass(frozen=True)
class CodexServerRequest:
    id: RequestId
    method: str
    params: Mapping[str, Any]


@dataclass(frozen=True)
class CodexInitializeResult:
    user_agent: str
    raw: Mapping[str, Any]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> CodexInitializeResult:
        return cls(
            user_agent=_as_str(payload.get("userAgent")) or "unknown",
            raw=dict(payload),
        )


@dataclass(frozen=True)
class CodexThreadSummary:
    id: str
    raw: Mapping[str, Any]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> CodexThreadSummary:
        return cls(
            id=_as_str(payload.get("id")) or "",
            raw=dict(payload),
        )


@dataclass(frozen=True)
class CodexThreadStartResult:
    thread: CodexThreadSummary
    model: str | None
    cwd: str | None
    raw: Mapping[str, Any]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> CodexThreadStartResult:
        return cls(
            thread=CodexThreadSummary.from_payload(_as_mapping(payload.get("thread"))),
            model=_as_str(payload.get("model")),
            cwd=_as_str(payload.get("cwd")),
            raw=dict(payload),
        )


@dataclass(frozen=True)
class CodexTurnError:
    message: str
    additional_details: str | None
    raw: Mapping[str, Any]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> CodexTurnError:
        return cls(
            message=_as_str(payload.get("message")) or "Unknown Codex turn failure",
            additional_details=_as_str(payload.get("additionalDetails")),
            raw=dict(payload),
        )


@dataclass(frozen=True)
class CodexTurnSummary:
    id: str
    status: str
    error: CodexTurnError | None
    raw: Mapping[str, Any]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> CodexTurnSummary:
        raw_error = _as_mapping(payload.get("error"))
        return cls(
            id=_as_str(payload.get("id")) or "",
            status=_as_str(payload.get("status")) or "unknown",
            error=CodexTurnError.from_payload(raw_error) if raw_error else None,
            raw=dict(payload),
        )


@dataclass(frozen=True)
class CodexTurnStartResult:
    turn: CodexTurnSummary
    raw: Mapping[str, Any]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> CodexTurnStartResult:
        return cls(
            turn=CodexTurnSummary.from_payload(_as_mapping(payload.get("turn"))),
            raw=dict(payload),
        )


@dataclass(frozen=True)
class CodexAccountSummary:
    account_type: CodexAccountType
    auth_mode: CodexAuthMode
    email: str | None
    plan_type: CodexPlanType
    requires_openai_auth: bool
    is_authenticated: bool
    raw_account: Mapping[str, Any] | None

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> CodexAccountSummary:
        account = _as_mapping(payload.get("account"))
        account_type = cast(CodexAccountType, _as_str(account.get("type")))
        payload_auth_mode = cast(CodexAuthMode, _as_str(payload.get("authMode")))
        if payload_auth_mode is not None:
            auth_mode = payload_auth_mode
        elif account_type == "apiKey":
            auth_mode = "apikey"
        elif account_type == "chatgpt":
            auth_mode = "chatgpt"
        else:
            auth_mode = None
        return cls(
            account_type=account_type,
            auth_mode=auth_mode,
            email=_as_str(account.get("email")),
            plan_type=cast(CodexPlanType, _as_str(account.get("planType"))),
            requires_openai_auth=_as_bool(payload.get("requiresOpenaiAuth")),
            is_authenticated=bool(account_type),
            raw_account=dict(account) if account else None,
        )


@dataclass(frozen=True)
class CodexLoginStartResult:
    login_type: str
    login_id: str | None
    auth_url: str | None
    raw: Mapping[str, Any]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> CodexLoginStartResult:
        return cls(
            login_type=_as_str(payload.get("type")) or "unknown",
            login_id=_as_str(payload.get("loginId")),
            auth_url=_as_str(payload.get("authUrl")),
            raw=dict(payload),
        )


@dataclass(frozen=True)
class CodexLoginCompleted:
    success: bool
    login_id: str | None
    error: str | None
    raw: Mapping[str, Any]

    @classmethod
    def from_notification(cls, params: Mapping[str, Any]) -> CodexLoginCompleted:
        return cls(
            success=_as_bool(params.get("success")),
            login_id=_as_str(params.get("loginId")),
            error=_as_str(params.get("error")),
            raw=dict(params),
        )


@dataclass(frozen=True)
class CodexModelReasoningOption:
    reasoning_effort: CodexReasoningEffort
    description: str | None

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> CodexModelReasoningOption:
        return cls(
            reasoning_effort=cast(CodexReasoningEffort, _as_str(payload.get("reasoningEffort"))),
            description=_as_str(payload.get("description")),
        )


@dataclass(frozen=True)
class CodexModelInfo:
    id: str
    model: str
    display_name: str
    description: str
    hidden: bool
    default_reasoning_effort: CodexReasoningEffort
    supported_reasoning_efforts: tuple[CodexModelReasoningOption, ...]
    input_modalities: tuple[str, ...]
    supports_personality: bool
    is_default: bool
    upgrade: str | None
    availability_message: str | None
    raw: Mapping[str, Any]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> CodexModelInfo:
        availability_nux = _as_mapping(payload.get("availabilityNux"))
        return cls(
            id=_as_str(payload.get("id")) or "",
            model=_as_str(payload.get("model")) or _as_str(payload.get("id")) or "",
            display_name=_as_str(payload.get("displayName")) or _as_str(payload.get("id")) or "",
            description=_as_str(payload.get("description")) or "",
            hidden=_as_bool(payload.get("hidden")),
            default_reasoning_effort=cast(
                CodexReasoningEffort,
                _as_str(payload.get("defaultReasoningEffort")),
            ),
            supported_reasoning_efforts=tuple(
                CodexModelReasoningOption.from_payload(entry)
                for entry in _iter_mappings(payload.get("supportedReasoningEfforts"))
            ),
            input_modalities=_iter_strings(payload.get("inputModalities"), default=("text", "image")),
            supports_personality=_as_bool(payload.get("supportsPersonality")),
            is_default=_as_bool(payload.get("isDefault")),
            upgrade=_as_str(payload.get("upgrade")),
            availability_message=_as_str(availability_nux.get("message")),
            raw=dict(payload),
        )


@dataclass(frozen=True)
class CodexModelListPage:
    models: tuple[CodexModelInfo, ...]
    next_cursor: str | None
    raw: Mapping[str, Any]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> CodexModelListPage:
        return cls(
            models=tuple(
                CodexModelInfo.from_payload(entry)
                for entry in _iter_mappings(payload.get("data"))
            ),
            next_cursor=_as_str(payload.get("nextCursor")),
            raw=dict(payload),
        )
