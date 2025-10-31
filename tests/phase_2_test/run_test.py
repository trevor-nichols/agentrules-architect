#!/usr/bin/env python3
"""
tests/phase_2/run_test.py

This script tests Phase 2 (Methodical Planning) functionality by using the Phase 1 
output as input and generating a detailed analysis plan.
"""

import sys
import os
import json
import asyncio
from pathlib import Path

# Add the project root to the Python path to allow importing from the project
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.analysis.phase_2 import Phase2Analysis
from core.utils.file_system.tree_generator import get_project_tree
from tests.utils.offline_stubs import patch_factory_offline

async def run_phase2_test():
    """
    Run Phase 2 analysis using the Phase 1 results and generate an analysis plan.
    """
    # Path to the test input directory
    test_input_dir = Path(__file__).parent.parent / "tests_input"
    
    # Path to the output directory
    output_dir = Path(__file__).parent / "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load Phase 1 results from the test input
    phase1_file = Path(__file__).parent / "test2_input.json"
    with open(phase1_file, "r") as f:
        phase1_results = json.load(f)
    
    # Generate project tree
    print(f"Generating project tree for: {test_input_dir}")
    tree = get_project_tree(test_input_dir)
    
    # Remove delimiters for analysis if they exist
    if len(tree) >= 2 and tree[0] == "<project_structure>" and tree[-1] == "</project_structure>":
        tree = tree[1:-1]
    
    # Initialize Phase 2 Analysis
    print("Initializing Phase 2 Analysis...")
    patch_factory_offline()
    phase2 = Phase2Analysis()  # Uses the model specified in agents.py
    
    # Run Phase 2 analysis
    print("Running Phase 2 Analysis...")
    results = await phase2.run(phase1_results, tree)
    
    # Add diagnostic output
    print(f"Raw results keys: {list(results.keys())}")
    print(f"Agents found: {len(results.get('agents', []))}")
    if 'agents' in results:
        for i, agent in enumerate(results['agents']):
            print(f"  Agent {i+1}: {agent.get('name', 'Unknown')} with {len(agent.get('file_assignments', []))} files")
    
    # Save the complete results
    output_file = output_dir / "phase2_results.json"
    print(f"Saving complete results to: {output_file}")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    # Save just the analysis plan text
    plan_file = output_dir / "analysis_plan.xml"
    print(f"Saving analysis plan to: {plan_file}")
    with open(plan_file, "w") as f:
        f.write(results.get("plan", ""))
    
    print("Phase 2 test completed successfully!")
    return results

if __name__ == "__main__":
    results = asyncio.run(run_phase2_test())
    print("\nPhase 2 Results Summary:")
    print(f"Analysis plan created with {len(results.get('agents', []))} agents")
