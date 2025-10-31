#!/usr/bin/env python3
"""
core/utils/formatters/clean_cursorrules.py

This module provides functionality for cleaning the generated rules file by
removing any text before the first occurrence of "You are...".

This ensures that cursor rules files start with the proper system prompt format.
"""

# ====================================================
# Importing Required Libraries
# ====================================================

import os
import re

from core.utils.constants import FINAL_RULES_FILENAME

# ====================================================
# Constants
# ====================================================
RULES_FILE_NAME = FINAL_RULES_FILENAME  # Default output filename for the agent rules
START_PATTERN = re.compile(r'\bYou are\b', re.IGNORECASE)  # Pattern to find "You are" text


# ====================================================
# Function: clean_cursorrules_file
# This function cleans the AGENTS.md rules file by removing any text
# before the first occurrence of "You are..."
# ====================================================
def clean_cursorrules_file(file_path: str) -> tuple[bool, str]:
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
# Function: clean_cursorrules
# This function finds and cleans an AGENTS.md rules file in the specified directory
# ====================================================
def clean_cursorrules(directory: str | None = None) -> tuple[bool, str]:
    """
    Find and clean an AGENTS.md rules file in the specified directory.

    Args:
        directory: Optional directory path where to find the file. If None, uses current directory.

    Returns:
        Tuple[bool, str]: Success status and message
    """
    # Determine the full path for the rules file
    if directory:
        cursorrules_path = os.path.join(directory, RULES_FILE_NAME)
    else:
        cursorrules_path = RULES_FILE_NAME

    return clean_cursorrules_file(cursorrules_path)
