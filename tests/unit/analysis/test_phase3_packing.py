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
