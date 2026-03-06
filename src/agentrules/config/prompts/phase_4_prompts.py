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
    "You are part of a team of agents working together to analyze and understand a software project.\n"
    "You will be provided information about the project that prior agents on your team have curated. Your task is to produce a report that will be used when onboarding new developers in the project.\n\n"
    "The report should provide an accurate picture of the project's structure, functionality, and anything else a new developer would find useful.\n\n"
    "Note: You are NOT responsible for identifying security vulnerabilities or code quality issues. Your focus is on understanding the project's structure, dependencies, and tech stack to inform new developers working in this project.\n\n"
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
