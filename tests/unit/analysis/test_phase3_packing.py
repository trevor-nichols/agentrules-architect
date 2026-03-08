import sys
from pathlib import Path
from types import ModuleType

import pytest

from agentrules.core.agents.base import ModelProvider, ReasoningMode
from agentrules.core.types.models import ModelConfig
from agentrules.core.utils.token_packer import PackedBatch

# Stub tavily to avoid dependency import errors when loading analysis modules.
stub_mod = ModuleType("tavily")
stub_mod.AsyncTavilyClient = object  # type: ignore[attr-defined]
stub_mod.TavilyClient = object  # type: ignore[attr-defined]
sys.modules.setdefault("tavily", stub_mod)

from agentrules.core.analysis.phase_3 import Phase3Analysis  # noqa: E402


class DummyArchitect:
    def __init__(self) -> None:
        self.model_name = "gpt-5-mini"
        self._model_config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-5-mini",
            reasoning=ReasoningMode.MEDIUM,
            max_input_tokens=1000,
            estimator_family="heuristic",
        )

    async def analyze(self, context: dict) -> dict:
        return {
            "received_files": context["assigned_files"],
            "previous_summary": context.get("previous_summary"),
        }


class CodexDummyArchitect:
    def __init__(self) -> None:
        self.model_name = "gpt-5.3-codex"
        self.provider = ModelProvider.CODEX
        self._model_config = ModelConfig(
            provider=ModelProvider.CODEX,
            model_name="gpt-5.3-codex",
            reasoning=ReasoningMode.MEDIUM,
            max_input_tokens=400_000,
            estimator_family="tiktoken",
        )
        self.contexts: list[dict] = []

    async def analyze(self, context: dict) -> dict:
        self.contexts.append(context)
        return {
            "received_files": context["assigned_files"],
            "formatted_prompt": context["formatted_prompt"],
            "cwd": context["cwd"],
            "file_contents": context["file_contents"],
        }


@pytest.mark.asyncio
async def test_phase3_batches_are_sequential(monkeypatch):
    phase = Phase3Analysis()
    architect = DummyArchitect()
    agent_def = {
        "id": "agent_1",
        "name": "Batcher",
        "description": "Testing",
        "file_assignments": ["a.py", "b.py"],
    }
    phase.architects = [(architect, agent_def)]

    batches = [
        PackedBatch(assigned_files=["a.py"], file_contents={"a.py": "aaa"}),
        PackedBatch(assigned_files=["b.py"], file_contents={"b.py": "bbb"}),
    ]

    async def _fake_get_file_contents(_dir, assigned):
        return {f: f"content-{f}" for f in assigned}

    monkeypatch.setattr(
        "agentrules.core.analysis.phase_3.get_architect_for_phase",
        lambda *args, **kwargs: architect,
    )
    monkeypatch.setattr(phase, "_pack_batches", lambda **kwargs: batches)
    monkeypatch.setattr(phase, "_get_file_contents", _fake_get_file_contents)

    result = await phase.run({"agents": [agent_def]}, tree=[], directory=Path("."))
    findings = result["findings"][0]
    assert "batches" in findings
    assert len(findings["batches"]) == 2
    assert findings["batches"][0]["result"].get("previous_summary") is None
    assert findings["batches"][1]["result"].get("previous_summary") is not None


@pytest.mark.asyncio
async def test_phase3_codex_path_skips_file_loading_and_uses_repo_runtime_prompt(
    monkeypatch,
    tmp_path: Path,
):
    phase = Phase3Analysis()
    architect = CodexDummyArchitect()
    agent_def = {
        "id": "agent_1",
        "name": "Repo Runtime Agent",
        "description": "Testing",
        "file_assignments": ["a.py", "nested/b.py"],
    }

    def _unexpected_file_load(*_args, **_kwargs):
        raise AssertionError("Phase 3 should not load file bodies for Codex runtime agents")

    monkeypatch.setattr(
        "agentrules.core.analysis.phase_3.get_architect_for_phase",
        lambda *args, **kwargs: architect,
    )
    monkeypatch.setattr(phase, "_get_file_contents", _unexpected_file_load)

    result = await phase.run({"agents": [agent_def]}, tree=["a.py", "nested/b.py"], directory=tmp_path)

    findings = result["findings"][0]
    assert findings["received_files"] == ["a.py", "nested/b.py"]
    assert findings["file_contents"] == {}
    assert findings["cwd"] == str(tmp_path.resolve())
    assert "RUNTIME INSTRUCTIONS:" in findings["formatted_prompt"]
    assert "repository navigation, file reading, and search tools" in findings["formatted_prompt"]
    assert "FILE CONTENTS:" not in findings["formatted_prompt"]
