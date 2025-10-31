"""
core/analysis/phase_3.py

This module provides functionality for Phase 3 (Deep Analysis) of the project analysis.
It defines the agents and methods needed for in-depth analysis of the project's code and architecture.
"""

# ====================================================
# Importing Required Libraries
# This section imports all the necessary libraries and modules needed for the script.
# ====================================================

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import os
from core.agents.anthropic import AnthropicArchitect
from core.utils.file_system.file_retriever import get_filtered_formatted_contents
from core.agents import get_architect_for_phase
from config.prompts.phase_3_prompts import format_phase3_prompt

# ====================================================
# Phase 3 Analysis Class
# This class handles the deep analysis phase (Phase 3) of the project.
# It uses AI agents to analyze the code and architecture.
# ====================================================

class Phase3Analysis:
    """
    Class responsible for Phase 3 (Deep Analysis) of the project analysis.
    
    This phase uses the agent assignments from Phase 2 to perform
    deep analysis of individual files in the project.
    """
    
    # ====================================================
    # Initialization (__init__)
    # This method sets up the initial state of the Phase3Analysis class.
    # ====================================================
    def __init__(self):
        """
        Initialize the Phase 3 analysis with required components.
        """
        # The actual architects will be created dynamically based on Phase 2 output
        self.architects = []
        
    # ====================================================
    # Run Analysis Function
    # This function runs the deep analysis using the created agents.
    # ====================================================
    async def run(self, analysis_plan: Dict, tree: List[str], directory: Path) -> Dict:
        """
        Run the Deep Analysis Phase.
        
        Args:
            analysis_plan: Dictionary containing the analysis plan from Phase 2
            tree: List of strings representing the project directory tree
            directory: Path to the project directory
            
        Returns:
            Dictionary containing the results of the phase
        """
        try:
            # Default fallback agents in case no agents were defined in Phase 2
            fallback_agents = [
                {
                    "id": "agent_1",
                    "name": "Code Analysis Agent",
                    "description": "Analyzes code quality, patterns, and implementation details",
                    "file_assignments": []  # Will be populated with all files
                },
                {
                    "id": "agent_2",
                    "name": "Dependency Mapping Agent",
                    "description": "Maps dependencies between files and modules",
                    "file_assignments": []  # Will be populated with all files
                },
                {
                    "id": "agent_3",
                    "name": "Architecture Agent",
                    "description": "Analyzes overall architecture and design patterns",
                    "file_assignments": []  # Will be populated with all files
                }
            ]
            
            # Get agent definitions from Phase 2
            agent_definitions = analysis_plan.get("agents", [])
            
            # Use fallback if no agents were defined
            if not agent_definitions:
                logging.warning("[bold yellow]Warning:[/bold yellow] No agents defined in Phase 2 output, using fallback agents")
                agent_definitions = fallback_agents
                
                # Assign all files to all fallback agents
                all_file_paths = []
                for line in tree:
                    if ".py" in line or ".js" in line or ".ts" in line or ".jsx" in line or ".tsx" in line:
                        path_match = line.strip().split(" ")[-1]  # Extract the file path
                        all_file_paths.append(path_match)
                
                for agent in agent_definitions:
                    agent["file_assignments"] = all_file_paths
            
            # Create architects for each agent
            self.architects = []
            
            logging.info(f"[bold]Phase 3:[/bold] Creating {len(agent_definitions)} specialized analysis agents")
            for agent_def in agent_definitions:
                agent_name = agent_def.get("name", "Unknown Agent")
                files_count = len(agent_def.get('file_assignments', []))
                logging.info(f"  [bold cyan]Agent {agent_def['id'].split('_')[1]}:[/bold cyan] {agent_name} with {files_count} files")
                
                # Create an architect for this agent
                architect = get_architect_for_phase(
                    "phase3",
                    name=agent_name,
                    role=agent_def.get("description", "Analyzing the project"),
                    responsibilities=agent_def.get("responsibilities", [])
                )
                self.architects.append((architect, agent_def))
            
            # Create analysis tasks for each architect
            analysis_tasks = []
            
            logging.info("[bold]Phase 3:[/bold] Beginning parallel analysis of files")
            for architect, agent_def in self.architects:
                # Get the files assigned to this agent
                assigned_files = agent_def.get("file_assignments", [])
                
                # Skip if no files assigned
                if not assigned_files:
                    logging.warning(f"[bold yellow]Warning:[/bold yellow] No files assigned to {agent_def.get('name', 'Unknown Agent')}, skipping")
                    continue
                
                # Get the content of assigned files
                file_contents = await self._get_file_contents(directory, assigned_files)
                
                # Create the context for this agent
                context = {
                    "agent_name": agent_def.get("name", "Analysis Agent"),
                    "agent_role": agent_def.get("description", "Analyzing the project"),
                    "assigned_files": assigned_files,
                    "file_contents": file_contents,
                    "tree_structure": tree,
                }
                
                # Create a formatted prompt for this agent
                formatted_prompt = format_phase3_prompt(context)
                context["formatted_prompt"] = formatted_prompt
                
                # Add the analysis task
                analysis_tasks.append(architect.analyze(context))
            
            # Run all analysis tasks in parallel
            results = await asyncio.gather(*analysis_tasks)
            
            logging.info(f"[bold green]Phase 3:[/bold green] All {len(analysis_tasks)} agents completed their analysis")
            
            # Return the results with phase information
            return {
                "phase": "Deep Analysis",
                "findings": results
            }
        except Exception as e:
            logging.error(f"[bold red]Error in Phase 3:[/bold red] {str(e)}")
            return {
                "phase": "Deep Analysis",
                "error": str(e)
            }
    
    async def _get_file_contents(self, directory: Path, assigned_files: List[str]) -> Dict[str, str]:
        """
        Get the contents of files assigned to an agent.
        
        Args:
            directory: Project directory
            assigned_files: List of file paths assigned to the agent
            
        Returns:
            Dictionary of {file_path: file_content}
        """
        # Simple async wrapper around synchronous file operations
        # In a real implementation, you might want to use asyncio.to_thread or similar
        file_contents = {}
        
        for file_path in assigned_files:
            try:
                # Handle both absolute and relative paths
                full_path = os.path.join(directory, file_path)
                
                # Try to read the file
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    file_contents[file_path] = content
                else:
                    # Try relative path
                    rel_path = file_path.lstrip('./')  # Remove leading ./ if present
                    full_path = os.path.join(directory, rel_path)
                    
                    if os.path.exists(full_path) and os.path.isfile(full_path):
                        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                            content = f.read()
                        file_contents[file_path] = content
                    else:
                        logging.warning(f"Could not find file: {file_path}")
            except Exception as e:
                logging.error(f"Error reading file {file_path}: {str(e)}")
        
        return file_contents
