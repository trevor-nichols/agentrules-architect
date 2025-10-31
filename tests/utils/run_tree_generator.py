#!/usr/bin/env python3
"""
tests/utils/run_tree_generator.py

A simple script to demonstrate the tree generator functionality.
This script runs the tree generator on the specified directory and outputs the result.

Usage:
    python run_tree_generator.py [directory_path] [max_depth]

Args:
    directory_path (optional): Path to the directory to analyze. Default is current directory.
    max_depth (optional): Maximum directory depth to display. Default is 4.
"""

import os
import sys
from pathlib import Path

# Add the project root to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.utils.file_system.tree_generator import get_project_tree


def main():
    """
    Run the tree generator on the specified directory and print the result.
    """
    # Parse command line arguments
    args = sys.argv[1:]
    target_dir = Path.cwd()  # Default to current directory
    max_depth = 4  # Default max depth
    
    # Parse directory path if provided
    if len(args) >= 1 and not args[0].isdigit():
        path_arg = args[0]
        target_dir = Path(path_arg)
        args = args[1:]  # Remove the processed argument
        
        if not target_dir.exists() or not target_dir.is_dir():
            print(f"Error: '{path_arg}' is not a valid directory.")
            sys.exit(1)
    
    # Parse max_depth if provided
    if len(args) >= 1:
        try:
            max_depth = int(args[0])
        except ValueError:
            print(f"Error: max_depth must be an integer. Using default value of {max_depth}.")
    
    print(f"Generating tree for: {target_dir}")
    print(f"Max depth: {max_depth}")
    print("-" * 50)
    
    # Generate the tree
    tree = get_project_tree(target_dir, max_depth=max_depth)
    
    # Print the tree
    for line in tree:
        print(line)


if __name__ == "__main__":
    main()
