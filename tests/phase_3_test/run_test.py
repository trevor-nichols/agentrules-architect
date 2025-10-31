#!/usr/bin/env python3
"""
tests/phase_3_test/run_test.py

This script tests Phase 3 (Deep Analysis) functionality by using the Phase 2 output
as input and running deep analysis on the test codebase files.
"""

import sys
import os
import json
import asyncio
from pathlib import Path

# Add the project root to the Python path to allow importing from the project
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.analysis.phase_3 import Phase3Analysis
from core.utils.file_system.tree_generator import get_project_tree
from tests.utils.offline_stubs import patch_factory_offline

async def run_phase3_test():
    """
    Run Phase 3 analysis using the Phase 2 results on the test input files.
    """
    # Path to the test input directory
    test_input_dir = Path(__file__).parent.parent / "tests_input"
    
    # Path to the output directory
    output_dir = Path(__file__).parent / "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load Phase 2 results from the test input JSON
    phase2_file = Path(__file__).parent / "test3_input.json"
    with open(phase2_file, "r") as f:
        phase2_results = json.load(f)
    
    # Generate project tree
    print(f"Generating project tree for: {test_input_dir}")
    tree = get_project_tree(test_input_dir)
    
    # Remove delimiters for analysis if they exist
    if len(tree) >= 2 and tree[0] == "<project_structure>" and tree[-1] == "</project_structure>":
        tree = tree[1:-1]
    
    # Initialize Phase 3 Analysis
    print("Initializing Phase 3 Analysis...")
    patch_factory_offline()
    phase3 = Phase3Analysis()
    
    # Run Phase 3 analysis
    print("Running Phase 3 Analysis...")
    results = await phase3.run(phase2_results, tree, test_input_dir)
    
    # Save the complete results
    output_file = output_dir / "phase3_results.json"
    print(f"Saving results to: {output_file}")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print("Phase 3 test completed successfully!")
    return results

if __name__ == "__main__":
    results = asyncio.run(run_phase3_test())
    print("\nPhase 3 Results Summary:")
    print(f"Number of agents: {len(results.get('findings', []))}")
