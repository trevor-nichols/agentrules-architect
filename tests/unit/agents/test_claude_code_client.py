from __future__ import annotations

import asyncio

import pytest

from agentrules.core.agents.claude_code.client import execute_query
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
