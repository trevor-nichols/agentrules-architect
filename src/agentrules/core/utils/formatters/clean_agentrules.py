#!/usr/bin/env python3
"""
core/utils/formatters/clean_agentrules.py

This module provides functionality for cleaning the generated rules file by
removing any text before the first occurrence of "You are...".

This ensures that agent rules files start with the proper system prompt format.
"""

# ====================================================
# Importing Required Libraries
# ====================================================

import os
import re

from agentrules.core.utils.constants import DEFAULT_RULES_FILENAME

# ====================================================
# Constants
# ====================================================
START_PATTERN = re.compile(r'\bYou are\b', re.IGNORECASE)  # Pattern to find "You are" text
DEVELOPMENT_PRINCIPLES_HEADING_PATTERN = re.compile(
    r'^(?P<hashes>#{1,6})\s*Development Principles\s*:?\s*$',
    re.IGNORECASE,
)
MARKDOWN_HEADING_PATTERN = re.compile(r'^(?P<hashes>#{1,6})\s+\S')
EXECPLANS_HEADING = "## ExecPlans"
EXECPLANS_GUIDANCE_LINE = (
    "- When writing complex features or refactors, use an ExecPlan "
    "(as described in `.agent/PLANS.md`) from design to implementation."
)
EXECPLANS_MILESTONES_HEADING = "### Milestones"
EXECPLANS_MILESTONES_LINE = (
    "- When the feature or refactor your writing is significantly complex, "
    "disaggregate the ExecPlan into milestones "
    "(as described in `.agent/templates/MILESTONE_TEMPLATE.md`)"
)
EXECPLANS_CLI_HEADING = "### Prefer CLI creation over manual file creation:"
EXECPLANS_CLI_LINES = (
    "* ExecPlan:",
    "  * Create: `agentrules execplan new \"<title>\" --slug <short-slug> --ms <N>` "
    "(Use `--ms <N>` for deterministic `MS###` sequence assignment).",
    "  * Archive: `agentrules execplan archive EP-YYYYMMDD-NNN`",
    "* Milestones:",
    "  * Create: `agentrules execplan milestone new EP-YYYYMMDD-NNN \"<Milestone Title>\"`",
    "  * Archive: `agentrules execplan milestone archive EP-YYYYMMDD-NNN --ms <N>`",
)
EXECPLANS_GUIDANCE_BLOCK = (
    EXECPLANS_HEADING,
    EXECPLANS_GUIDANCE_LINE,
    "",
    EXECPLANS_MILESTONES_HEADING,
    EXECPLANS_MILESTONES_LINE,
    "",
    EXECPLANS_CLI_HEADING,
    *EXECPLANS_CLI_LINES,
)
EXECPLANS_REQUIRED_LINES = (
    EXECPLANS_GUIDANCE_LINE,
    EXECPLANS_MILESTONES_HEADING,
    EXECPLANS_MILESTONES_LINE,
    EXECPLANS_CLI_HEADING,
    *EXECPLANS_CLI_LINES,
)


def _inject_execplans_guidance(content: str) -> tuple[str, bool, str]:
    if all(line in content for line in EXECPLANS_REQUIRED_LINES):
        return content, False, "ExecPlans guidance already present."

    lines = content.splitlines()
    heading_index = -1
    heading_level = 0
    for index, line in enumerate(lines):
        match = DEVELOPMENT_PRINCIPLES_HEADING_PATTERN.match(line.strip())
        if match:
            heading_index = index
            heading_level = len(match.group("hashes"))
            break

    if heading_index == -1:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend(
            [
                "# Development Principles",
                "",
                *EXECPLANS_GUIDANCE_BLOCK,
            ]
        )
        return "\n".join(lines) + "\n", True, "Added missing Development Principles section with ExecPlans guidance."

    section_end = len(lines)
    for index in range(heading_index + 1, len(lines)):
        line = lines[index]
        heading_match = MARKDOWN_HEADING_PATTERN.match(line.strip())
        if not heading_match:
            continue
        if len(heading_match.group("hashes")) <= heading_level:
            section_end = index
            break

    section_lines = lines[heading_index:section_end]
    execplans_heading_index: int | None = None
    execplans_heading_level = 0
    for index, line in enumerate(section_lines):
        normalized = line.strip().lower().rstrip(":")
        if normalized == "## execplans" or normalized == "### execplans":
            execplans_heading_index = heading_index + index
            heading_match = MARKDOWN_HEADING_PATTERN.match(line.strip())
            if heading_match:
                execplans_heading_level = len(heading_match.group("hashes"))
            break

    if execplans_heading_index is not None:
        execplans_block_end = section_end
        for index in range(execplans_heading_index + 1, section_end):
            line = lines[index]
            heading_match = MARKDOWN_HEADING_PATTERN.match(line.strip())
            if not heading_match:
                continue
            if len(heading_match.group("hashes")) <= execplans_heading_level:
                execplans_block_end = index
                break

        replacement_lines = list(EXECPLANS_GUIDANCE_BLOCK)
        updated_lines = lines[:execplans_heading_index] + replacement_lines + lines[execplans_block_end:]
        return (
            "\n".join(updated_lines) + "\n",
            True,
            "Updated existing ExecPlans guidance under Development Principles.",
        )

    insert_at = section_end
    while insert_at > heading_index and not lines[insert_at - 1].strip():
        insert_at -= 1

    insertion_lines = ["", *EXECPLANS_GUIDANCE_BLOCK, ""]
    updated_lines = lines[:insert_at] + insertion_lines + lines[section_end:]
    return "\n".join(updated_lines) + "\n", True, "Added ExecPlans guidance under Development Principles."


# ====================================================
# Function: clean_agentrules_file
# This function cleans the AGENTS.md rules file by removing any text
# before the first occurrence of "You are..."
# ====================================================
def clean_agentrules_file(file_path: str) -> tuple[bool, str]:
    """
    Clean the rules file by removing any text before "You are...".

    Args:
        file_path: Path to the generated rules file

    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        # Check if file exists
        if not os.path.isfile(file_path):
            return False, f"File not found: {file_path}"

        # Read file content
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        # Find first occurrence of "You are"
        match = START_PATTERN.search(content)
        if not match:
            return False, f"Pattern 'You are' not found in {file_path}"

        # Get the cleaned content starting from "You are"
        cleaned_content = content[match.start():]

        # Write the cleaned content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)

        return True, f"Successfully cleaned {file_path}"

    except Exception as e:
        return False, f"Error cleaning {file_path}: {str(e)}"


# ====================================================
# Function: clean_agentrules
# This function finds and cleans an AGENTS.md rules file in the specified directory
# ====================================================
def clean_agentrules(directory: str | None = None, *, filename: str | None = None) -> tuple[bool, str]:
    """
    Find and clean an AGENTS.md rules file in the specified directory.

    Args:
        directory: Optional directory path where to find the file. If None, uses current directory.

    Returns:
        Tuple[bool, str]: Success status and message
    """
    # Determine the full path for the rules file
    target_filename = filename or DEFAULT_RULES_FILENAME
    if directory:
        agentrules_path = os.path.join(directory, target_filename)
    else:
        agentrules_path = target_filename

    return clean_agentrules_file(agentrules_path)


def ensure_execplans_guidance(directory: str | None = None, *, filename: str | None = None) -> tuple[bool, str]:
    """Ensure AGENTS rules include ExecPlans guidance under Development Principles."""
    target_filename = filename or DEFAULT_RULES_FILENAME
    if directory:
        agentrules_path = os.path.join(directory, target_filename)
    else:
        agentrules_path = target_filename

    try:
        if not os.path.isfile(agentrules_path):
            return False, f"File not found: {agentrules_path}"

        with open(agentrules_path, encoding="utf-8") as file_handle:
            content = file_handle.read()

        updated_content, changed, message = _inject_execplans_guidance(content)
        if changed:
            with open(agentrules_path, "w", encoding="utf-8") as file_handle:
                file_handle.write(updated_content)
        return True, message
    except Exception as error:
        return False, f"Failed to ensure ExecPlans guidance in {agentrules_path}: {error}"
