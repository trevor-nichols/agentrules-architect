"""
core/analysis/phase_1.py

This module provides functionality for Phase 1 (Initial Discovery) of the project analysis.
It defines the agents and methods needed for the initial exploration of the project.
"""

# ====================================================
# Importing Required Libraries
# This section imports all the necessary libraries and modules needed for this phase.
# ====================================================

import asyncio  # For running asynchronous tasks concurrently.
import json     # For handling JSON data.
from typing import Dict, List, Any  # For type hinting.
from config.prompts.phase_1_prompts import ( # Prompts used for configuring the agents in Phase 1.
    PHASE_1_BASE_PROMPT,
    STRUCTURE_AGENT_PROMPT,
    DEPENDENCY_AGENT_PROMPT,
    TECH_STACK_AGENT_PROMPT,
    RESEARCHER_AGENT_PROMPT,
)
from core.agents.factory.factory import get_architect_for_phase, get_researcher_architect
from config.tools import TOOL_SETS
try:
    from core.agent_tools.web_search.tavily import run_tavily_search as _run_tavily_search
except Exception:
    _run_tavily_search = None
import logging  # For logging information about the execution
from rich import print

# ====================================================
# Phase 1 Analysis Class
# This class handles the initial discovery phase of the project analysis.
# ====================================================

MAX_RESEARCHER_TOOL_ITERATIONS = 3


class Phase1Analysis:
    """
    Class responsible for Phase 1 (Initial Discovery) of the project analysis.
    
    This phase uses Anthropic models to perform initial exploration of the project,
    analyzing directory structure, dependencies, and technology stack.
    """
    
    # ----------------------------------------------------
    # Initialization
    # Sets up the agents required for the initial discovery.
    # ----------------------------------------------------
    def __init__(self):
        """
        Initialize the Phase 1 analysis with the required architects.
        """
        # Use the Architect architecture
        self.initial_architects = [
            get_architect_for_phase(
                "phase1",
                name=STRUCTURE_AGENT_PROMPT["name"],
                role=STRUCTURE_AGENT_PROMPT["role"],
                responsibilities=STRUCTURE_AGENT_PROMPT["responsibilities"],
                prompt_template=PHASE_1_BASE_PROMPT
            ),
            get_architect_for_phase(
                "phase1",
                name=DEPENDENCY_AGENT_PROMPT["name"],
                role=DEPENDENCY_AGENT_PROMPT["role"],
                responsibilities=DEPENDENCY_AGENT_PROMPT["responsibilities"],
                prompt_template=PHASE_1_BASE_PROMPT
            ),
            get_architect_for_phase(
                "phase1",
                name=TECH_STACK_AGENT_PROMPT["name"],
                role=TECH_STACK_AGENT_PROMPT["role"],
                responsibilities=TECH_STACK_AGENT_PROMPT["responsibilities"],
                prompt_template=PHASE_1_BASE_PROMPT
            )
        ]
        
        # Initialize the researcher agent separately
        self.researcher_architect = get_researcher_architect(
            name=RESEARCHER_AGENT_PROMPT["name"],
            role=RESEARCHER_AGENT_PROMPT["role"],
            responsibilities=RESEARCHER_AGENT_PROMPT["responsibilities"],
            prompt_template=PHASE_1_BASE_PROMPT
        )
    
    # ----------------------------------------------------
    # Run Method
    # Executes the Initial Discovery phase.
    # ----------------------------------------------------
    async def run(self, tree: List[str], package_info: Dict) -> Dict:
        """
        Run the Initial Discovery Phase.
        
        Args:
            tree: List of strings representing the project directory tree
            package_info: Dictionary containing information about project dependencies
            
        Returns:
            Dictionary containing the results of the phase
        """
        # Create a context object for the initial analysis.
        initial_context = {
            "tree_structure": tree,
            "package_info": package_info
        }
        
        logging.info("[bold]Phase 1, Part 1:[/bold] Starting initial analysis with 3 agents")
        
        # Run initial architects in parallel
        architect_tasks = [architect.analyze(initial_context) for architect in self.initial_architects]
        initial_results = await asyncio.gather(*architect_tasks)
        
        logging.info("[bold green]Phase 1, Part 1:[/bold green] All initial agents have completed their analysis")

        # Part 2: Run the researcher agent
        logging.info("[bold]Phase 1, Part 2:[/bold] Starting documentation research")

        # Combine dependency and tech stack findings for the researcher
        # The Dependency agent is the second one (index 1), Tech Stack is the third (index 2)
        dependency_findings = initial_results[1] 
        tech_stack_findings = initial_results[2]

        research_context = {
            "dependencies": dependency_findings,
            "tech_stack": tech_stack_findings
        }
        
        # Provide web-search tool to the researcher
        researcher_tools = TOOL_SETS.get("RESEARCHER_TOOLS", [])
        research_findings = await self._run_researcher_with_tools(
            research_context,
            researcher_tools
        )
        
        logging.info("[bold green]Phase 1, Part 2:[/bold green] Documentation research complete")
        
        # Return the combined results.
        return {
            "phase": "Initial Discovery",
            "initial_findings": initial_results,
            "documentation_research": research_findings
        }

    async def _run_researcher_with_tools(
        self,
        research_context: Dict[str, Any],
        researcher_tools: List[Any]
    ) -> Dict[str, Any]:
        """Execute the researcher architect, completing tool loops when required."""

        # Preserve the base context so each iteration starts from shared facts
        base_context = dict(research_context)
        executed_tools: List[Dict[str, Any]] = []
        latest_response: Dict[str, Any] = {}

        context_payload: Dict[str, Any] = dict(base_context)

        for iteration in range(1, MAX_RESEARCHER_TOOL_ITERATIONS + 1):
            latest_response = await self.researcher_architect.analyze(context_payload, tools=researcher_tools)

            # Collect and execute tool requests, if any
            latest_tool_runs: List[Dict[str, Any]] = []
            try:
                latest_tool_runs.extend(
                    await self._handle_anthropic_tool_calls(latest_response.get("tool_calls"))
                )
                latest_tool_runs.extend(
                    await self._handle_gemini_function_calls(latest_response.get("function_calls"))
                )
            except Exception as tool_error:  # Fail fast but keep loop state visible
                latest_tool_runs.append({"error": str(tool_error)})

            if not latest_tool_runs:
                # Ensure we don't surface stale tool call instructions downstream
                latest_response.pop("tool_calls", None)
                latest_response.pop("function_calls", None)
                break

            executed_tools.extend(latest_tool_runs)

            # Prepare follow-up context for the agent; include all prior tool output
            context_payload = dict(base_context)
            context_payload["tool_feedback"] = {
                "executed_tools": executed_tools,
                "latest_results": latest_tool_runs,
                "previous_findings": latest_response.get("findings"),
                "iteration": iteration,
                "instructions": (
                    "You requested external research tools. Incorporate the tool "
                    "results above into your documentation research summary. If "
                    "additional tools are required, request them explicitly; otherwise "
                    "return your written findings."
                )
            }

            if iteration == MAX_RESEARCHER_TOOL_ITERATIONS:
                # Guard against infinite loops: surface diagnostic info to caller
                latest_response.setdefault("error", "maximum researcher tool iterations reached")
                break

        if executed_tools:
            latest_response["executed_tools"] = executed_tools

        return latest_response

    async def _handle_anthropic_tool_calls(self, tool_calls: Any) -> List[Dict[str, Any]]:
        """Execute Anthropic-style tool calls and return structured results."""
        results: List[Dict[str, Any]] = []
        if not tool_calls:
            return results

        for call in tool_calls or []:
            fn_name = (call.get("function", {}) or {}).get("name") or call.get("name")
            raw_args = (call.get("function", {}) or {}).get("arguments")
            args: Dict[str, Any] = {}
            if isinstance(raw_args, str):
                try:
                    args = json.loads(raw_args)
                except Exception:
                    args = {}
            elif isinstance(call.get("input"), dict):
                args = call.get("input")

            results.append(await self._execute_supported_tool(fn_name, args))

        return results

    async def _handle_gemini_function_calls(self, function_calls: Any) -> List[Dict[str, Any]]:
        """Execute Gemini-style function calls and return structured results."""
        results: List[Dict[str, Any]] = []
        if not function_calls:
            return results

        for fc in function_calls or []:
            fn_name = fc.get("name")
            args = fc.get("args", {}) or {}
            results.append(await self._execute_supported_tool(fn_name, args))

        return results

    async def _execute_supported_tool(self, fn_name: Any, args: Dict[str, Any]) -> Dict[str, Any]:
        """Run a supported tool and return a normalized execution record."""
        if fn_name == "tavily_web_search":
            query = args.get("query", "")
            depth = args.get("search_depth", "basic")
            max_results = int(args.get("max_results", 5) or 5)
            if _run_tavily_search:
                result_json = await _run_tavily_search(query, depth, max_results)
            else:
                result_json = json.dumps({"error": "tavily not available in this environment"})
            return {
                "name": fn_name,
                "args": {"query": query, "search_depth": depth, "max_results": max_results},
                "result": result_json
            }

        return {
            "name": fn_name,
            "args": args,
            "result": json.dumps({"error": f"unsupported tool '{fn_name}'"})
        }
