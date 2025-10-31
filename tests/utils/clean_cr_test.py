#!/usr/bin/env python3
"""
tests/utils/clean_cr_test.py

Simple smoke test for the rules file cleanup utility.
"""

import os
import shutil
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.utils.constants import FINAL_RULES_FILENAME
from core.utils.formatters.clean_cursorrules import clean_cursorrules_file

# Setup test paths
# NOTE: keep this simple path logic aligned with the actual fixture file name.
input_file = Path(f"tests/tests_input/{FINAL_RULES_FILENAME}")
output_dir = Path("tests/utils/outputs")
output_file = output_dir / FINAL_RULES_FILENAME

# Create output directory if it doesn't exist
output_dir.mkdir(exist_ok=True, parents=True)

# Copy test file to output directory
if input_file.exists():
    shutil.copy(str(input_file), str(output_file))
    print(f"Copied test file from {input_file} to {output_file}")
else:
    print(f"Error: Test input file not found at {input_file}")
    exit(1)

# Run the clean function
success, message = clean_cursorrules_file(str(output_file))

# Check results
if success:
    print(f"Success: {message}")

    # Verify file now starts with "You are"
    with open(output_file, encoding='utf-8') as f:
        content = f.read()

    if content.strip().startswith("You are"):
        print("Verification passed: File now starts with 'You are'")
    else:
        print("Verification failed: File does not start with 'You are'")
        print(f"File starts with: {content[:50]}...")
else:
    print(f"Failed: {message}")
