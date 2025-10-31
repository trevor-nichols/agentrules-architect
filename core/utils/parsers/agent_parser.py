#!/usr/bin/env python3
"""
core/utils/parsers/agent_parser.py

This module provides functionality for parsing agent assignments from Phase 2's
output format. It extracts agent definitions, responsibilities, and file
assignments to enable dynamic agent creation in Phase 3.

This module is used by Phase 3 to create agents based on Phase 2's allocation plan.
"""

# ====================================================
# Importing Necessary Libraries
# ====================================================

import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Union, Any
import xml.etree.ElementTree as ET
from io import StringIO

# ====================================================
# Initialize Logger
# ====================================================

logger = logging.getLogger("project_extractor")

# ====================================================
# Define XML Tag Constants
# ====================================================

DESCRIPTION_TAG = "description"
FILE_ASSIGNMENTS_TAG = "file_assignments"
FILE_PATH_TAG = "file_path"
NAME_TAG = "name"
EXPERTISE_TAG = "expertise"
RESPONSIBILITIES_TAG = "responsibilities"
RESPONSIBILITY_TAG = "responsibility"
REASONING_TAG = "reasoning"
ANALYSIS_PLAN_TAG = "analysis_plan"

# ====================================================
# Helper Functions
# ====================================================

def extract_from_json(data: Union[Dict, str]) -> str:
    """
    Extract the plan field from a JSON object or JSON string.
    
    Args:
        data: Either a dictionary or a JSON string
        
    Returns:
        str: The extracted plan content or original data if not found
    """
    # Handle dictionary input
    if isinstance(data, dict):
        logger.debug("Extracting plan from dictionary")
        if "plan" in data:
            return data["plan"]
        else:
            logger.debug("No 'plan' field found in dictionary")
            return ""
    
    # Handle potential JSON string
    if isinstance(data, str) and data.strip().startswith('{'):
        try:
            json_data = json.loads(data)
            if isinstance(json_data, dict) and "plan" in json_data:
                logger.debug("Extracted plan from JSON string")
                return json_data["plan"]
        except json.JSONDecodeError:
            logger.debug("Failed to parse as JSON, continuing with raw string")
            pass
    
    # Return original data if no extraction possible
    return data

def extract_from_markdown_block(content: str) -> str:
    """
    Extract content from various markdown code block formats.
    
    Args:
        content: String potentially containing markdown code blocks
        
    Returns:
        str: Content with markdown formatting removed
    """
    # Case 1: Four backticks format (````xml)
    four_backticks = re.search(r'````(?:xml|)\s*\n?(.*?)```', content, re.DOTALL)
    if four_backticks:
        logger.debug("Extracted content from four-backtick format")
        return four_backticks.group(1).strip()
    
    # Case 2: Standard markdown block (```xml)
    three_backticks = re.search(r'```(?:xml|)\s*\n?(.*?)```', content, re.DOTALL)
    if three_backticks:
        logger.debug("Extracted content from three-backtick format")
        return three_backticks.group(1).strip()
    
    # Case 3: Multiple code blocks or incomplete blocks
    if '```' in content:
        logger.debug("Cleaning up multiple markdown code blocks")
        cleaned = re.sub(r'```(?:xml|)?\s*\n?', '', content)
        cleaned = cleaned.replace('```', '')
        return cleaned.strip()
    
    # No markdown blocks found, return original
    return content

def extract_xml_content(content: str) -> str:
    """
    Extract XML content from between analysis_plan tags or restructure content to be valid XML.
    
    Args:
        content: String potentially containing XML content
        
    Returns:
        str: Properly formatted XML content
    """
    # Check if we have both reasoning and analysis_plan tags at the root level
    if re.search(r'^\s*<reasoning>.*?</reasoning>\s*<analysis_plan>', content, re.DOTALL):
        logger.info("Found both reasoning and analysis_plan tags, wrapping in root element")
        # Clean up empty lines and normalize spacing to avoid parsing issues
        cleaned_content = re.sub(r'\n\s*\n', '\n', content)
        return f"<root>{cleaned_content}</root>"
    
    # Try to find <analysis_plan> tags
    plan_match = re.search(r'<analysis_plan>(.*?)</analysis_plan>', content, re.DOTALL)
    
    # If not found, check for <reasoning> followed by <analysis_plan>
    if not plan_match:
        reasoning_and_plan = re.search(
            r'<reasoning>.*?</reasoning>.*?<analysis_plan>(.*?)</analysis_plan>',
            content, re.DOTALL
        )
        if reasoning_and_plan:
            logger.info("Found analysis_plan after reasoning tag")
            return reasoning_and_plan.group(1).strip()
        else:
            # If still not found, look for agent tags directly
            agent_matches = re.findall(r'<agent_\d+.*?>.*?</agent_\d+>', content, re.DOTALL)
            if agent_matches:
                logger.info("Extracted agent definitions without analysis_plan wrapper")
                return "\n".join(agent_matches)
            else:
                logger.error("Could not find any valid agent definitions")
                return ""
    else:
        return plan_match.group(1).strip()

def clean_and_fix_xml(xml_content: str) -> str:
    """
    Clean and fix common XML issues.
    
    Args:
        xml_content: Raw XML string with potential issues
        
    Returns:
        str: Cleaned and fixed XML content
    """
    if not xml_content:
        return "<analysis_plan></analysis_plan>"
    
    # Remove excessive whitespace and normalize newlines
    xml_content = re.sub(r'\n\s*\n', '\n', xml_content)
    
    # Fix non-standard attribute format in agent tags
    # Replace <agent_1="Name"> with <agent_1 name="Name">
    fixed_content = re.sub(r'<(agent_\d+)="([^"]*)">', r'<\1 name="\2">', xml_content)
    
    # Escape any potentially problematic characters in content between tags
    fixed_content = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;)', '&amp;', fixed_content)
    
    # Replace any double quotes inside attribute values that are already in double quotes
    # This is a common issue with model-generated XML
    # Look for patterns like name="This is a "quoted" word"
    quote_pattern = r'(\w+)="([^"]*)"([^"]*)"([^"]*)"'
    while re.search(quote_pattern, fixed_content):
        fixed_content = re.sub(quote_pattern, r'\1="\2\'\3\'\4"', fixed_content)
    
    # Fix missing quotes in attribute values
    # Look for patterns like name=Some Value> and change to name="Some Value">
    fixed_content = re.sub(r'(\w+)=([^"][^ >]*)([ >])', r'\1="\2"\3', fixed_content)
    
    # Remove any invalid XML characters
    fixed_content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', fixed_content)
    
    # Wrap in a root element if not already present
    if fixed_content.strip().startswith('<root>'):
        return fixed_content  # Already has a root element
    elif not fixed_content.strip().startswith('<analysis_plan'):
        fixed_content = f"<analysis_plan>\n{fixed_content}\n</analysis_plan>"
    
    return fixed_content

# ====================================================
# Main Parser Functions
# ====================================================

def parse_agent_definition(agent_element: ET.Element) -> Dict:
    """
    Parse an agent element into a structured dictionary.
    
    Args:
        agent_element: XML Element representing an agent
        
    Returns:
        Dict: Structured agent definition
    """
    agent_id = agent_element.tag
    agent_info = {
        "id": agent_id,
        "name": "",
        "description": "",
        "expertise": [],
        "responsibilities": [],
        "file_assignments": []
    }
    
    # Get agent name from attribute first
    if "name" in agent_element.attrib:
        agent_info["name"] = agent_element.attrib["name"]
    else:
        # Try to get name from child element
        name_elem = agent_element.find(NAME_TAG)
        if name_elem is not None and name_elem.text:
            agent_info["name"] = name_elem.text.strip()
        else:
            # Use agent_id as fallback name
            agent_info["name"] = agent_id.replace("_", " ").title()
    
    # Get description
    description_elem = agent_element.find(DESCRIPTION_TAG)
    if description_elem is not None and description_elem.text:
        agent_info["description"] = description_elem.text.strip()
    
    # Get expertise
    expertise_elem = agent_element.find(EXPERTISE_TAG)
    if expertise_elem is not None and expertise_elem.text:
        agent_info["expertise"] = [exp.strip() for exp in expertise_elem.text.split(',')]
    
    # Get responsibilities
    responsibilities_elem = agent_element.find(RESPONSIBILITIES_TAG)
    if responsibilities_elem is not None:
        for resp_elem in responsibilities_elem.findall(RESPONSIBILITY_TAG):
            if resp_elem.text:
                agent_info["responsibilities"].append(resp_elem.text.strip())
    
    # Get file assignments
    file_assignments_elem = agent_element.find(FILE_ASSIGNMENTS_TAG)
    if file_assignments_elem is not None:
        for file_path_elem in file_assignments_elem.findall(FILE_PATH_TAG):
            if file_path_elem.text and file_path_elem.text.strip():
                agent_info["file_assignments"].append(file_path_elem.text.strip())
    
    return agent_info

def extract_agent_fallback(content: str) -> List[Dict]:
    """
    Extract agent definitions using regex as a fallback when XML parsing fails.
    
    Args:
        content: Raw text containing agent definitions
        
    Returns:
        List[Dict]: List of agent definitions
    """
    agents = []
    
    # Try to extract full analysis_plan section
    plan_match = re.search(r'<analysis_plan>(.*?)</analysis_plan>', content, re.DOTALL)
    if plan_match:
        logger.info("Found analysis_plan section in fallback extraction")
        content = plan_match.group(1)
    
    # Find all file assignment blocks
    assignment_blocks = re.findall(r'<file_assignments>(.*?)</file_assignments>', content, re.DOTALL)
    
    # Try to extract agent blocks with full details
    agent_block_pattern = r'<agent_(\d+)[^>]*>.*?<description>(.*?)</description>.*?<file_assignments>(.*?)</file_assignments>'
    agent_blocks = re.findall(agent_block_pattern, content, re.DOTALL)
    
    if agent_blocks:
        logger.info(f"Found {len(agent_blocks)} complete agent blocks")
        for num, desc, files_section in agent_blocks:
            agent_id = f"agent_{num}"
            
            # Try to find the agent name
            name_match = re.search(rf'<{agent_id}[^>]*name="([^"]*)"', content)
            if name_match:
                agent_name = name_match.group(1)
            else:
                name_tag_match = re.search(rf'<{agent_id}[^>]*>.*?<name>(.*?)</name>', content, re.DOTALL)
                if name_tag_match:
                    agent_name = name_tag_match.group(1).strip()
                else:
                    # Extract name from description if not found otherwise
                    name_from_desc = re.search(r'^([^\.,:]+)', desc.strip())
                    agent_name = name_from_desc.group(1).strip() if name_from_desc else f"Agent {num}"
            
            # Extract files
            file_paths = re.findall(r'<file_path>(.*?)</file_path>', files_section, re.DOTALL)
            file_paths = [path.strip() for path in file_paths if path.strip()]
            
            agent_info = {
                "id": agent_id,
                "name": agent_name.replace("&amp;", "and"),
                "description": desc.strip().replace("&amp;", "and"),
                "expertise": [],
                "responsibilities": [],
                "file_assignments": file_paths
            }
            
            agents.append(agent_info)
        
        if agents:
            return agents
    
    # If no complete blocks found, try simpler extraction
    agent_matches = re.findall(r'<(agent_\d+)\s+name="([^"]*)"', content, re.DOTALL)
    
    # If not found, look for agent tags and try to find names inside
    if not agent_matches:
        agent_ids = re.findall(r'<(agent_\d+)[^>]*>', content, re.DOTALL)
        agent_matches = []
        
        for agent_id in agent_ids:
            name_pattern = f'<{agent_id}[^>]*>.*?<name>(.*?)</name>'
            name_match = re.search(name_pattern, content, re.DOTALL)
            name = name_match.group(1).strip() if name_match else f"Agent {agent_id.split('_')[1]}"
            agent_matches.append((agent_id, name))
    
    # Process the matches if found
    if agent_matches:
        for i, (agent_id, agent_name) in enumerate(agent_matches):
            file_paths = []
            if i < len(assignment_blocks):
                block = assignment_blocks[i]
                file_paths = re.findall(r'<file_path>(.*?)</file_path>', block, re.DOTALL)
                file_paths = [path.strip() for path in file_paths if path.strip()]
            
            # Try to get description
            desc_pattern = f'<{agent_id}[^>]*>.*?<description>(.*?)</description>'
            desc_match = re.search(desc_pattern, content, re.DOTALL)
            description = desc_match.group(1).strip() if desc_match else f"Agent {i+1}"
            
            agent_info = {
                "id": agent_id,
                "name": agent_name.replace("&amp;", "and"),
                "description": description.replace("&amp;", "and"),
                "expertise": [],
                "responsibilities": [],
                "file_assignments": file_paths
            }
            
            agents.append(agent_info)
    
    # Last resort - if we have file assignments but no agents, create default agents
    if not agents and assignment_blocks:
        all_files = []
        for block in assignment_blocks:
            file_paths = re.findall(r'<file_path>(.*?)</file_path>', block, re.DOTALL)
            all_files.extend([path.strip() for path in file_paths if path.strip()])
        
        if all_files:
            agents.append({
                "id": "agent_1",
                "name": "Fallback Agent",
                "description": "Automatically created fallback agent",
                "expertise": [],
                "responsibilities": [],
                "file_assignments": all_files
            })
    
    # Ultra fallback - search for file paths anywhere in the content
    if not agents:
        last_chance_files = re.findall(r'<file_path>(.*?)</file_path>', content, re.DOTALL)
        if last_chance_files:
            logger.info("Last resort extraction found some files")
            agents.append({
                "id": "agent_1",
                "name": "Emergency Fallback Agent",
                "description": "Emergency fallback agent created when no other extraction methods worked",
                "expertise": [],
                "responsibilities": [],
                "file_assignments": [f.strip() for f in last_chance_files if f.strip()]
            })
    
    return agents

def parse_agents_from_phase2(input_data: Union[Dict, str]) -> List[Dict]:
    """
    Universal parser that handles any format of Phase 2 output.
    
    This function is the main entry point for parsing agent definitions.
    It gracefully handles various input formats including:
    - Dictionaries with "plan" or "agents" fields
    - JSON strings
    - XML wrapped in markdown code blocks
    - Direct XML
    
    Args:
        input_data: Phase 2 output in any supported format
        
    Returns:
        List[Dict]: List of agent definitions
    """
    logger.debug(f"Starting agent parsing with input type: {type(input_data).__name__}")
    
    # STEP 1: Check if agents are already available in the input
    if isinstance(input_data, dict):
        # Direct access to pre-parsed agents if available
        if "agents" in input_data and isinstance(input_data["agents"], list):
            agents = input_data["agents"]
            if agents:
                logger.info(f"[bold green]Agents:[/bold green] Found {len(agents)} pre-parsed agents")
                return agents
    
    # STEP 2: Extract text from JSON if needed
    content = extract_from_json(input_data)
    
    # STEP 3: Handle empty or None content
    if not content:
        logger.warning("[bold yellow]Warning:[/bold yellow] Received empty content after extraction")
        return []
    
    # STEP 4: Extract from markdown code blocks if present
    content = extract_from_markdown_block(content)
    
    # STEP 5: Try XML parsing first
    try:
        # Extract XML content and clean it
        xml_content = extract_xml_content(content)
        xml_content = clean_and_fix_xml(xml_content)
        
        # Parse the XML
        root = ET.fromstring(xml_content)
        
        agents = []
        # Extract agent definitions from the XML
        
        # Check if we wrapped in a root element
        if root.tag == "root":
            # Find the analysis_plan element
            analysis_plan = root.find("analysis_plan")
            if analysis_plan is not None:
                for element in analysis_plan:
                    if element.tag.startswith("agent_"):
                        agent_info = parse_agent_definition(element)
                        agents.append(agent_info)
        else:
            # Regular agent extraction
            for element in root:
                if element.tag.startswith("agent_"):
                    agent_info = parse_agent_definition(element)
                    agents.append(agent_info)
        
        if agents:
            logger.info(f"[bold green]Success:[/bold green] Extracted {len(agents)} agents via XML parsing")
            _log_detailed_agent_info(agents, "XML")
            return agents
    except ET.ParseError as e:
        logger.debug(f"XML parsing failed: {e}. Falling back to regex method.")
    except Exception as e:
        logger.debug(f"Unexpected error during XML parsing: {str(e)}. Using fallback.")
    
    # STEP 6: Fallback to regex extraction
    logger.info("[bold yellow]Notice:[/bold yellow] Using regex-based extraction as fallback")
    agents = extract_agent_fallback(content)
    
    # Report results
    if agents:
        logger.info(f"[bold green]Success:[/bold green] Extracted {len(agents)} agents via fallback extraction")
        _log_detailed_agent_info(agents, "fallback")
    else:
        logger.error("[bold red]Error:[/bold red] Failed to extract any agents using all available methods")
    
    return agents

def _log_detailed_agent_info(agents: List[Dict], method: str) -> None:
    """
    Helper function to log detailed agent information.
    
    Args:
        agents: List of agent definitions
        method: The method used to extract agents
    """
    logger.debug(f"===== AGENT SUMMARY ({method}) =====")
    logger.debug(f"Total agents found: {len(agents)}")
    
    # Only log the first agent in detail at INFO level
    if agents:
        first_agent = agents[0]
        logger.info(f"  [bold cyan]First Agent:[/bold cyan] {first_agent.get('name', 'Unknown')} with {len(first_agent.get('file_assignments', []))} files")
    
    # Log the rest at DEBUG level
    for i, agent in enumerate(agents):
        logger.debug(f"  Agent {i+1}: {agent.get('name', 'Unknown')} (ID: {agent.get('id', 'unknown')})")
        logger.debug(f"    Description: {agent.get('description', 'No description')[:50]}...")
        logger.debug(f"    Files assigned: {len(agent.get('file_assignments', []))}")
        if agent.get('file_assignments'):
            for j, file_path in enumerate(agent['file_assignments'][:3]):  # Show first 3 files
                logger.debug(f"      - {file_path}")
            if len(agent['file_assignments']) > 3:
                logger.debug(f"      - ... and {len(agent['file_assignments']) - 3} more files")
    
    logger.debug("================================")

# ====================================================
# Utility Functions
# ====================================================

def get_agent_file_mapping(phase2_output: Union[Dict, str]) -> Dict[str, List[str]]:
    """
    Get a mapping of agent IDs to their assigned files.
    
    Args:
        phase2_output: Phase 2 output in any supported format
        
    Returns:
        Dict[str, List[str]]: Dictionary mapping agent IDs to file paths
    """
    agents = parse_agents_from_phase2(phase2_output)
    mapping = {}
    
    for agent in agents:
        mapping[agent["id"]] = agent["file_assignments"]
    
    return mapping

def get_all_file_assignments(phase2_output: Union[Dict, str]) -> List[str]:
    """
    Get a list of all unique file paths assigned to any agent.
    
    Args:
        phase2_output: Phase 2 output in any supported format
        
    Returns:
        List[str]: List of all unique file paths
    """
    agents = parse_agents_from_phase2(phase2_output)
    all_files = set()
    
    for agent in agents:
        for file_path in agent["file_assignments"]:
            all_files.add(file_path)
    
    return list(all_files)