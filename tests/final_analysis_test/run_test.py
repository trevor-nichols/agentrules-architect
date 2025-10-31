#!/usr/bin/env python3
"""
tests/final_analysis_test/run_test.py

This script tests the Final Analysis functionality by using the Phase 5 
output as input and generating final cursor rules.
"""

import sys
import os
import json
import asyncio
from pathlib import Path

# Add the project root to the Python path to allow importing from the project
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.analysis.final_analysis import FinalAnalysis
from core.utils.file_system.tree_generator import get_project_tree
from tests.utils.offline_stubs import patch_factory_offline

async def run_final_analysis_test():
    """
    Run Final Analysis using the Phase 5 results and generate cursor rules.
    """
    # Path to the output directory
    output_dir = Path(__file__).parent / "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Path to the test input directory (for generating a sample project tree)
    test_input_dir = Path(__file__).parent.parent / "tests_input"
    
    # Load Phase 5 results from the test input
    phase5_file = Path(__file__).parent / "fa_test_input.json"
    with open(phase5_file, "r") as f:
        phase5_results = json.load(f)
    
    # Generate a sample project tree
    print(f"Generating project tree for: {test_input_dir}")
    tree = get_project_tree(test_input_dir)
    
    # Remove delimiters for analysis if they exist
    if len(tree) >= 2 and tree[0] == "<project_structure>" and tree[-1] == "</project_structure>":
        tree = tree[1:-1]
    
    # Initialize Final Analysis
    print("Initializing Final Analysis...")
    patch_factory_offline()
    final_analysis = FinalAnalysis()
    
    # Run Final Analysis
    print("Running Final Analysis...")
    results = await final_analysis.run(phase5_results, tree)
    
    # Save the complete results
    output_file = output_dir / "final_analysis_results.json"
    print(f"Saving results to: {output_file}")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    # Also save just the analysis text if available
    if "analysis" in results:
        rules_file = output_dir / "cursor_rules.md"
        print(f"Saving cursor rules to: {rules_file}")
        with open(rules_file, "w") as f:
            f.write(results["analysis"])
    
    print("Final Analysis test completed successfully!")
    return results

if __name__ == "__main__":
    results = asyncio.run(run_final_analysis_test())
    print("\nFinal Analysis Results Summary:")
    if "analysis" in results:
        print(f"Cursor rules length: {len(results['analysis'])} characters")
    else:
        print(f"Response keys: {list(results.keys())}")
