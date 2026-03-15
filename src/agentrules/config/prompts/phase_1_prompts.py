"""
config/prompts/phase_1_prompts.py

This module contains the prompts used by Phase 1 (Initial Discovery) agents.
Centralizing prompts here makes it easier to edit and maintain them without
modifying the core logic of the agents.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from agentrules.core.utils.system_prompt import normalize_responsibilities

# Phase 1 system prompt template (agent behavior/persona guidance).
PHASE_1_SYSTEM_PROMPT = (
    "You are {agent_name}, responsible for {agent_role}.\n\n"
    "You are part of a team of agents working together to analyze and understand a software project.\n"
    "You will be provided files and information about the project, and your task is to produce findings that will help the team build an accurate picture of the project to assist with onboarding.\n\n"
    "Note: You are NOT responsible for identifying security vulnerabilities or code quality issues. Your focus is on understanding the project's structure, dependencies, and tech stack to inform new developers working in this project.\n\n"
    "Responsibilities:\n"
    "{agent_responsibilities}\n\n"
    "Behavior requirements:\n"
    "- Analyze only from evidence in provided project context and tool results.\n"
    "- Keep findings concrete, technically precise, and actionable.\n"
    "- Use clear section headers and concise bullet points when appropriate.\n"
    "- Call out uncertainties explicitly instead of guessing.\n"
)


def _format_responsibilities(responsibilities: object) -> str:
    cleaned = normalize_responsibilities(responsibilities)
    if not cleaned:
        return "- (no specific responsibilities provided)"
    return "\n".join(f"- {item}" for item in cleaned)


def format_phase1_system_prompt(
    *,
    agent_name: str,
    agent_role: str,
    responsibilities: object,
) -> str:
    return PHASE_1_SYSTEM_PROMPT.format(
        agent_name=agent_name,
        agent_role=agent_role,
        agent_responsibilities=_format_responsibilities(responsibilities),
    )


# Base prompt template for all Phase 1 agents (user/task payload only).
PHASE_1_BASE_PROMPT = """Project context:
{context}

Produce the requested phase-1 findings for your assigned scope."""

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
        "Determine version requirements",
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

FRONTEND_DESIGN_AGENT_PROMPT = {
    "name": "Frontend Design Agent",
    "role": "analyzing UI styling architecture and design system surface",
    "responsibilities": [
        "Identify the primary styling approach used by the frontend (Tailwind, CSS modules, global CSS, CSS-in-JS)",
        "Locate likely design-token and variant definitions from configuration files and project layout",
        "Summarize frontend architecture patterns that influence UI composition and onboarding",
        "Call out uncertainty explicitly when styling evidence is incomplete or mixed"
    ],
    "profile_key": "frontend",
}

PYTHON_TOOLING_AGENT_PROMPT = {
    "name": "Python Tooling Agent",
    "role": "analyzing Python packaging, tooling, and local developer workflow surfaces",
    "responsibilities": [
        "Summarize Python packaging and dependency-management conventions across pyproject, requirements, and setup files",
        "Identify task runner entrypoints such as Makefile or justfile and their likely onboarding relevance",
        "Capture tooling surfaces such as tox or nox that shape local development workflows",
        "Highlight mixed or redundant Python tooling conventions that may confuse onboarding"
    ],
    "profile_key": "python",
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


def get_specialized_phase1_agent_prompts(
    project_profile: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    """
    Return specialized Phase 1 agent configs based on deterministic profile signals.

    Specialized agents are optional and should run only when the profile indicates
    a relevant project surface.
    """

    prompts: list[dict[str, Any]] = []
    profile = project_profile if isinstance(project_profile, Mapping) else {}

    if _profile_slice_detected(profile, "frontend"):
        prompts.append(_clone_prompt(FRONTEND_DESIGN_AGENT_PROMPT))
    if _profile_slice_detected(profile, "python"):
        prompts.append(_clone_prompt(PYTHON_TOOLING_AGENT_PROMPT))
    return prompts


def _profile_slice_detected(project_profile: Mapping[str, Any], key: str) -> bool:
    section = project_profile.get(key)
    return bool(isinstance(section, Mapping) and section.get("detected"))


def _clone_prompt(prompt: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "name": str(prompt["name"]),
        "role": str(prompt["role"]),
        "responsibilities": list(prompt.get("responsibilities", [])),
        "profile_key": prompt.get("profile_key"),
    }


# List of all Phase 1 agent configurations (default order assumes researcher enabled)
PHASE_1_AGENTS = [
    DEPENDENCY_KNOWLEDGE_GAP_PROMPT,
    STRUCTURE_AGENT_PROMPT,
    TECH_STACK_AGENT_PROMPT,
    RESEARCHER_AGENT_PROMPT,
    FRONTEND_DESIGN_AGENT_PROMPT,
    PYTHON_TOOLING_AGENT_PROMPT,
]
