from __future__ import annotations

import asyncio
import os

import pytest

from agentrules.core.agents.claude_code.client import execute_query, stream_query
from agentrules.core.agents.claude_code.errors import ClaudeCodeExecutionError


@pytest.mark.asyncio
async def test_execute_query_maps_timeout_to_claude_code_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import claude_agent_sdk

    async def _slow_query(*_args: object, **_kwargs: object):
        await asyncio.sleep(1)
        yield object()

    monkeypatch.setattr(claude_agent_sdk, "query", _slow_query)

    with pytest.raises(ClaudeCodeExecutionError, match="timed out after 0.01 seconds"):
        await execute_query("Inspect the repository.", {}, timeout_seconds=0.01)


@pytest.mark.asyncio
async def test_execute_query_scrubs_inherited_api_key_env_until_sdk_starts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import claude_agent_sdk

    monkeypatch.setenv("ANTHROPIC_API_KEY", "parent-api-key")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "parent-auth-token")
    observed_api_key_values: list[str | None] = []
    observed_auth_token_values: list[str | None] = []

    async def _capturing_query(*_args: object, **_kwargs: object):
        observed_api_key_values.append(os.environ.get("ANTHROPIC_API_KEY"))
        observed_auth_token_values.append(os.environ.get("ANTHROPIC_AUTH_TOKEN"))
        yield object()
        observed_api_key_values.append(os.environ.get("ANTHROPIC_API_KEY"))
        observed_auth_token_values.append(os.environ.get("ANTHROPIC_AUTH_TOKEN"))
        yield object()

    monkeypatch.setattr(claude_agent_sdk, "query", _capturing_query)

    messages = await execute_query(
        "Inspect the repository.",
        {},
        sanitized_env_vars=("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"),
    )

    assert len(messages) == 2
    assert observed_api_key_values == [None, "parent-api-key"]
    assert observed_auth_token_values == [None, "parent-auth-token"]
    assert os.environ["ANTHROPIC_API_KEY"] == "parent-api-key"
    assert os.environ["ANTHROPIC_AUTH_TOKEN"] == "parent-auth-token"


@pytest.mark.asyncio
async def test_stream_query_maps_timeout_to_claude_code_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import claude_agent_sdk

    async def _slow_query(*_args: object, **_kwargs: object):
        await asyncio.sleep(1)
        yield object()

    monkeypatch.setattr(claude_agent_sdk, "query", _slow_query)

    with pytest.raises(ClaudeCodeExecutionError, match="timed out after 0.01 seconds"):
        async for _message in stream_query("Inspect the repository.", {}, timeout_seconds=0.01):
            pass


@pytest.mark.asyncio
async def test_stream_query_scrubs_inherited_api_key_env_until_sdk_starts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import claude_agent_sdk

    monkeypatch.setenv("ANTHROPIC_API_KEY", "parent-api-key")
    observed_api_key_values: list[str | None] = []

    async def _capturing_query(*_args: object, **_kwargs: object):
        observed_api_key_values.append(os.environ.get("ANTHROPIC_API_KEY"))
        yield object()
        observed_api_key_values.append(os.environ.get("ANTHROPIC_API_KEY"))
        yield object()

    monkeypatch.setattr(claude_agent_sdk, "query", _capturing_query)

    messages = []
    async for message in stream_query(
        "Inspect the repository.",
        {},
        sanitized_env_vars=("ANTHROPIC_API_KEY",),
    ):
        messages.append(message)

    assert len(messages) == 2
    assert observed_api_key_values == [None, "parent-api-key"]
    assert os.environ["ANTHROPIC_API_KEY"] == "parent-api-key"
