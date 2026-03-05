"""
config/prompts/phase_4_prompts.py

This module contains the prompts used by Phase 4 (Synthesis).
Centralizing prompts here makes it easier to edit and maintain them without
modifying the core logic of the agents.
"""

import json

# Phase 4 system prompt (synthesis behavior guidance).
PHASE_4_SYSTEM_PROMPT = (
    "You are the synthesis architect for this analysis pipeline.\n\n"
    "Behavior requirements:\n"
    "- Merge phase-3 findings into a coherent developer report.\n"
    "- Prioritize high-impact architectural insights and risks.\n"
    "- Preserve technical fidelity while reducing redundancy.\n"
)


def format_phase4_system_prompt() -> str:
    return PHASE_4_SYSTEM_PROMPT


# Prompt template for Phase 4 (Synthesis) user/task payload.
PHASE_4_PROMPT = """Synthesis input:
<analysis_results>
{phase3_results}
</analysis_results>

Produce the phase-4 synthesis report.
"""

def format_phase4_prompt(phase3_results: dict) -> str:
    """
    Format the Phase 4 prompt with the Phase 3 results.

    Args:
        phase3_results: Dictionary containing the results from Phase 3

    Returns:
        Formatted prompt string
    """
    return PHASE_4_PROMPT.format(
        phase3_results=json.dumps(phase3_results, indent=2)
    )
