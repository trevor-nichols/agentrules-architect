# core/analysis/phase_4.py
"""
This module provides functionality for Phase 4 (Synthesis) of the project analysis.
It defines the methods needed for synthesizing the findings from Phase 3.
"""

# ====================================================
# Import Statements
# This section imports necessary modules and functions for the script.
# ====================================================

import logging  # Used for logging messages
from typing import Dict  # Used for type hinting, making code more readable
from config.prompts.phase_4_prompts import PHASE_4_PROMPT, format_phase4_prompt  # Prompts for Phase 4
from core.agents import get_architect_for_phase  # Added import for dynamic model configuration

# ====================================================
# Logger Initialization
# Get the logger for this module.
# ====================================================

# Get logger
logger = logging.getLogger("project_extractor")

# ====================================================
# Phase 4 Analysis Class
# This class handles the Phase 4 (Synthesis) of the project analysis.
# ====================================================

class Phase4Analysis:
    """
    Class responsible for Phase 4 (Synthesis) of the project analysis.
    
    This phase uses a model configured in config/agents.py to synthesize the findings from Phase 3,
    providing a deeper analysis and updated directions.
    """
    
    # ====================================================
    # Initialization Method
    # Sets up the Phase 4 analysis with the OpenAI agent.
    # ====================================================
    def __init__(self):
        """
        Initialize the Phase 4 analysis with the architect from configuration.
        """
        # Use the factory function to get the appropriate architect based on configuration
        self.architect = get_architect_for_phase("phase4")

    # ====================================================
    # Run Method
    # Executes the Synthesis Phase using the configured model.
    # ====================================================
    async def run(self, phase3_results: Dict) -> Dict:
        """
        Run the Synthesis Phase using the configured model.
        
        Args:
            phase3_results: Dictionary containing the results from Phase 3
            
        Returns:
            Dictionary containing the synthesis and token usage
        """
        try:
            # Format the prompt using the template from the prompts file
            prompt = format_phase4_prompt(phase3_results)
            
            logger.info("[bold]Phase 4:[/bold] Synthesizing findings from all analysis agents")
            
            # Use the architect to synthesize findings from Phase 3
            result = await self.architect.synthesize_findings(phase3_results, prompt)
            
            logger.info("[bold green]Phase 4:[/bold green] Synthesis completed successfully")
            
            return result
        except Exception as e:
            logger.error(f"[bold red]Error in Phase 4:[/bold red] {str(e)}")
            return {"error": str(e)}
