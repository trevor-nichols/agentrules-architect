from pathlib import Path
from typing import Any, cast

import pytest

from agentrules.core.agents.base import ModelProvider
from agentrules.core.analysis.final_analysis import FinalAnalysis
from agentrules.core.analysis.phase_2 import Phase2Analysis
from agentrules.core.analysis.phase_3 import Phase3Analysis
from agentrules.core.analysis.phase_5 import Phase5Analysis
from tests.utils.offline_stubs import patch_factory_offline


@pytest.mark.asyncio
async def test_phase2_uses_legacy_prompt_when_structured_outputs_unsupported(monkeypatch):
    patch_factory_offline()

    class ArchStub:
        provider = ModelProvider.ANTHROPIC
        model_name = "claude-opus-4-1"

        def __init__(self) -> None:
            self.seen_prompt = ""

        async def create_analysis_plan(self, phase1_results, prompt=None):
            self.seen_prompt = prompt or ""
            return {"plan": "<analysis_plan></analysis_plan>"}

    p2 = Phase2Analysis()
    arch = ArchStub()
    p2.architect = cast(Any, arch)
    await p2.run({"phase": 1}, ["a.py"])
    assert "## OUTPUT FORMAT" in arch.seen_prompt
    assert "<analysis_plan>" in arch.seen_prompt


@pytest.mark.asyncio
async def test_phase2_uses_structured_prompt_when_supported(monkeypatch):
    patch_factory_offline()

    class ArchStub:
        provider = ModelProvider.OPENAI
        model_name = "gpt-5-mini"

        def __init__(self) -> None:
            self.seen_prompt = ""

        async def create_analysis_plan(self, phase1_results, prompt=None):
            self.seen_prompt = prompt or ""
            return {"plan": "Structured plan", "agents": []}

    p2 = Phase2Analysis()
    arch = ArchStub()
    p2.architect = cast(Any, arch)
    await p2.run({"phase": 1}, ["a.py"])
    assert "Output contract:" in arch.seen_prompt
    assert "## OUTPUT FORMAT" not in arch.seen_prompt


@pytest.mark.asyncio
async def test_phase2_fallback_agents_from_assignments(monkeypatch):
    patch_factory_offline()

    class ArchStub:
        async def create_analysis_plan(self, phase1_results, prompt=None):
            # No agent tags, just file_assignments to trigger fallback
            return {"plan": "<analysis_plan><file_assignments><file_path>a.py</file_path></file_assignments></analysis_plan>"}

    p2 = Phase2Analysis()
    p2.architect = cast(Any, ArchStub())
    out = await p2.run({"phase": 1}, ["a.py"])
    assert "agents" in out and len(out["agents"]) >= 1
    assert out["agents"][0]["file_assignments"] == ["a.py"]


@pytest.mark.asyncio
async def test_phase2_invalid_preparsed_agents_falls_back_to_plan(monkeypatch):
    patch_factory_offline()

    class ArchStub:
        async def create_analysis_plan(self, phase1_results, prompt=None):
            return {
                "agents": [{"id": "agent_1"}],  # Invalid; missing file_assignments
                "plan": (
                    "<analysis_plan><agent_1 name='A'>"
                    "<file_assignments><file_path>a.py</file_path></file_assignments>"
                    "</agent_1></analysis_plan>"
                ),
            }

    p2 = Phase2Analysis()
    p2.architect = cast(Any, ArchStub())
    out = await p2.run({"phase": 1}, ["a.py"])
    assert "agents" in out and len(out["agents"]) == 1
    assert out["agents"][0]["id"] == "agent_1"
    assert out["agents"][0]["file_assignments"] == ["a.py"]


@pytest.mark.asyncio
async def test_phase2_non_string_plan_payload_does_not_fail(monkeypatch):
    patch_factory_offline()

    class ArchStub:
        async def create_analysis_plan(self, phase1_results, prompt=None):
            return {"plan": {"kind": "json_plan", "meta": {"x": 1}}}

    p2 = Phase2Analysis()
    p2.architect = cast(Any, ArchStub())
    out = await p2.run({"phase": 1}, ["a.py"])
    assert "error" not in out
    assert out.get("agents") == []


@pytest.mark.asyncio
async def test_phase3_fallback_when_no_agents(tmp_path: Path, monkeypatch):
    patch_factory_offline()
    # Create a file; ensure tree includes it
    f = tmp_path / "x.py"
    f.write_text("print('x')")
    tree = ["x.py"]
    p3 = Phase3Analysis()
    out = await p3.run({}, tree, tmp_path)
    assert out["phase"] == "Deep Analysis"
    assert isinstance(out.get("findings"), list)


@pytest.mark.asyncio
async def test_phase3_ignores_invalid_responsibility_items(tmp_path: Path, monkeypatch):
    patch_factory_offline()
    (tmp_path / "x.py").write_text("print('x')", encoding="utf-8")

    p3 = Phase3Analysis()
    out = await p3.run(
        {
            "agents": [
                {
                    "id": "agent_1",
                    "name": "Architecture Agent",
                    "description": "architecture review",
                    "responsibilities": ["Inspect boundaries", 3, None, {"bad": True}],
                    "file_assignments": ["x.py"],
                }
            ]
        },
        ["x.py"],
        tmp_path,
    )

    assert out["phase"] == "Deep Analysis"
    assert "error" not in out
    assert isinstance(out.get("findings"), list)


@pytest.mark.asyncio
async def test_phase5_fallback_report_shaping(monkeypatch):
    patch_factory_offline()

    class ArchStub:
        async def consolidate_results(self, all_results, prompt=None):
            return {"findings": "Y"}

    p5 = Phase5Analysis()
    p5.architect = cast(Any, ArchStub())
    out = await p5.run({"phase1": {}, "phase2": {}, "phase3": {}, "phase4": {}})
    assert out["phase"] == "Consolidation"
    assert out["report"] == "Y"


@pytest.mark.asyncio
async def test_final_analysis_lazy_factory_success_and_error(monkeypatch):
    # Patch factory.get_architect_for_phase to a stub
    import agentrules.core.agents.factory.factory as factory_mod

    class ArchOK:
        async def final_analysis(self, consolidated_report, prompt=None):
            return {"analysis": "OK"}

    class ArchFail:
        async def final_analysis(self, consolidated_report, prompt=None):
            raise RuntimeError("boom")

    # Success path
    factory_mod.get_architect_for_phase = lambda phase: ArchOK()
    fa = FinalAnalysis()
    out = await fa.run({"report": "R"}, ["."])
    assert out["analysis"] == "OK"

    # Error path
    factory_mod.get_architect_for_phase = lambda phase: ArchFail()
    fa2 = FinalAnalysis()
    out2 = await fa2.run({"report": "R"}, ["."])
    assert "error" in out2


@pytest.mark.asyncio
async def test_final_analysis_prompt_uses_overridden_rules_filename(monkeypatch):
    import agentrules.core.agents.factory.factory as factory_mod

    captured_prompt: dict[str, str] = {"prompt": ""}

    class ArchCapture:
        async def final_analysis(self, consolidated_report, prompt=None):
            captured_prompt["prompt"] = prompt or ""
            return {"analysis": "OK"}

    factory_mod.get_architect_for_phase = lambda phase: ArchCapture()
    fa = FinalAnalysis()
    out = await fa.run({"report": "R"}, ["."], rules_filename="CLAUDE.md")
    assert out["analysis"] == "OK"
    assert "tailored CLAUDE.md file using" in captured_prompt["prompt"]
