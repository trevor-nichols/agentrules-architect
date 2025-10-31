#!/usr/bin/env python3
"""
core/utils/file_system/file_retriever.py

This module provides functionality for retrieving file contents from a codebase.
It respects exclusion patterns from config/exclusions.py and formats the output
with file paths and contents in a structured format for AI analysis.

This module is used by the analysis phases to retrieve and process file contents
for deep code analysis.
"""

# ====================================================
# Importing Necessary Libraries
# This section imports all the external libraries needed for this script to work.
# Each import statement brings in code from another file or module, making
# those functions and tools available for use here.
# ====================================================

import os
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple, Generator
import fnmatch
import logging
from config.exclusions import EXCLUDED_DIRS, EXCLUDED_FILES, EXCLUDED_EXTENSIONS

# ====================================================
# Initial Setup
# This part sets up a logger to record important events and messages,
# and defines a list of encodings to handle different file types.
# ====================================================

# Initialize logger
logger = logging.getLogger("project_extractor")

# Define file encoding to try in order of preference
ENCODINGS = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']


# ====================================================
# Function: should_exclude
# This function checks if a given file or directory should be excluded
# based on predefined rules (like excluding certain directory names or file patterns).
# ====================================================

def should_exclude(path: Path, exclude_dirs: Set[str], exclude_patterns: Set[str]) -> bool:
    """
    Determine if a file or directory should be excluded based on exclusion patterns.
    
    Args:
        path: The path to check
        exclude_dirs: Set of directory names to exclude
        exclude_patterns: Set of file patterns to exclude
        
    Returns:
        bool: True if the path should be excluded, False otherwise
    """
    # Check if any part of the path is in excluded dirs
    for part in path.parts:
        if part in exclude_dirs:
            return True
    
    # Check filename against excluded patterns
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(path.name, pattern):
            return True
    
    return False


# ====================================================
# Function: read_file_with_fallback
# This function tries to read a file using different encodings.
# If it fails with one encoding, it tries the next until it can read the file.
# ====================================================

def read_file_with_fallback(file_path: Path) -> Tuple[str, str]:
    """
    Read file content with encoding fallback.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Tuple[str, str]: Tuple of (file_content, encoding_used)
    """
    for encoding in ENCODINGS:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return content, encoding
        except UnicodeDecodeError:
            continue
    
    # If all encodings fail, read as binary and decode with replacement
    with open(file_path, 'rb') as f:
        content = f.read().decode('utf-8', errors='replace')
    return content, 'utf-8 (with replacement)'


# ====================================================
# Function: format_file_content
# This function takes the content of a file and adds the file path
# to the beginning and end, making it easy to identify where the content came from.
# ====================================================

def format_file_content(file_path: Path, content: str) -> str:
    """
    Format file content with file path in the specified format.
    
    Args:
        file_path: Path to the file
        content: File content
        
    Returns:
        str: Formatted file content with path
    """
    relative_path = file_path.as_posix()
    return f"<file_path=\"{relative_path}\">\n{content}\n</file>"


# ====================================================
# Function: list_files
# This function goes through a directory and finds all files,
# excluding those that match the exclusion rules. It searches
# up to a certain depth (how many folders deep it goes).
# ====================================================

def list_files(
    directory: Path,
    exclude_dirs: Optional[Set[str]] = None,
    exclude_patterns: Optional[Set[str]] = None,
    max_depth: int = 10,
) -> Generator[Path, None, None]:
    """
    List all files in a directory that aren't excluded.
    
    Args:
        directory: Directory to search
        exclude_dirs: Set of directory names to exclude
        exclude_patterns: Set of file patterns to exclude
        max_depth: Maximum depth to search
        
    Yields:
        Path: File paths that match criteria
    """
    if exclude_dirs is None:
        exclude_dirs = EXCLUDED_DIRS
    
    if exclude_patterns is None:
        # Combine excluded files and patterns based on extensions
        exclude_patterns = set()
        # Add excluded files
        for file in EXCLUDED_FILES:
            exclude_patterns.add(file)
        # Add excluded extensions as patterns
        for ext in EXCLUDED_EXTENSIONS:
            exclude_patterns.add(f'*{ext}')
    
    def _list_files_recursive(path: Path, current_depth: int = 0) -> Generator[Path, None, None]:
        if current_depth > max_depth:
            return
        
        try:
            for item in path.iterdir():
                if should_exclude(item, exclude_dirs, exclude_patterns):
                    continue
                
                if item.is_file():
                    yield item
                elif item.is_dir():
                    yield from _list_files_recursive(item, current_depth + 1)
        except PermissionError:
            logger.warning(f"Permission denied: {path}")
    
    yield from _list_files_recursive(directory)


# ====================================================
# Function: get_file_contents
# This function retrieves the contents of all files in a directory,
# while respecting exclusion rules, size limits, and a maximum number of files.
# ====================================================

def get_file_contents(
    directory: Path,
    exclude_dirs: Optional[Set[str]] = None,
    exclude_patterns: Optional[Set[str]] = None,
    max_size_kb: int = 1000,  # Don't process files larger than 1MB by default
    max_files: int = 100,  # Limit the number of files to process
) -> Dict[str, str]:
    """
    Get the contents of all files in a directory, excluding those that match exclusion patterns.
    
    Args:
        directory: Directory to search
        exclude_dirs: Set of directory names to exclude
        exclude_patterns: Set of file patterns to exclude
        max_size_kb: Maximum file size in KB to process
        max_files: Maximum number of files to process
        
    Returns:
        Dict[str, str]: Dictionary of {file_path: formatted_content}
    """
    file_contents = {}
    file_count = 0
    
    for file_path in list_files(directory, exclude_dirs, exclude_patterns):
        if file_count >= max_files:
            logger.warning(f"Reached maximum file limit of {max_files}")
            break
        
        # Check file size
        try:
            file_size_kb = file_path.stat().st_size / 1024
            if file_size_kb > max_size_kb:
                logger.info(f"Skipping large file: {file_path} ({file_size_kb:.2f}KB)")
                continue
            
            # Read file content
            content, encoding = read_file_with_fallback(file_path)
            
            # Format content
            formatted_content = format_file_content(file_path, content)
            
            # Add to dictionary
            relative_path = file_path.relative_to(directory).as_posix()
            file_contents[relative_path] = formatted_content
            file_count += 1
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
    
    return file_contents


# ====================================================
# Function: get_formatted_file_contents
# This function gets all the file contents from a directory
# and combines them into a single string, with each file's content
# clearly marked with its path.
# ====================================================

def get_formatted_file_contents(directory: Path) -> str:
    """
    Get all file contents formatted with file paths in a single string.
    
    Args:
        directory: Directory to search
        
    Returns:
        str: All formatted file contents concatenated
    """
    file_contents = get_file_contents(directory)
    return "\n\n".join(file_contents.values())


# ====================================================
# Function: get_filtered_formatted_contents
# This function gets the formatted contents of only specific files
# listed in 'files_to_include'. It's useful for when you only want
# to process certain files and not the entire directory.
# ====================================================

def get_filtered_formatted_contents(directory: Path, files_to_include: List[str]) -> str:
    """
    Get formatted contents for only the specified files.
    
    Args:
        directory: Base directory
        files_to_include: List of file paths to include
        
    Returns:
        str: Formatted contents of the specified files
    """
    all_contents = get_file_contents(directory)
    filtered_contents = []
    
    for file_path in files_to_include:
        if file_path in all_contents:
            filtered_contents.append(all_contents[file_path])
        else:
            # Try to find the file with a fuzzy match
            for path in all_contents:
                if file_path in path or path.endswith(file_path):
                    filtered_contents.append(all_contents[path])
                    break
    
    return "\n\n".join(filtered_contents)
