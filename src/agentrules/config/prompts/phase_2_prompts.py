"""
config/prompts/phase_2_prompts.py

This module contains the prompts used by Phase 2 (Methodical Planning).
Centralizing prompts here makes it easier to edit and maintain them without
modifying the core logic of the agents.
"""

import json
from collections.abc import Sequence

# Phase 2 system prompts (planner behavior guidance).
PHASE_2_STRUCTURED_SYSTEM_PROMPT = (
    "You are a project documentation planner.\n\n"
    "You are part of a team of agents working together to analyze and understand a software project.\n"
    "Your task is to design 3-5 agents that will help review files in the project in order to produce an accurate picture of the project's structure and functionality for onboarding purposes.\n\n"
    "Note: The agents are NOT responsible for identifying security vulnerabilities or code quality issues. Their focus is on understanding the project's structure, dependencies, and tech stack to inform new developers working in this project.\n\n"
    "Behavior requirements:\n"
    "- Design a practical 3-5 agent plan with balanced workloads.\n"
    "- Ensure broad repository coverage and avoid unnecessary duplication.\n"
    "- Keep outputs concise and machine-parseable.\n"
    "- Follow the response schema contract exactly.\n"
)

PHASE_2_LEGACY_XML_SYSTEM_PROMPT = (
    "You are a project documentation planner.\n\n"
    "You are part of a team of agents working together to analyze and understand a software project.\n"
    "Your task is to design 3-5 agents that will help review files in the project in order to produce an accurate picture of the project's structure and functionality for onboarding purposes.\n\n"
    "Note: The agents are NOT responsible for identifying security vulnerabilities or code quality issues. Their focus is on understanding the project's structure, dependencies, and tech stack to inform new developers working in this project.\n\n"
    "Behavior requirements:\n"
    "- Design a practical 3-5 agent plan with balanced workloads.\n"
    "- Ensure broad repository coverage and avoid unnecessary duplication.\n"
    "- Output valid XML only (no markdown fences) matching the requested structure.\n"
    "- Keep IDs stable as agent_1, agent_2, ... and keep file paths repository-relative.\n"
)

# Base prompt template for Phase 2 (Methodical Planning) when structured outputs
# are enabled for the selected provider/model.
PHASE_2_STRUCTURED_PROMPT = """Project structure:
{project_structure}

Initial findings from the discovery phase:
<initial_findings>
{phase1_results}
</initial_findings>

Output contract:
- `plan`: concise planning summary in markdown/plain text.
- `agents`: list of objects with:
  - `id` as `agent_1`, `agent_2`, ...
  - `name`: short role name
  - `description`: what the agent does
  - `responsibilities`: list of specific responsibilities
  - `file_assignments`: list of file paths
- `reasoning`: optional rationale string.
"""

# Legacy fallback prompt for models/pathways that cannot use structured outputs.
PHASE_2_LEGACY_XML_PROMPT = """Project structure:
{project_structure}

Initial findings from discovery:
<initial_findings>
{phase1_results}
</initial_findings>

# OUTPUT REQUIREMENTS
# 1. Use valid XML format with proper closing tags **NOT IN A CODE BLOCK**
# 2. DO NOT use special characters like &, <, > in agent names or descriptions
# 3. Use only alphanumeric characters and spaces in names
# 4. Keep agent IDs exactly as shown: agent_1, agent_2, agent_3)

---

## OUTPUT FORMAT

<reasoning>
Describe your approach or reasoning here.
</reasoning>

<analysis_plan>
<agent_1 name="agent-name">
<description>Brief description of this agent's role and expertise.</description>
<file_assignments>
<file_path>[File path 1]</file_path>
<file_path>[File path 2]</file_path>
<!-- Additional files as needed -->
</file_assignments>
</agent_1>

<agent_2 name="agent-name">
<description>Brief description of this agent's role and expertise.</description>
<file_assignments>
<file_path>[File path 3]</file_path>
<file_path>[File path 4]</file_path>
<!-- Additional files as needed -->
</file_assignments>
</agent_2>

<agent_3 name="agent-name">
<description>Brief description of this agent's role and expertise.</description>
<file_assignments>
<file_path>[File path 5]</file_path>
<file_path>[File path 6]</file_path>
<!-- Additional files as needed -->
</file_assignments>
</agent_3>

<!-- Add agent_4 and agent_5 with the same structure if needed -->
</analysis_plan>

"""

# Backwards-compatible alias retained for existing imports.
PHASE_2_PROMPT = PHASE_2_STRUCTURED_PROMPT


def format_phase2_structured_system_prompt() -> str:
    return PHASE_2_STRUCTURED_SYSTEM_PROMPT


def format_phase2_legacy_xml_system_prompt() -> str:
    return PHASE_2_LEGACY_XML_SYSTEM_PROMPT


def _format_phase2_template(
    template: str,
    phase1_results: dict,
    project_structure: Sequence[str] | None = None,
) -> str:
    """Render a Phase 2 prompt template with project data."""
    structure_lines = (
        list(project_structure)
        if project_structure is not None
        else ["No project structure provided"]
    )
    structure_str = "\n".join(structure_lines)

    return template.format(
        phase1_results=json.dumps(phase1_results, indent=2),
        project_structure=structure_str,
    )


def format_phase2_structured_prompt(
    phase1_results: dict,
    project_structure: Sequence[str] | None = None,
) -> str:
    """Format the structured-output Phase 2 prompt."""
    return _format_phase2_template(
        PHASE_2_STRUCTURED_PROMPT,
        phase1_results,
        project_structure,
    )


def format_phase2_legacy_prompt(
    phase1_results: dict,
    project_structure: Sequence[str] | None = None,
) -> str:
    """Format the legacy XML Phase 2 prompt used as compatibility fallback."""
    return _format_phase2_template(
        PHASE_2_LEGACY_XML_PROMPT,
        phase1_results,
        project_structure,
    )


def format_phase2_prompt(
    phase1_results: dict,
    project_structure: Sequence[str] | None = None,
    *,
    use_legacy_xml: bool = False,
) -> str:
    """
    Backwards-compatible Phase 2 prompt formatter.

    Args:
        phase1_results: Dictionary containing the results from Phase 1
        project_structure: List of strings representing the project tree structure
        use_legacy_xml: When True, use the old XML prompt instructions

    Returns:
        Formatted prompt string
    """
    if use_legacy_xml:
        return format_phase2_legacy_prompt(phase1_results, project_structure)
    return format_phase2_structured_prompt(phase1_results, project_structure)
