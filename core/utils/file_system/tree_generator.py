#!/usr/bin/env python3
"""
core/utils/file_system/tree_generator.py

This module provides enhanced tree generation functionality for visualizing
directory structures with file type icons and customizable exclusion rules.

It is used by the main analysis process to generate visual representations
of project structures.
"""

# ====================================================
# Importing Necessary Libraries
# This section imports external libraries that the script needs to function.
# Each library provides specific functionalities used later in the code.
# ====================================================

import fnmatch  # Provides support for Unix shell-style wildcards
from pathlib import Path  # Offers a way to interact with files and directories in a more object-oriented manner

from config.exclusions import (  # Importing predefined exclusion lists
    EXCLUDED_DIRS,
    EXCLUDED_EXTENSIONS,
    EXCLUDED_FILES,
)
from core.utils.constants import FINAL_RULES_FILENAME

# ====================================================
# Setting Up Default Exclusion Constants
# These constants define which directories, files, and file extensions
# should be ignored by default when generating the tree structure.
# ====================================================

# Use the centralized exclusion constants
DEFAULT_EXCLUDE_DIRS = EXCLUDED_DIRS

# Combine excluded files and patterns based on extensions
DEFAULT_EXCLUDE_PATTERNS = set()
# Add excluded files
for file in EXCLUDED_FILES:
    DEFAULT_EXCLUDE_PATTERNS.add(file)
# Add excluded extensions as patterns
for ext in EXCLUDED_EXTENSIONS:
    DEFAULT_EXCLUDE_PATTERNS.add(f'*{ext}')

# ====================================================
# Defining File Type Icons and Descriptions
# This section maps file extensions and specific filenames to emoji icons
# and provides human-readable descriptions for each icon.
# ====================================================

# File type emojis
FILE_ICONS: dict[str, str] = {
    # Programming Languages
    '.py': '🐍',    # Python
    '.js': '📜',    # JavaScript
    '.jsx': '⚛️',    # React
    '.ts': '💠',    # TypeScript
    '.tsx': '⚛️',    # React TypeScript
    '.html': '🌐',   # HTML
    '.css': '🎨',    # CSS
    '.scss': '🎨',   # SCSS
    '.sass': '🎨',   # SASS
    '.less': '🎨',   # LESS
    '.json': '📋',   # JSON
    '.xml': '📋',    # XML
    '.yaml': '📋',   # YAML
    '.yml': '📋',    # YML
    '.md': '📝',     # Markdown
    '.txt': '📄',    # Text
    '.sh': '💻',     # Shell
    '.bash': '💻',   # Bash
    '.zsh': '💻',    # Zsh
    '.env': '🔒',    # Environment
    'Dockerfile': '🐳',    # Dockerfile
    'docker-compose.yml': '🐳',  # Docker compose
    'package.json': '📦',  # Package JSON
    'requirements.txt': '📦',  # Python requirements
    'README': '📖',        # README
}

# File type descriptions for the key
ICON_DESCRIPTIONS = {
    '📁': 'Directory',
    '🐍': 'Python',
    '📜': 'JavaScript',
    '⚛️': 'React',
    '💠': 'TypeScript',
    '🌐': 'HTML',
    '🎨': 'CSS/SCSS/SASS',
    '📋': 'Data file (JSON/YAML/XML)',
    '📝': 'Markdown',
    '📄': 'Text file',
    '💻': 'Shell script',
    '🔒': 'Environment file',
    '📦': 'Package file',
    '📖': 'README',
    '🐳': 'Docker file',
    '️': 'Error/Warning'
}

# ====================================================
# Function Definitions
# This section contains all the functions that perform the core logic
# of the script, such as getting file icons, checking exclusions,
# generating the tree, creating a key, and saving the output.
# ====================================================


def get_file_icon(path: Path) -> str:
    """
    Get the appropriate emoji icon for a file.

    Args:
        path: Path object to get icon for

    Returns:
        str: Emoji icon representing the file type
    """
    if path.is_dir():
        return '📁'

    # Check for exact filename matches first
    if path.name in FILE_ICONS:
        return FILE_ICONS[path.name]

    # Then check extensions
    ext = path.suffix.lower()
    if ext in FILE_ICONS:
        return FILE_ICONS[ext]

    # Default file icon
    return '📄'


def should_exclude(item: Path, exclude_dirs: set[str], exclude_patterns: set[str]) -> bool:
    """
    Check if an item should be excluded based on directory name or file pattern.

    Args:
        item: Path object to check
        exclude_dirs: Set of directory names to exclude
        exclude_patterns: Set of file patterns to exclude

    Returns:
        bool: True if item should be excluded, False otherwise
    """
    # Check if it's a directory in the exclude list
    if item.is_dir() and (item.name in exclude_dirs):
        return True

    # Check file patterns
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(item.name.lower(), pattern.lower()):
            return True

    return False


def generate_tree(
    path: Path,
    prefix: str = "",
    exclude_dirs: set[str] | None = None,
    exclude_patterns: set[str] | None = None,
    max_depth: int = 4,
    current_depth: int = 0
) -> list[str]:
    """
    Generate a tree structure of the specified directory path.

    Args:
        path: The directory path to generate tree for
        prefix: Current prefix for the tree line (used for recursion)
        exclude_dirs: Set of directory names to exclude
        exclude_patterns: Set of patterns to exclude (e.g., "*.pyc")
        max_depth: Maximum depth to traverse
        current_depth: Current depth in the traversal

    Returns:
        List of strings representing the tree structure
    """
    if exclude_dirs is None:
        exclude_dirs = DEFAULT_EXCLUDE_DIRS
    if exclude_patterns is None:
        exclude_patterns = DEFAULT_EXCLUDE_PATTERNS

    # If we've reached max depth, indicate there's more
    if current_depth >= max_depth:
        return [f"{prefix}└── ... (max depth reached)"]

    tree = []

    if isinstance(path, str):
        path = Path(path)

    try:
        # Get all items in the directory
        items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))

        # Filter out excluded items
        items = [item for item in items if not should_exclude(item, exclude_dirs, exclude_patterns)]

        # Process each item
        for index, item in enumerate(items):
            is_last = index == len(items) - 1
            connector = "└── " if is_last else "├── "

            # Add the current item to the tree with its icon
            icon = get_file_icon(item)
            tree.append(f"{prefix}{connector}{icon} {item.name}")

            # If it's a directory, recursively process its contents
            if item.is_dir():
                extension = "    " if is_last else "│   "
                tree.extend(
                    generate_tree(
                        item,
                        prefix + extension,
                        exclude_dirs,
                        exclude_patterns,
                        max_depth,
                        current_depth + 1
                    )
                )
    except PermissionError:
        tree.append(f"{prefix}└── ⚠️ <Permission Denied>")
    except Exception as e:
        tree.append(f"{prefix}└── ⚠️ <Error: {str(e)}>")

    return tree


def generate_key(tree_content: list[str]) -> list[str]:
    """
    Generate a key of emojis used in the tree.

    Args:
        tree_content: List of strings containing the tree structure

    Returns:
        List of strings representing the key
    """
    used_icons = set()

    # Extract all emojis used in the tree
    for line in tree_content:
        # Find emoji in the line (emojis are between connector and filename)
        parts = line.split(' ')
        for part in parts:
            if any(icon in part for icon in ICON_DESCRIPTIONS):
                used_icons.add(part.strip())

    if not used_icons:
        return []

    # Generate key lines
    key_lines = [
        "File Type Key:",
        "------------"
    ]

    # Add descriptions for used icons
    for icon in sorted(used_icons):
        if icon in ICON_DESCRIPTIONS:
            key_lines.append(f"{icon} : {ICON_DESCRIPTIONS[icon]}")

    return key_lines + [""]  # Add empty line after key


def save_tree_to_file(tree_content: list[str], path: Path) -> str:
    """
    Save the tree structure to the generated rules file.

    Args:
        tree_content: List of strings containing the tree structure
        path: The directory path that was processed

    Returns:
        The path to the saved file
    """
    output_file = path / FINAL_RULES_FILENAME

    # Remove delimiters if they exist
    filtered_content = tree_content
    has_wrapping_tags = (
        len(tree_content) >= 2
        and tree_content[0] == "<project_structure>"
        and tree_content[-1] == "</project_structure>"
    )
    if has_wrapping_tags:
        filtered_content = tree_content[1:-1]

    # Generate key for used icons
    key = generate_key(filtered_content)

    header = [
        "<!-- BEGIN_STRUCTURE -->",
        "# Project Directory Structure",
        "------------------------------"
    ]

    if key:  # Only add key if there are icons used
        header.extend(key)

    header.append("```")

    footer = [
        "```",
        "<!-- END_STRUCTURE -->"
    ]

    with output_file.open('w', encoding='utf-8') as f:
        f.write('\n'.join(header + filtered_content + footer))

    return str(output_file)


def get_project_tree(directory: Path, max_depth: int = 4) -> list[str]:
    """
    Generate a tree structure for a project directory.
    This is the main function to be used from other modules.

    Args:
        directory: The project directory path
        max_depth: Maximum depth to traverse

    Returns:
        List of strings representing the tree structure with delimiters
    """
    # Generate the tree
    tree = generate_tree(
        directory,
        max_depth=max_depth,
        exclude_dirs=DEFAULT_EXCLUDE_DIRS,
        exclude_patterns=DEFAULT_EXCLUDE_PATTERNS
    )

    # Add the key
    key = generate_key(tree)

    # Prepare the complete tree with key
    if key:
        complete_tree = key + tree
    else:
        complete_tree = tree

    # Add the delimiters
    delimited_tree = ["<project_structure>"] + complete_tree + ["</project_structure>"]

    return delimited_tree
