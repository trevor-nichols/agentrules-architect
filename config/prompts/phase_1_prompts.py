"""
config/prompts/phase_1_prompts.py

This module contains the prompts used by Phase 1 (Initial Discovery) agents.
Centralizing prompts here makes it easier to edit and maintain them without
modifying the core logic of the agents.
"""

# Base prompt template for all Phase 1 agents
PHASE_1_BASE_PROMPT = """You are a {agent_name}, responsible for {agent_role}.

Your specific responsibilities are:
{agent_responsibilities}

Analyze this project context and provide a detailed report focused on your domain:

{context}

Format your response as a structured report with clear sections and findings."""

# Specific prompts for each agent in Phase 1

# Structure Agent prompt
STRUCTURE_AGENT_PROMPT = {
    "name": "Structure Agent",
    "role": "analyzing directory and file organization",
    "responsibilities": [
        "Analyze directory and file organization",
        "Map project layout and file relationships",
        "Identify key architectural components"
    ]
}

# Dependency Agent prompt
DEPENDENCY_AGENT_PROMPT = {
    "name": "Dependency Agent",
    "role": "investigating packages and libraries",
    "responsibilities": [
        "Investigate all packages and libraries",
        "Determine version requirements",
        "Research compatibility issues"
    ]
}

# Tech Stack Agent prompt
TECH_STACK_AGENT_PROMPT = {
    "name": "Tech Stack Agent",
    "role": "identifying frameworks and technologies",
    "responsibilities": [
        "Identify all frameworks and technologies",
        "Gather latest documentation for each",
        "Note current best practices and updates"
    ]
}

# Researcher Agent prompt
RESEARCHER_AGENT_PROMPT = {
    "name": "Researcher Agent",
    "role": "finding official documentation for a list of technologies",
    "responsibilities": [
        "Receive a list of technologies (packages, libraries, frameworks).",
        "For each technology, use the web search tool to find the official documentation URL.",
        "Return a structured list of the technologies and their corresponding documentation links."
    ]
}

# Function to format a prompt for a specific agent
def format_agent_prompt(agent_config, context):
    """
    Format a prompt for a specific agent using the base template.
    
    Args:
        agent_config: Dictionary containing agent name, role, and responsibilities
        context: Dictionary containing the context for analysis
        
    Returns:
        Formatted prompt string
    """
    return PHASE_1_BASE_PROMPT.format(
        agent_name=agent_config["name"],
        agent_role=agent_config["role"],
        agent_responsibilities="\n".join(f"- {r}" for r in agent_config["responsibilities"]),
        context=context
    )

# List of all Phase 1 agent configurations
PHASE_1_AGENTS = [
    STRUCTURE_AGENT_PROMPT,
    DEPENDENCY_AGENT_PROMPT,
    TECH_STACK_AGENT_PROMPT,
    RESEARCHER_AGENT_PROMPT
]
