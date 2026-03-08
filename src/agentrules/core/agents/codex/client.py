"""Async JSON-RPC client for Codex app-server."""

from __future__ import annotations

import asyncio
import importlib.metadata
import logging
from collections import deque
from collections.abc import Callable, Mapping
from itertools import count
from typing import Any

from .errors import CodexError, CodexProcessError, CodexProtocolError
from .models import (
    CodexAccountSummary,
    CodexClientInfo,
    CodexInitializeResult,
    CodexLoginCompleted,
    CodexLoginStartResult,
    CodexModelInfo,
    CodexModelListPage,
    CodexNotification,
    CodexServerRequest,
    RequestId,
)
from .process import CodexAppServerProcess
from .protocol import (
    build_notification,
    build_request,
    decode_message,
    encode_message,
    parse_notification,
    parse_response_result,
    parse_server_request,
)

logger = logging.getLogger("project_extractor")


NotificationPredicate = Callable[[CodexNotification], bool]
ServerRequestPredicate = Callable[[CodexServerRequest], bool]


def _default_client_info() -> CodexClientInfo:
    version = "0.0.0+local"
    try:
        version = importlib.metadata.version("agentrules")
    except importlib.metadata.PackageNotFoundError:
        pass
    return CodexClientInfo(
        name="agentrules",
        title="AgentRules Architect",
        version=version,
    )


class CodexAppServerClient:
    """Maintain one initialized app-server connection and request/notification state."""

    def __init__(
        self,
        process: CodexAppServerProcess,
        *,
        client_info: CodexClientInfo | None = None,
        request_timeout_seconds: float = 30.0,
    ) -> None:
        self._process = process
        self._client_info = client_info or _default_client_info()
        self._request_timeout_seconds = request_timeout_seconds
        self._request_ids = count(0)
        self._pending_requests: dict[RequestId, asyncio.Future[dict[str, Any]]] = {}
        self._notification_buffer: deque[CodexNotification] = deque()
        self._server_request_buffer: deque[CodexServerRequest] = deque()
        self._notification_event = asyncio.Event()
        self._server_request_event = asyncio.Event()
        self._reader_task: asyncio.Task[None] | None = None
        self._stderr_task: asyncio.Task[None] | None = None
        self._connected = False
        self._closing = False
        self._connection_error: BaseException | None = None
        self._initialize_result: CodexInitializeResult | None = None

    @property
    def initialize_result(self) -> CodexInitializeResult | None:
        return self._initialize_result

    @property
    def is_connected(self) -> bool:
        return self._connected and self._connection_error is None

    async def __aenter__(self) -> CodexAppServerClient:
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def connect(self) -> CodexInitializeResult:
        if self._connected and self._initialize_result is not None:
            return self._initialize_result

        self._reset_connection_state()
        await self._process.start()
        self._stderr_task = asyncio.create_task(self._process.read_stderr_forever())
        self._reader_task = asyncio.create_task(self._read_stdout_forever())

        try:
            payload = await self.request(
                "initialize",
                {
                    "clientInfo": {
                        "name": self._client_info.name,
                        "title": self._client_info.title,
                        "version": self._client_info.version,
                    }
                },
            )
            self._initialize_result = CodexInitializeResult.from_payload(payload)
            await self.notify("initialized", {})
            self._connected = True
        except Exception:
            await self.close()
            raise

        logger.debug("Initialized Codex app-server client", extra=self._process.describe_launch())
        return self._initialize_result

    async def close(self) -> None:
        self._closing = True
        self._connected = False

        self._fail_pending_requests(CodexProcessError("Codex app-server connection closed."))

        reader_task = self._reader_task
        stderr_task = self._stderr_task
        self._reader_task = None
        self._stderr_task = None

        if reader_task is not None:
            reader_task.cancel()
        if stderr_task is not None:
            stderr_task.cancel()

        for task in (reader_task, stderr_task):
            if task is None:
                continue
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:  # pragma: no cover - defensive cleanup
                logger.debug("Codex task shutdown raised", exc_info=True)

        await self._process.stop()

    async def request(
        self,
        method: str,
        params: Mapping[str, Any] | None = None,
        *,
        timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        self._ensure_transport_ready()
        request_id = next(self._request_ids)
        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending_requests[request_id] = future
        await self._send_message(build_request(method, request_id, params))
        try:
            return await asyncio.wait_for(
                future,
                timeout=self._request_timeout_seconds if timeout_seconds is None else timeout_seconds,
            )
        finally:
            self._pending_requests.pop(request_id, None)

    async def notify(self, method: str, params: Mapping[str, Any] | None = None) -> None:
        self._ensure_transport_ready()
        await self._send_message(build_notification(method, params))

    async def read_account(self, *, refresh_token: bool = False) -> CodexAccountSummary:
        payload = await self.request("account/read", {"refreshToken": refresh_token})
        return CodexAccountSummary.from_payload(payload)

    async def start_chatgpt_login(self) -> CodexLoginStartResult:
        payload = await self.request("account/login/start", {"type": "chatgpt"})
        return CodexLoginStartResult.from_payload(payload)

    async def wait_for_login_completion(
        self,
        login_id: str | None,
        *,
        timeout_seconds: float = 300.0,
    ) -> CodexLoginCompleted:
        notification = await self.wait_for_notification(
            "account/login/completed",
            predicate=lambda item: (
                login_id is None or CodexLoginCompleted.from_notification(item.params).login_id == login_id
            ),
            timeout_seconds=timeout_seconds,
        )
        return CodexLoginCompleted.from_notification(notification.params)

    async def logout(self) -> None:
        await self.request("account/logout")

    async def list_models(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        include_hidden: bool | None = None,
    ) -> CodexModelListPage:
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor
        if include_hidden is not None:
            params["includeHidden"] = include_hidden
        payload = await self.request("model/list", params)
        return CodexModelListPage.from_payload(payload)

    async def list_all_models(
        self,
        *,
        limit: int = 100,
        include_hidden: bool = False,
    ) -> tuple[CodexModelInfo, ...]:
        models: list[CodexModelInfo] = []
        cursor: str | None = None
        while True:
            page = await self.list_models(limit=limit, cursor=cursor, include_hidden=include_hidden)
            models.extend(page.models)
            if page.next_cursor is None:
                return tuple(models)
            cursor = page.next_cursor

    async def wait_for_notification(
        self,
        method: str,
        *,
        predicate: NotificationPredicate | None = None,
        timeout_seconds: float | None = None,
    ) -> CodexNotification:
        timeout = self._request_timeout_seconds if timeout_seconds is None else timeout_seconds
        return await asyncio.wait_for(
            self._wait_for_buffered_message(
                self._notification_buffer,
                self._notification_event,
                matcher=lambda item: item.method == method and (predicate is None or predicate(item)),
            ),
            timeout=timeout,
        )

    async def wait_for_server_request(
        self,
        method: str,
        *,
        predicate: ServerRequestPredicate | None = None,
        timeout_seconds: float | None = None,
    ) -> CodexServerRequest:
        timeout = self._request_timeout_seconds if timeout_seconds is None else timeout_seconds
        return await asyncio.wait_for(
            self._wait_for_buffered_message(
                self._server_request_buffer,
                self._server_request_event,
                matcher=lambda item: item.method == method and (predicate is None or predicate(item)),
            ),
            timeout=timeout,
        )

    def drain_notifications(self) -> tuple[CodexNotification, ...]:
        drained = tuple(self._notification_buffer)
        self._notification_buffer.clear()
        self._notification_event.clear()
        return drained

    def drain_server_requests(self) -> tuple[CodexServerRequest, ...]:
        drained = tuple(self._server_request_buffer)
        self._server_request_buffer.clear()
        self._server_request_event.clear()
        return drained

    async def _wait_for_buffered_message(
        self,
        buffer: deque[Any],
        event: asyncio.Event,
        *,
        matcher: Callable[[Any], bool],
    ) -> Any:
        while True:
            self._ensure_transport_ready()
            for index, item in enumerate(buffer):
                if matcher(item):
                    matched = buffer[index]
                    del buffer[index]
                    if not buffer:
                        event.clear()
                    return matched
            await event.wait()

    async def _send_message(self, payload: dict[str, Any]) -> None:
        writer = self._process.stdin
        writer.write(encode_message(payload))
        await writer.drain()

    async def _read_stdout_forever(self) -> None:
        try:
            while True:
                line = await self._process.stdout.readline()
                if not line:
                    break
                if not line.strip():
                    continue
                message = decode_message(line)
                if "id" in message and "method" not in message:
                    self._handle_response(message)
                    continue
                if "id" in message and "method" in message:
                    self._server_request_buffer.append(parse_server_request(message))
                    self._server_request_event.set()
                    continue
                if "method" in message:
                    self._notification_buffer.append(parse_notification(message))
                    self._notification_event.set()
                    continue
                raise CodexProtocolError("Received JSON-RPC message without method or id.")
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._set_connection_error(exc)
            return

        if not self._closing:
            if self._process.returncode not in (None, 0):
                error = CodexProcessError(
                    f"Codex app-server exited with status {self._process.returncode}.",
                    stderr=self._process.recent_stderr,
                )
            else:
                error = CodexProcessError("Codex app-server closed the connection unexpectedly.")
            self._set_connection_error(error)

    def _handle_response(self, message: dict[str, Any]) -> None:
        request_id = message.get("id")
        if not isinstance(request_id, (int, str)):
            logger.debug("Discarding malformed Codex response without a valid id: %s", message)
            return
        future = self._pending_requests.get(request_id)
        if future is None:
            logger.debug("Discarding unexpected Codex response id=%s", request_id)
            return
        if future.done():
            return
        try:
            result = parse_response_result(message)
        except Exception as exc:
            future.set_exception(exc)
            return
        future.set_result(result)

    def _reset_connection_state(self) -> None:
        self._closing = False
        self._connection_error = None
        self._connected = False
        self._initialize_result = None
        self._notification_buffer.clear()
        self._server_request_buffer.clear()
        self._notification_event.clear()
        self._server_request_event.clear()
        self._pending_requests.clear()

    def _set_connection_error(self, error: BaseException) -> None:
        if self._connection_error is None:
            self._connection_error = error
        self._connected = False
        self._fail_pending_requests(error)
        self._notification_event.set()
        self._server_request_event.set()

    def _fail_pending_requests(self, error: BaseException) -> None:
        for future in list(self._pending_requests.values()):
            if not future.done():
                future.set_exception(error)

    def _ensure_transport_ready(self) -> None:
        if self._reader_task is None or self._stderr_task is None:
            raise CodexProcessError("Codex app-server client is not connected.")
        if self._closing:
            raise CodexProcessError("Codex app-server client is closing.")
        if self._connection_error is not None:
            if isinstance(self._connection_error, CodexError):
                raise self._connection_error
            raise CodexProcessError(str(self._connection_error), stderr=self._process.recent_stderr)
