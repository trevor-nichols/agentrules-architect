"""
config/prompts/phase_3_prompts.py

This module provides prompt templates for Phase 3 (Deep Analysis) of the project analysis.
It defines functions to format prompts for the dynamic agents based on their assignments.
"""



def format_phase3_prompt(context: dict) -> str:
    """
    Format the prompt for a Phase 3 analysis agent.

    Args:
        context: Dictionary containing agent information and analysis context

    Returns:
        Formatted prompt string
    """
    # Extract required context elements with defaults
    agent_name = context.get("agent_name", "Analysis Agent")
    agent_role = context.get("agent_role", "analyzing code files")

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
    return f"""You are {agent_name}, responsible for {agent_role}.

Your task is to perform a deep analysis of the code files assigned to you in this project.

TREE STRUCTURE:
{tree_structure}

ASSIGNED FILES:
{assigned_files}

FILE CONTENTS:
{file_content_str}
{summary_block}

Analyze the code following these guidelines:
1. Focus on understanding the purpose and functionality of each file
2. Identify key patterns and design decisions
3. Note any potential issues, optimizations, or improvements
4. Pay attention to relationships between different components
5. Summarize your findings in a clear, structured format

Format your response as a structured report with clear sections and findings for each file."""
