# core/analysis/phase_2.py
"""
This module provides functionality for Phase 2 (Methodical Planning) of the project analysis.
It defines the methods needed for creating a detailed analysis plan based on Phase 1 results.
"""

# ====================================================
# Import Statements
# This section imports necessary modules and functions for the script.
# ====================================================

import logging  # Used for logging messages
from typing import Dict, List  # Used for type hinting, making code more readable
from config.prompts.phase_2_prompts import PHASE_2_PROMPT, format_phase2_prompt  # Prompts for Phase 2
from core.utils.parsers.agent_parser import parse_agents_from_phase2, extract_agent_fallback  # Function to parse agent definitions
from core.agents import get_architect_for_phase  # Added import for dynamic model configuration

# ====================================================
# Logger Initialization
# Get the logger for this module.
# ====================================================
logger = logging.getLogger("project_extractor")

# ====================================================
# Phase 2 Analysis Class
# This class handles the methodical planning phase.
# ====================================================

class Phase2Analysis:
    """
    Class responsible for Phase 2 (Methodical Planning) of the project analysis.
    
    This phase uses a model configured in config/agents.py to create a detailed 
    analysis plan based on the findings from Phase 1.
    """
    
    # ====================================================
    # Initialization
    # Sets up the Phase 2 analysis.
    # ====================================================
    def __init__(self):
        """
        Initialize the Phase 2 analysis with the architect from configuration.
        """
        # Use the factory function to get the appropriate architect based on configuration
        self.architect = get_architect_for_phase("phase2")
    
    # ====================================================
    # Run Method
    # Executes the methodical planning phase.
    # ====================================================
    async def run(self, phase1_results: Dict, tree: List[str] = None) -> Dict:
        """
        Run the Methodical Planning Phase using the configured model.
        
        Args:
            phase1_results: Dictionary containing the results from Phase 1
            tree: List of strings representing the project directory tree
            
        Returns:
            Dictionary containing the analysis plan and token usage
        """
        try:
            # ====================================================
            # Prompt Formatting
            # Format the prompt using the template.
            # ====================================================
            prompt = format_phase2_prompt(phase1_results, tree)
            
            logger.info("[bold]Phase 2:[/bold] Creating analysis plan using configured model")
            
            # ====================================================
            # Analysis Plan Creation
            # Use the architect to create an analysis plan.
            # ====================================================
            analysis_plan_response = await self.architect.create_analysis_plan(phase1_results, prompt)
            
            # ====================================================
            # Error Handling
            # Check for errors and return if any.
            # ====================================================
            if "error" in analysis_plan_response and analysis_plan_response["error"]:
                logger.error(f"[bold red]Error:[/bold red] {analysis_plan_response['error']}")
                return analysis_plan_response
            
            # ====================================================
            # Plan Extraction and Agent Parsing
            # Get the plan and parse agent definitions.
            # ====================================================
            plan_text = analysis_plan_response.get("plan", "")  # Extract the raw plan text
            
            # Try parsing agents from the plan text
            logger.info("[bold]Phase 2:[/bold] Parsing agent definitions from plan")
            agents = parse_agents_from_phase2(plan_text)  # Parse the agent definitions from plan text
            
            if agents:
                logger.info(f"[bold green]Success:[/bold green] Found {len(agents)} agents in the analysis plan")
                for i, agent in enumerate(agents):
                    files_count = len(agent.get('file_assignments', []))
                    logger.info(f"  [bold cyan]Agent {i+1}:[/bold cyan] {agent.get('name', 'Unknown')} with {files_count} files")
            # If no agents found, try the fallback approach directly
            else:
                logger.info("[bold yellow]Warning:[/bold yellow] No agents found from standard parsing, trying fallback")
                try:
                    fallback_agents = extract_agent_fallback(plan_text)
                    if fallback_agents:
                        logger.info(f"[bold green]Success:[/bold green] Fallback found {len(fallback_agents)} agents")
                        agents = fallback_agents
                    else:
                        logger.warning("[bold yellow]Warning:[/bold yellow] Fallback parsing couldn't find any agents")
                except Exception as e:
                    logger.error(f"[bold red]Error:[/bold red] Fallback parsing failed: {str(e)}")
            
            # Add the agents to the response dictionary
            analysis_plan_response["agents"] = agents
            
            return analysis_plan_response
        except Exception as e:
            logger.error(f"[bold red]Error:[/bold red] in Phase 2: {str(e)}")
            return {"error": str(e)}
