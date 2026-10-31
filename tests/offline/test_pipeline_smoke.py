"""Run the public CLI through all analysis phases without provider credentials."""

import os
import subprocess
import sys
from pathlib import Path


def test_offline_cli_writes_rules_and_phase_artifacts(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = project / "tests" / "tests_input" / "main.py"
    source.parent.mkdir(parents=True)
    source.write_text('def greet(name: str) -> str:\n    return f"Hello, {name}"\n', encoding="utf-8")
    (project / "pyproject.toml").write_text('[project]\nname = "smoke-project"\nversion = "0.1.0"\n', encoding="utf-8")

    environment = {**os.environ, "AGENTRULES_CONFIG_DIR": str(tmp_path / "config")}
    completed = subprocess.run(
        [sys.executable, "-m", "agentrules", "analyze", "--offline", str(project)],
        capture_output=True,
        text=True,
        env=environment,
        timeout=90,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert (
        (project / "AGENTS.md").read_text(encoding="utf-8").startswith("You are an offline final analysis assistant.")
    )
    phase_outputs = project / "phases_output"
    assert "tests/tests_input/main.py" in (phase_outputs / "phase2_planning.md").read_text(encoding="utf-8")
    assert "Code Analysis Agent" in (phase_outputs / "phase3_analysis.md").read_text(encoding="utf-8")
    assert (phase_outputs / "phase5_consolidation.md").is_file()
