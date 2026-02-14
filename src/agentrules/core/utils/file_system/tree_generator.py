#!/usr/bin/env python3
"""
core/utils/file_system/tree_generator.py

This module provides tree generation functionality for visualizing
directory structures with customizable exclusion rules.

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

from pathspec import PathSpec

from agentrules.config.exclusions import (  # Importing predefined exclusion lists
    EXCLUDED_DIRS,
    EXCLUDED_EXTENSIONS,
    EXCLUDED_FILES,
)
from agentrules.core.utils.constants import DEFAULT_RULES_FILENAME

# ====================================================
# Setting Up Default Exclusion Constants
# These constants define which directories, files, and file extensions
# should be ignored by default when generating the tree structure.
# ====================================================

# Use the centralized exclusion constants
DEFAULT_EXCLUDE_DIRS = EXCLUDED_DIRS


def _build_exclude_patterns(files: set[str], extensions: set[str]) -> set[str]:
    patterns: set[str] = set()
    for file in files:
        patterns.add(file)
    for ext in extensions:
        patterns.add(f"*{ext}")
    return patterns


DEFAULT_EXCLUDE_PATTERNS = _build_exclude_patterns(EXCLUDED_FILES, EXCLUDED_EXTENSIONS)

# ====================================================
# Function Definitions
# This section contains all the functions that perform the core logic
# of the script, such as checking exclusions, generating the tree,
# and saving the output.
# ====================================================


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
    max_depth: int = 5,
    current_depth: int = 0,
    *,
    gitignore_spec: PathSpec | None = None,
    root: Path | None = None,
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
    if isinstance(path, str):
        path = Path(path)

    if root is None:
        root = path

    if exclude_dirs is None:
        exclude_dirs = DEFAULT_EXCLUDE_DIRS
    if exclude_patterns is None:
        exclude_patterns = DEFAULT_EXCLUDE_PATTERNS

    # If we've reached max depth, indicate there's more
    if current_depth >= max_depth:
        return [f"{prefix}└── ... (max depth reached)"]

    tree = []

    try:
        # Get all items in the directory
        items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))

        # Filter out excluded items
        filtered_items = []
        for item in items:
            if gitignore_spec is not None:
                try:
                    relative = item.relative_to(root).as_posix()
                except ValueError:
                    relative = item.as_posix()
                if gitignore_spec.match_file(relative):
                    continue
            if should_exclude(item, exclude_dirs, exclude_patterns):
                continue
            filtered_items.append(item)

        items = filtered_items

        # Process each item
        for index, item in enumerate(items):
            is_last = index == len(items) - 1
            connector = "└── " if is_last else "├── "

            # Add the current item to the tree
            tree.append(f"{prefix}{connector}{item.name}")

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
                        current_depth + 1,
                        gitignore_spec=gitignore_spec,
                        root=root,
                    )
                )
    except PermissionError:
        tree.append(f"{prefix}└── <Permission Denied>")
    except Exception as e:
        tree.append(f"{prefix}└── <Error: {str(e)}>")

    return tree


def save_tree_to_file(tree_content: list[str], path: Path, *, rules_filename: str | None = None) -> str:
    """
    Save the tree structure to the generated rules file.

    Args:
        tree_content: List of strings containing the tree structure
        path: The directory path that was processed

    Returns:
        The path to the saved file
    """
    output_file = path / (rules_filename or DEFAULT_RULES_FILENAME)

    # Remove delimiters if they exist
    filtered_content = tree_content
    has_wrapping_tags = (
        len(tree_content) >= 2
        and tree_content[0] == "<project_structure>"
        and tree_content[-1] == "</project_structure>"
    )
    if has_wrapping_tags:
        filtered_content = tree_content[1:-1]

    header = [
        "<!-- BEGIN_STRUCTURE -->",
        "# Project Directory Structure",
        "------------------------------"
    ]

    header.append("```")

    footer = [
        "```",
        "<!-- END_STRUCTURE -->"
    ]

    with output_file.open('w', encoding='utf-8') as f:
        f.write('\n'.join(header + filtered_content + footer))

    return str(output_file)


def get_project_tree(
    directory: Path,
    max_depth: int = 5,
    *,
    exclude_dirs: set[str] | None = None,
    exclude_files: set[str] | None = None,
    exclude_extensions: set[str] | None = None,
    gitignore_spec: PathSpec | None = None,
) -> list[str]:
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
    dirs = exclude_dirs or DEFAULT_EXCLUDE_DIRS
    files = exclude_files or EXCLUDED_FILES
    extensions = exclude_extensions or EXCLUDED_EXTENSIONS
    patterns = _build_exclude_patterns(set(files), set(extensions))

    tree = generate_tree(
        directory,
        max_depth=max_depth,
        exclude_dirs=dirs,
        exclude_patterns=patterns,
        gitignore_spec=gitignore_spec,
        root=directory,
    )

    # Add the delimiters
    delimited_tree = ["<project_structure>"] + tree + ["</project_structure>"]

    return delimited_tree
