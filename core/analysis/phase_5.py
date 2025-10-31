# core/analysis/phase_5.py
# =============================================================================
# Phase 5: Consolidation
# This file contains the code for Phase 5 of the project analysis, which
# consolidates the results from all previous phases into a single report.
# =============================================================================

# =============================================================================
# Import Statements
# These lines import necessary modules and functions for this phase.
# - json: For handling JSON data.
# - logging: For logging events and errors.
# - Dict: For type hinting dictionaries.
# - Anthropic: The Anthropic API client.
# - PHASE_5_PROMPT, format_phase5_prompt: Specific prompt and formatting
#   function for Phase 5 from the config.prompts module.
# =============================================================================
import json
import logging
from typing import Dict
from config.prompts.phase_5_prompts import PHASE_5_PROMPT, format_phase5_prompt
from core.agents import get_architect_for_phase

# =============================================================================
# Initialize the Anthropic Client and Logger
# This section initializes the Anthropic client for API calls and sets up
# logging to track the process.
# =============================================================================
logger = logging.getLogger("project_extractor")

# =============================================================================
# Phase 5 Analysis Class
# This class handles the consolidation of results from all previous phases.
# =============================================================================
class Phase5Analysis:
    """
    Class responsible for Phase 5 (Consolidation) of the project analysis.
    
    This phase uses a model configured in config/agents.py to consolidate 
    the results from all previous phases into a comprehensive final report.
    """
    
    # =========================================================================
    # Initialization Method
    # Sets up the Phase 5 analysis with the model from configuration.
    # =========================================================================
    def __init__(self):
        """
        Initialize the Phase 5 analysis with the architect from configuration.
        """
        # Use the factory function to get the appropriate architect based on configuration
        self.architect = get_architect_for_phase("phase5")
    
    # =========================================================================
    # Run Method
    # Executes the consolidation phase using the configured model.
    # =========================================================================
    async def run(self, all_results: Dict) -> Dict:
        """
        Run the Consolidation Phase using the configured model.
        
        Args:
            all_results: Dictionary containing the results from all previous phases
            
        Returns:
            Dictionary containing the consolidated report
        """
        try:
            # Format the prompt using the template from the prompts file
            prompt = format_phase5_prompt(all_results)
            
            logger.info("[bold]Phase 5:[/bold] Consolidating results from all previous phases")
            
            # Use the architect to consolidate results
            result = await self.architect.consolidate_results(all_results, prompt)
            
            logger.info("[bold green]Phase 5:[/bold green] Consolidation completed successfully")
            
            # Return the result, ensuring it has the expected format
            if "report" not in result and "error" not in result:
                if "phase" in result and isinstance(result.get("phase"), str):
                    return result  # Already in the expected format
                else:
                    # Extract findings if available
                    findings = result.get("findings", "No consolidated report generated")
                    return {
                        "phase": "Consolidation",
                        "report": findings if isinstance(findings, str) else json.dumps(findings)
                    }
            return result
        except Exception as e:
            logger.error(f"[bold red]Error in Phase 5:[/bold red] {str(e)}")
            return {
                "phase": "Consolidation",
                "error": str(e)
            }
