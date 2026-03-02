from pathlib import Path
from tempfile import TemporaryDirectory

from agentrules.core.utils.file_creation.phases_output import save_phase_outputs


def _analysis_payload() -> dict:
    return {
        "phase1": {},
        "phase2": {"plan": {}},
        "phase3": {},
        "phase4": {"analysis": "Phase 4"},
        "consolidated_report": {"report": "Phase 5"},
        "final_analysis": {"analysis": "You are a test agent."},
        "metrics": {"time": 0.1},
    }


def test_save_phase_outputs_uses_rules_tree_depth_and_snapshot_reference() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        nested = root / "src" / "nested"
        nested.mkdir(parents=True)
        (nested / "deep.py").write_text("print('deep')\n", encoding="utf-8")
        (root / "top.py").write_text("print('top')\n", encoding="utf-8")

        save_phase_outputs(
            root,
            _analysis_payload(),
            rules_filename="AGENTS.md",
            include_phase_files=False,
            rules_tree_max_depth=1,
            snapshot_reference_filename="SNAPSHOT.custom.md",
        )

        rendered = (root / "AGENTS.md").read_text(encoding="utf-8")
        assert "## Developer Notes" in rendered
        assert "Refer to `SNAPSHOT.custom.md` for the full project snapshot artifact." in rendered
        assert "deep.py" not in rendered


def test_save_phase_outputs_omits_snapshot_reference_when_not_configured() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "top.py").write_text("print('top')\n", encoding="utf-8")

        save_phase_outputs(
            root,
            _analysis_payload(),
            rules_filename="AGENTS.md",
            include_phase_files=False,
            rules_tree_max_depth=2,
            snapshot_reference_filename=None,
        )

        rendered = (root / "AGENTS.md").read_text(encoding="utf-8")
        assert "## Developer Notes" not in rendered
        assert "full project snapshot artifact" not in rendered
