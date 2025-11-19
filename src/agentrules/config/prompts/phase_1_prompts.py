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

# Dependency Agent prompts (dynamic per researcher availability)
DEPENDENCY_KNOWLEDGE_GAP_PROMPT = {
    "name": "Dependency Agent",
    "role": "identifying dependency knowledge gaps",
    "responsibilities": [
        "Survey all manifest files to list the major packages, libraries, and frameworks that define the project",
        "Capture the exact version requirements for each high-impact dependency",
        "Highlight dependencies whose versions you are not familar with (e.g. new versions beyond those in your training data) so downstream agents can research them"
    ]
}

DEPENDENCY_CATALOG_PROMPT = {
    "name": "Dependency Agent",
    "role": "investigating packages and libraries",
    "responsibilities": [
        "Investigate all packages, libraries, and frameworks declared in manifest files",
        "Determine version requirements and note any discrepancies or conflicts",
        "Summarize key runtime and build tooling so downstream agents have a complete reference"
    ]
}

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
    "role": "researching and documenting current versions of dependencies and frameworks",
    "responsibilities": [
        "Receive a list of technologies (packages, libraries, frameworks) with their specific versions that may be beyond your training data or have significant updates",
        "For each technology, use the web search tool to find and retrieve the official documentation for that specific version",
        "Read and synthesize the documentation to extract key information: new features, breaking changes, API updates, best practices, and important usage patterns",
        "Create comprehensive documentation summaries for each technology so downstream agents have accurate, up-to-date context",
        "Focus on information that would impact code analysis: API changes, deprecated features, new capabilities, and version-specific gotchas",
        "Return structured documentation that fills knowledge gaps and prevents downstream agents from providing outdated advice"
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

def get_dependency_agent_prompt(researcher_enabled: bool) -> dict:
    """Return the dependency agent prompt suited to the active researcher mode."""

    prompt = (
        DEPENDENCY_KNOWLEDGE_GAP_PROMPT
        if researcher_enabled
        else DEPENDENCY_CATALOG_PROMPT
    )
    return {
        "name": prompt["name"],
        "role": prompt["role"],
        "responsibilities": list(prompt["responsibilities"]),
    }


# List of all Phase 1 agent configurations (default order assumes researcher enabled)
PHASE_1_AGENTS = [
    DEPENDENCY_KNOWLEDGE_GAP_PROMPT,
    STRUCTURE_AGENT_PROMPT,
    TECH_STACK_AGENT_PROMPT,
    RESEARCHER_AGENT_PROMPT
]
