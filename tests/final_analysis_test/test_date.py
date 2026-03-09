"""
tests/final_analysis/test_temporal_framework.py

This script tests dynamic insertion of the current year into the final analysis prompt.
"""

import calendar
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agentrules.config.prompts.final_analysis_prompt import format_final_analysis_prompt


def test_temporal_framework():
    """Test that only the current year is inserted into the temporal framework examples."""
    current_year = datetime.now().year

    consolidated_report = {
        "test": "This is a test report"
    }

    prompt = format_final_analysis_prompt(consolidated_report)

    expected_format = f"It is {current_year} and [temporal context]"
    expected_example = (
        f"It is {current_year} and you are developing with the brand new {current_year}"
    )

    assert expected_format in prompt
    assert expected_example in prompt

    for month_name in calendar.month_name[1:]:
        assert f"It is {month_name} {current_year} and [temporal context]" not in prompt
        assert (
            f"It is {month_name} {current_year} and you are developing with the brand new {current_year}"
            not in prompt
        )

if __name__ == "__main__":
    test_temporal_framework()
