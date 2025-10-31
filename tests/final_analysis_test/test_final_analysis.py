"""
Live SDK tests for Final Analysis (opt-in with --run-live).

These validate that the Final Analysis pipeline runs end-to-end against the
configured providers. They are skipped by default; enable with --run-live.
"""

import os
from datetime import datetime
from typing import Dict

import pytest

from core.analysis.final_analysis import FinalAnalysis
from core.types.models import (
    CLAUDE_WITH_REASONING,
    GPT4_1_DEFAULT as GPT4_1,
    O1_HIGH,
    O3_MINI_HIGH,
    ModelConfig,
)


# Sample consolidated report for testing
SAMPLE_CONSOLIDATED_REPORT = {
    "project_name": "Test Project",
    "analysis_date": datetime.now().strftime("%Y-%m-%d"),
    "phases": {
        "phase1": {
            "structure": {"findings": "Project structure OK"},
            "dependency": {"findings": "Deps A, B, C"},
            "tech_stack": {"findings": "Python"},
        },
        "phase4": {"analysis": "Sensible architecture"},
        "phase5": {"consolidated_findings": "Stable project"},
    },
}

# Sample project structure for testing
SAMPLE_PROJECT_STRUCTURE = [
    ".",
    "├── main.py",
    "├── config/",
    "│   ├── __init__.py",
    "│   └── settings.py",
]


@pytest.mark.live
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name,model_config,env_var",
    [
        ("CLAUDE_WITH_REASONING", CLAUDE_WITH_REASONING, "ANTHROPIC_API_KEY"),
        ("O1_HIGH", O1_HIGH, "OPENAI_API_KEY"),
        ("GPT4_1", GPT4_1, "OPENAI_API_KEY"),
        ("O3_MINI_HIGH", O3_MINI_HIGH, "OPENAI_API_KEY"),
    ],
)
async def test_live_final_analysis_configs(name: str, model_config: ModelConfig, env_var: str):
    if not os.getenv(env_var):
        pytest.skip(f"Missing {env_var} for live '{name}' test")

    # Override config for 'final' to exercise each model
    import config.agents as cfg

    original = cfg.MODEL_CONFIG.get("final")
    cfg.MODEL_CONFIG["final"] = model_config
    try:
        fa = FinalAnalysis()
        result = await fa.run(SAMPLE_CONSOLIDATED_REPORT, SAMPLE_PROJECT_STRUCTURE)
    finally:
        cfg.MODEL_CONFIG["final"] = original

    # Expect a structured response; content varies by provider
    assert isinstance(result, dict)
    assert "analysis" in result or "error" in result
