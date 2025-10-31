#!/usr/bin/env python3
"""
core/utils/formatters/clean_cursorrules.py

This module provides functionality for cleaning .cursorrules files by removing
any text before the first occurrence of "You are...".

This ensures that cursor rules files start with the proper system prompt format.
"""

# ====================================================
# Importing Required Libraries
# ====================================================

import os
import re
from pathlib import Path
from typing import Tuple, Optional

# ====================================================
# Constants
# ====================================================
CURSORRULES_FILE = ".cursorrules"  # Default name for the .cursorrules file
START_PATTERN = re.compile(r'\bYou are\b', re.IGNORECASE)  # Pattern to find "You are" text


# ====================================================
# Function: clean_cursorrules_file
# This function cleans a .cursorrules file by removing any text 
# before the first occurrence of "You are..."
# ====================================================
def clean_cursorrules_file(file_path: str) -> Tuple[bool, str]:
    """
    Clean a .cursorrules file by removing any text before "You are...".
    
    Args:
        file_path: Path to the .cursorrules file
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        # Check if file exists
        if not os.path.isfile(file_path):
            return False, f"File not found: {file_path}"
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
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
# This function finds and cleans a .cursorrules file in the specified directory
# ====================================================
def clean_cursorrules(directory: Optional[str] = None) -> Tuple[bool, str]:
    """
    Find and clean a .cursorrules file in the specified directory.
    
    Args:
        directory: Optional directory path where to find the file. If None, uses current directory.
    
    Returns:
        Tuple[bool, str]: Success status and message
    """
    # Determine the full path for the .cursorrules file
    if directory:
        cursorrules_path = os.path.join(directory, CURSORRULES_FILE)
    else:
        cursorrules_path = CURSORRULES_FILE
    
    return clean_cursorrules_file(cursorrules_path)
