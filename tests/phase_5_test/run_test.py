#!/usr/bin/env python3
"""
tests/phase_5_test/run_test.py

This script tests Phase 5 (Consolidation) functionality by using the Phase 4 
output as input and generating a consolidated report.
"""

import sys
import os
import json
import asyncio
from pathlib import Path

# Add the project root to the Python path to allow importing from the project
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.analysis.phase_5 import Phase5Analysis
from tests.utils.offline_stubs import patch_factory_offline

async def run_phase5_test():
    """
    Run Phase 5 analysis using the Phase 4 results and generate a consolidated report.
    """
    # Path to the output directory
    output_dir = Path(__file__).parent / "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load Phase 4 results from the test input
    phase4_file = Path(__file__).parent / "test5_input.json"
    with open(phase4_file, "r") as f:
        phase4_results = json.load(f)
    
    # Create all_results dict (simulate the structure from main.py)
    all_results = {
        "phase1": {},  # Empty placeholders for earlier phases
        "phase2": {},
        "phase3": {},
        "phase4": {
            "analysis": phase4_results.get("synthesis", ""),
            "reasoning": phase4_results.get("reasoning", "")
        }
    }
    
    # Initialize Phase 5 Analysis
    print("Initializing Phase 5 Analysis...")
    patch_factory_offline()
    phase5 = Phase5Analysis()
    
    # Run Phase 5 analysis
    print("Running Phase 5 Analysis...")
    results = await phase5.run(all_results)
    
    # Save the complete results
    output_file = output_dir / "phase5_results.json"
    print(f"Saving results to: {output_file}")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    # Also save just the consolidated report if available
    if "report" in results:
        report_file = output_dir / "consolidated_report.md"
        print(f"Saving consolidated report to: {report_file}")
        with open(report_file, "w") as f:
            f.write(results["report"])
    
    print("Phase 5 test completed successfully!")
    return results

if __name__ == "__main__":
    results = asyncio.run(run_phase5_test())
    print("\nPhase 5 Results Summary:")
    if "report" in results:
        print(f"Consolidated report length: {len(results['report'])} characters")
    else:
        print(f"Response keys: {list(results.keys())}")
