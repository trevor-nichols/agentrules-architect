"""
config/prompts/phase_5_prompts.py

This module contains the prompt templates used in Phase 5 (Consolidation) of the project analysis.
These prompts are used by the Anthropic agent to generate the final report.
"""

import json

# Phase 5 system prompt (consolidation behavior guidance).
PHASE_5_SYSTEM_PROMPT = (
    "You are the consolidation architect for this analysis pipeline.\n\n"
    "You are part of a team of agents working together to analyze and understand a software project.\n"
    "You will be provided information about the project that prior agents on your team have curated. Your task is to produce a report that will be used when onboarding new developers in the project.\n\n"
    "The report should provide an accurate picture of the project's structure, functionality, and anything else a new developer would find useful.\n\n"
    "Note: You are NOT responsible for identifying security vulnerabilities or code quality issues. Your focus is on understanding the project's structure, dependencies, and tech stack to inform new developers working in this project.\n\n"
    "Behavior requirements:\n"
    "- Combine outputs from phases 1-4 into one final technical report.\n"
    "- Organize by component/module and overall architecture narrative.\n"
    "- Highlight key discoveries, the project's structure, functionality, and tech stack.\n"
)


def format_phase5_system_prompt() -> str:
    return PHASE_5_SYSTEM_PROMPT


# Prompt for the report payload only; behavior lives in system prompts.
PHASE_5_PROMPT = """Analysis results from previous phases:
{results}

Produce the consolidated phase-5 report."""

def format_phase5_prompt(results: dict) -> str:
    """
    Format the Phase 5 prompt with the results from all previous phases.

    Args:
        results: Dictionary containing the results from all previous phases

    Returns:
        Formatted prompt string
    """
    return PHASE_5_PROMPT.format(results=json.dumps(results, indent=2))
