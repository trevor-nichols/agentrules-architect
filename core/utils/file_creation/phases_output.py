"""
utils/file_creation/phases_output.py

This module provides functionality for saving the outputs of analysis phases
to separate files. It handles the creation of output directories and formatting
of the output files.

This module is used by the main analysis process to save results in a structured way.
"""

# ====================================================
# Importing Necessary Libraries
# This section imports external libraries that are used in the code.
# These libraries add extra functionalities that Python doesn't have by default.
# ====================================================

import json  # Used for working with JSON data
import os  # Used for creating directories
from pathlib import Path  # Used for interacting with file paths in a more object-oriented way
from typing import Any  # Used for type hinting, which makes the code easier to understand

from core.utils.constants import FINAL_RULES_FILENAME

# ====================================================
# Function to Save Phase Outputs
# This is the main function that takes the analysis results and saves them into separate files.
# ====================================================

def save_phase_outputs(directory: Path, analysis_data: dict) -> None:
    """
    Save the outputs of each phase to separate markdown files.

    Args:
        directory: Path to the project directory
        analysis_data: Dictionary containing the results from all phases
    """
    # Import the MODEL_CONFIG to get model information for each phase
    from config.agents import MODEL_CONFIG
    from core.utils.model_config_helper import get_model_config_name

    # Get model configuration names
    phase1_model = get_model_config_name(MODEL_CONFIG['phase1'])
    phase2_model = get_model_config_name(MODEL_CONFIG['phase2'])
    phase3_model = get_model_config_name(MODEL_CONFIG['phase3'])
    phase4_model = get_model_config_name(MODEL_CONFIG['phase4'])
    phase5_model = get_model_config_name(MODEL_CONFIG['phase5'])
    final_model = get_model_config_name(MODEL_CONFIG['final'])

    # Create the phases_output directory if it doesn't exist
    output_dir = directory / "phases_output"
    os.makedirs(output_dir, exist_ok=True)

    # Helper function to ensure values are strings
    def ensure_string(value: Any) -> str:
        """
        Ensure that the value is a string.

        Args:
            value: The value to convert to a string

        Returns:
            String representation of the value
        """
        if isinstance(value, str):
            return value
        elif isinstance(value, dict) or isinstance(value, list):
            return json.dumps(value, indent=2)
        else:
            return str(value)

    # Phase 1: Initial Discovery
    with open(output_dir / "phase1_discovery.md", "w", encoding="utf-8") as f:
        f.write(f"# Phase 1: Initial Discovery (Config: {phase1_model})\n\n")
        f.write("## Agent Findings\n\n")
        f.write("```json\n")
        f.write(json.dumps(analysis_data["phase1"], indent=2))  # Write the Phase 1 results as JSON
        f.write("\n```\n")

    # Phase 2: Methodical Planning
    with open(output_dir / "phase2_planning.md", "w", encoding="utf-8") as f:
        f.write(f"# Phase 2: Methodical Planning (Config: {phase2_model})\n\n")
        plan_data = analysis_data["phase2"].get("plan", "Error in planning phase")
        f.write(ensure_string(plan_data))  # Ensure we're writing a string

    # Phase 3: Deep Analysis
    with open(output_dir / "phase3_analysis.md", "w", encoding="utf-8") as f:
        f.write(f"# Phase 3: Deep Analysis (Config: {phase3_model})\n\n")
        f.write("```json\n")
        f.write(json.dumps(analysis_data["phase3"], indent=2))  # Write the Phase 3 results as JSON
        f.write("\n```\n")

    # Phase 4: Synthesis
    with open(output_dir / "phase4_synthesis.md", "w", encoding="utf-8") as f:
        f.write(f"# Phase 4: Synthesis (Config: {phase4_model})\n\n")
        analysis_data_phase4 = analysis_data["phase4"].get("analysis", "Error in synthesis phase")
        f.write(ensure_string(analysis_data_phase4))  # Ensure we're writing a string

    # Phase 5: Consolidation
    with open(output_dir / "phase5_consolidation.md", "w", encoding="utf-8") as f:
        f.write(f"# Phase 5: Consolidation (Config: {phase5_model})\n\n")
        report_data = analysis_data["consolidated_report"].get("report", "Error in consolidation phase")
        f.write(ensure_string(report_data))  # Ensure we're writing a string

    # Final Analysis - Save to both markdown file and AGENTS.md guidance file
    final_analysis_data = analysis_data["final_analysis"].get("analysis", "Error in final analysis phase")

    # Save to markdown file in phases_output directory
    with open(output_dir / "final_analysis.md", "w", encoding="utf-8") as f:
        f.write(f"# Final Analysis (Config: {final_model})\n\n")
        f.write(ensure_string(final_analysis_data))  # Ensure we're writing a string

    # Save to AGENTS.md file in project root directory with project tree
    # Define directories to exclude from the tree
    exclude_dirs = ["phases_output", "__pycache__", ".git", ".vscode", ".cursor"]

    # Get the project tree without the excluded directories
    from core.utils.file_system.tree_generator import (
        DEFAULT_EXCLUDE_DIRS,
        DEFAULT_EXCLUDE_PATTERNS,
        generate_tree,
    )

    # Create a custom set of exclude directories by combining defaults with our additions
    custom_exclude_dirs = DEFAULT_EXCLUDE_DIRS.union(set(exclude_dirs))

    # Generate a tree with our custom exclusions
    tree = generate_tree(
        directory,
        exclude_dirs=custom_exclude_dirs,
        exclude_patterns=DEFAULT_EXCLUDE_PATTERNS
    )

    # Add delimiters and format for inclusion in the AGENTS.md file
    tree_section = [
        "\n<project_structure>",
    ]
    tree_section.extend(tree)
    tree_section.append("</project_structure>")

    # Write final analysis and tree to AGENTS.md file
    with open(directory / FINAL_RULES_FILENAME, "w", encoding="utf-8") as f:
        f.write(ensure_string(final_analysis_data))  # Save the final analysis
        f.write("\n\n")  # Add spacing
        f.write("# Project Directory Structure\n")  # Section header
        f.write("---\n\n")  # Section divider
        f.write('\n'.join(tree_section))  # Append the tree structure

    # ====================================================
    # Create metrics file
    # This section creates a metrics file that summarizes key information
    # from the entire analysis, including metrics like total time and token usage.
    # ====================================================
    with open(output_dir / "metrics.md", "w", encoding="utf-8") as f:
        f.write("# CursorRules Architect Metrics\n\n")
        f.write(f"Project: {directory}\n")
        f.write("=" * 50 + "\n\n")
        f.write("## Analysis Metrics\n\n")
        f.write(f"- Time taken: {analysis_data['metrics']['time']:.2f} seconds\n")  # Write the total time

        f.write("\n## Model Configurations Used\n\n")
        f.write(f"- Phase 1: Initial Discovery - {phase1_model}\n")
        f.write(f"- Phase 2: Methodical Planning - {phase2_model}\n")
        f.write(f"- Phase 3: Deep Analysis - {phase3_model}\n")
        f.write(f"- Phase 4: Synthesis - {phase4_model}\n")
        f.write(f"- Phase 5: Consolidation - {phase5_model}\n")
        f.write(f"- Final Analysis - {final_model}\n")

        f.write("\n## Generated Files\n\n")
        f.write(f"- `{FINAL_RULES_FILENAME}` - Contains the final analysis for Cursor IDE\n")
        f.write("- `.cursorignore` - Contains patterns of files to ignore in Cursor IDE\n")
        f.write(f"- `phase1_discovery.md` - Results from Initial Discovery (Config: {phase1_model})\n")
        f.write(f"- `phase2_planning.md` - Results from Methodical Planning (Config: {phase2_model})\n")
        f.write(f"- `phase3_analysis.md` - Results from Deep Analysis (Config: {phase3_model})\n")
        f.write(f"- `phase4_synthesis.md` - Results from Synthesis (Config: {phase4_model})\n")
        f.write(f"- `phase5_consolidation.md` - Results from Consolidation (Config: {phase5_model})\n")
        f.write(f"- `final_analysis.md` - Copy of the final analysis (Config: {final_model})\n\n")
        f.write("See individual phase files for detailed outputs.")
