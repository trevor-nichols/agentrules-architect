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
    "When writing complex features or significant refactors, "
    "use an ExecPlan (as described in .agent/PLANS.md) from design to implementation."
)


def _inject_execplans_guidance(content: str) -> tuple[str, bool, str]:
    if EXECPLANS_GUIDANCE_LINE in content:
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
                EXECPLANS_HEADING,
                EXECPLANS_GUIDANCE_LINE,
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
    for line in section_lines:
        normalized = line.strip().lower().rstrip(":")
        if normalized == "## execplans" or normalized == "### execplans":
            return content, False, "ExecPlans heading already present under Development Principles."

    insert_at = section_end
    while insert_at > heading_index and not lines[insert_at - 1].strip():
        insert_at -= 1

    insertion_lines = ["", EXECPLANS_HEADING, EXECPLANS_GUIDANCE_LINE, ""]
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
