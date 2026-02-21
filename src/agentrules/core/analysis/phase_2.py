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
from collections.abc import Sequence

from agentrules.config.prompts.phase_2_prompts import (  # Prompts for Phase 2
    format_phase2_prompt,
)
from agentrules.core.agents import get_architect_for_phase  # Added import for dynamic model configuration
from agentrules.core.analysis.events import AnalysisEvent, AnalysisEventSink, NullEventSink
from agentrules.core.utils.parsers.agent_parser import (  # Function to parse agent definitions
    extract_agent_fallback,
    parse_agents_from_phase2,
)

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
    def __init__(self, events: AnalysisEventSink | None = None):
        """
        Initialize the Phase 2 analysis with the architect from configuration.
        """
        # Use the factory function to get the appropriate architect based on configuration
        self.architect = get_architect_for_phase("phase2")
        self._events: AnalysisEventSink = events or NullEventSink()

    def set_event_sink(self, events: AnalysisEventSink | None) -> None:
        """Update the event sink after construction."""

        self._events = events or NullEventSink()

    # ====================================================
    # Run Method
    # Executes the methodical planning phase.
    # ====================================================
    async def run(self, phase1_results: dict, tree: Sequence[str] | None = None) -> dict:
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

            # Prefer structured fields on the full response payload; parser falls
            # back to plan text/XML recovery when structured agents are absent.
            logger.info("[bold]Phase 2:[/bold] Parsing agent definitions from plan")
            agents = parse_agents_from_phase2(analysis_plan_response)

            if agents:
                logger.info(f"[bold green]Success:[/bold green] Found {len(agents)} agents in the analysis plan")
                for i, agent in enumerate(agents):
                    files_count = len(agent.get('file_assignments', []))
                    logger.info(
                        "  [bold cyan]Agent %d:[/bold cyan] %s with %d files",
                        i + 1,
                        agent.get("name", "Unknown"),
                        files_count,
                    )
                self._publish_agent_plan(phase="phase2", agents=agents)
            # If no agents found, try the fallback approach directly
            else:
                logger.info(
                    "[bold yellow]Warning:[/bold yellow] No agents found from standard parsing, "
                    "trying fallback",
                )
                try:
                    fallback_agents = extract_agent_fallback(plan_text)
                    if fallback_agents:
                        logger.info(f"[bold green]Success:[/bold green] Fallback found {len(fallback_agents)} agents")
                        agents = fallback_agents
                        self._publish_agent_plan(phase="phase2", agents=agents)
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

    def _publish_agent_plan(self, *, phase: str, agents: Sequence[dict]) -> None:
        """Emit a structured event describing the parsed agent plan."""

        summaries = []
        for idx, agent in enumerate(agents, start=1):
            agent_id = agent.get("id") or f"agent_{idx}"
            summaries.append(
                {
                    "id": agent_id,
                    "name": agent.get("name") or agent_id,
                    "description": agent.get("description"),
                    "files": list(agent.get("file_assignments", []) or []),
                }
            )

        event = AnalysisEvent(phase=phase, type="agent_plan", payload={"agents": summaries})
        self._events.publish(event)
