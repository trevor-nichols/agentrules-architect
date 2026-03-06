"""
config/prompts/phase_3_prompts.py

This module provides prompt templates for Phase 3 (Deep Analysis) of the project analysis.
It defines functions to format prompts for the dynamic agents based on their assignments.
"""

from __future__ import annotations

from agentrules.core.utils.system_prompt import normalize_responsibilities


PHASE_3_SYSTEM_PROMPT = (
    "You are {agent_name}, responsible for {agent_role}.\n\n"
    "Responsibilities:\n"
    "{agent_responsibilities}\n\n"
    "Behavior requirements:\n"
    "- Focus on purpose, behavior, and cross-file interactions.\n"
    "- Identify risks, correctness issues, and maintainability concerns.\n"
    "- Separate observations from recommendations.\n"
    "- Return a structured report that is useful to downstream synthesis.\n"
)


def _format_responsibilities(responsibilities: object) -> str:
    cleaned = normalize_responsibilities(responsibilities)
    if not cleaned:
        return "- (no specific responsibilities provided)"
    return "\n".join(f"- {item}" for item in cleaned)


def format_phase3_system_prompt(
    *,
    agent_name: str,
    agent_role: str,
    responsibilities: object,
) -> str:
    return PHASE_3_SYSTEM_PROMPT.format(
        agent_name=agent_name,
        agent_role=agent_role,
        agent_responsibilities=_format_responsibilities(responsibilities),
    )


def format_phase3_prompt(context: dict) -> str:
    """
    Format the prompt for a Phase 3 analysis agent.

    Args:
        context: Dictionary containing agent information and analysis context

    Returns:
        Formatted prompt string
    """
    # Format the tree structure
    tree_structure = context.get("tree_structure", [])
    if isinstance(tree_structure, list):
        tree_structure = "\n".join(tree_structure)

    # Format assigned files
    assigned_files = context.get("assigned_files", [])
    if isinstance(assigned_files, list):
        assigned_files = "\n".join(f"- {file}" for file in assigned_files)

    # Format file contents
    file_contents = context.get("file_contents", {})
    if isinstance(file_contents, dict):
        formatted_contents = []
        for path, content in file_contents.items():
            formatted_contents.append(f"<file path=\"{path}\">\n{content}\n</file>")

        file_content_str = "\n\n".join(formatted_contents)
    else:
        file_content_str = str(file_contents)

    previous_summary = context.get("previous_summary")
    summary_block = ""
    if previous_summary:
        summary_block = f"\nPREVIOUS BATCH SUMMARY:\n{previous_summary}\n"

    # Return a formatted prompt
    return f"""TREE STRUCTURE:
{tree_structure}

ASSIGNED FILES:
{assigned_files}

FILE CONTENTS:
{file_content_str}
{summary_block}

Analyze this scope and return structured findings for the assigned files."""
