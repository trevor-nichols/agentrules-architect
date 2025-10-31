import json
from pathlib import Path

import pytest

from core.analysis.phase_2 import Phase2Analysis
from core.analysis.phase_3 import Phase3Analysis
from core.analysis.phase_5 import Phase5Analysis
from core.analysis.final_analysis import FinalAnalysis
from tests.utils.offline_stubs import patch_factory_offline


@pytest.mark.asyncio
async def test_phase2_fallback_agents_from_assignments(monkeypatch):
    patch_factory_offline()

    class ArchStub:
        async def create_analysis_plan(self, phase1_results, prompt=None):
            # No agent tags, just file_assignments to trigger fallback
            return {"plan": "<analysis_plan><file_assignments><file_path>a.py</file_path></file_assignments></analysis_plan>"}

    p2 = Phase2Analysis()
    p2.architect = ArchStub()
    out = await p2.run({"phase": 1}, ["a.py"])
    assert "agents" in out and len(out["agents"]) >= 1
    assert out["agents"][0]["file_assignments"] == ["a.py"]


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
async def test_phase5_fallback_report_shaping(monkeypatch):
    patch_factory_offline()

    class ArchStub:
        async def consolidate_results(self, all_results, prompt=None):
            return {"findings": "Y"}

    p5 = Phase5Analysis()
    p5.architect = ArchStub()
    out = await p5.run({"phase1": {}, "phase2": {}, "phase3": {}, "phase4": {}})
    assert out["phase"] == "Consolidation"
    assert out["report"] == "Y"


@pytest.mark.asyncio
async def test_final_analysis_lazy_factory_success_and_error(monkeypatch):
    # Patch factory.get_architect_for_phase to a stub
    import core.agents.factory.factory as factory_mod

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

