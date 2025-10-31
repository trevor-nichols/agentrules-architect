#!/usr/bin/env python3
"""
tests/phase_1_test/run_test.py

This script tests Phase 1 (Initial Discovery) functionality by running it on the test input
and saving the output to the specified directory.
"""

import sys
import os
import json
import asyncio
from pathlib import Path

# Add the project root to the Python path to allow importing from the project
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.analysis.phase_1 import Phase1Analysis
from core.utils.file_system.tree_generator import get_project_tree
from tests.utils.offline_stubs import patch_factory_offline

async def run_phase1_test():
    """
    Run Phase 1 analysis on the test input and save the results to the output directory.
    """
    # Path to the test input directory
    test_input_dir = Path(__file__).parent.parent / "tests_input"
    
    # Path to the output directory
    output_dir = Path(__file__).parent / "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate project tree
    print(f"Generating project tree for: {test_input_dir}")
    tree = get_project_tree(test_input_dir)
    
    # Remove delimiters for analysis if they exist
    if len(tree) >= 2 and tree[0] == "<project_structure>" and tree[-1] == "</project_structure>":
        tree = tree[1:-1]
    
    # Package info (simplified for test)
    package_info = {"dependencies": {"flask": "latest"}}
    
    # Initialize Phase 1
    print("Initializing Phase 1 Analysis...")
    # Patch factory to avoid real API calls
    patch_factory_offline()
    phase1 = Phase1Analysis()
    
    # Run Phase 1 analysis
    print("Running Phase 1 Analysis...")
    results = await phase1.run(tree, package_info)
    
    # Save the results
    output_file = output_dir / "phase1_results.json"
    print(f"Saving results to: {output_file}")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print("Phase 1 test completed successfully!")
    return results

if __name__ == "__main__":
    results = asyncio.run(run_phase1_test())
    print("\nPhase 1 Results Summary:")
    print(f"Number of findings: {len(results.get('findings', []))}")
