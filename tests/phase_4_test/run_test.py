#!/usr/bin/env python3
"""
tests/phase_4_test/run_test.py

This script tests Phase 4 (Synthesis) functionality by using the Phase 3 
output as input and generating a synthesis of the findings.
"""

import sys
import os
import json
import asyncio
from pathlib import Path

# Add the project root to the Python path to allow importing from the project
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.analysis.phase_4 import Phase4Analysis
from tests.utils.offline_stubs import patch_factory_offline

async def run_phase4_test():
    """
    Run Phase 4 analysis using the Phase 3 results and generate a synthesis.
    """
    # Path to the output directory
    output_dir = Path(__file__).parent / "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load Phase 3 results from the test input
    phase3_file = Path(__file__).parent / "test4_input.json"
    with open(phase3_file, "r") as f:
        phase3_results = json.load(f)
    
    # Initialize Phase 4 Analysis
    print("Initializing Phase 4 Analysis...")
    patch_factory_offline()
    phase4 = Phase4Analysis()
    
    # Run Phase 4 analysis
    print("Running Phase 4 Analysis...")
    results = await phase4.run(phase3_results)
    
    # Save the complete results
    output_file = output_dir / "phase4_results.json"
    print(f"Saving complete results to: {output_file}")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    # Also save just the analysis text if available
    if "analysis" in results:
        analysis_file = output_dir / "analysis.md"
        print(f"Saving analysis to: {analysis_file}")
        with open(analysis_file, "w") as f:
            f.write(results["analysis"])
    
    print("Phase 4 test completed successfully!")
    return results

if __name__ == "__main__":
    results = asyncio.run(run_phase4_test())
    print("\nPhase 4 Results Summary:")
    if "analysis" in results:
        print(f"Analysis text length: {len(results['analysis'])} characters")
    else:
        print(f"Response keys: {list(results.keys())}")
