"""
config/tools.py

This module defines the tool configurations used by different AI models in the analysis phases.
It provides standardized tool definitions that work across different model providers
and configures which tools are available in each phase.
"""

from core.agent_tools.web_search import TAVILY_SEARCH_TOOL_SCHEMA
from core.types.tool_config import Tool, ToolSets

# ====================================================
# Phase-specific Tool Sets
# Define which tools are available for each phase.
# ====================================================

TOOL_SETS: ToolSets = {
    "RESEARCHER_TOOLS": [TAVILY_SEARCH_TOOL_SCHEMA],
    "PHASE_1_TOOLS": [],
    "PHASE_2_TOOLS": [],
    "PHASE_3_TOOLS": [],
    "PHASE_4_TOOLS": [],
    "PHASE_5_TOOLS": [],
    "FINAL_TOOLS": [],
}

# ====================================================
# Tool-enabled Model Variants
# Helper function to enable tools on a model configuration.
# ====================================================

def with_tools_enabled(model_config):
    """
    Create a copy of a model config with tools enabled.
    
    Args:
        model_config: The original model configuration
        
    Returns:
        A new ModelConfig with tools enabled
    """
    return model_config._replace(
        tools_config={"enabled": True, "tools": None}
    )
