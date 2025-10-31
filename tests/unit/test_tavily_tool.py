import os
import json
import pytest

from core.agent_tools.web_search import tavily as tavily_mod


@pytest.mark.asyncio
async def test_run_tavily_search_missing_api_key(monkeypatch):
    # Ensure key not present
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    res = await tavily_mod.run_tavily_search("flask")
    data = json.loads(res)
    assert "error" in data
    assert "key" in data["error"].lower()


@pytest.mark.asyncio
async def test_run_tavily_search_clamps_max_results_and_calls_client(monkeypatch):
    calls = {}

    class FakeClient:
        def __init__(self, api_key: str):
            calls["api_key"] = api_key

        async def search(self, query: str, search_depth: str, max_results: int):
            calls["args"] = {
                "query": query,
                "search_depth": search_depth,
                "max_results": max_results,
            }
            return {"ok": True}

    monkeypatch.setenv("TAVILY_API_KEY", "dummy")
    monkeypatch.setattr(tavily_mod, "AsyncTavilyClient", FakeClient)

    res = await tavily_mod.run_tavily_search("docs", search_depth="advanced", max_results=100)
    data = json.loads(res)
    assert data == {"ok": True}
    assert calls["api_key"] == "dummy"
    assert calls["args"]["query"] == "docs"
    assert calls["args"]["search_depth"] == "advanced"
    # clamped to 10
    assert calls["args"]["max_results"] == 10

