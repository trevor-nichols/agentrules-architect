"""
config/prompts/phase_2_prompts.py

This module contains the prompts used by Phase 2 (Methodical Planning).
Centralizing prompts here makes it easier to edit and maintain them without
modifying the core logic of the agents.
"""

import json
from collections.abc import Sequence

# Base prompt template for Phase 2 (Methodical Planning) when structured outputs
# are enabled for the selected provider/model.
PHASE_2_STRUCTURED_PROMPT = """You are a project documentation planner responsible for assigning specialized agents to analyze a codebase.

Your tasks:
1. Create a team of 3 to 5 agents best suited for this repository.
2. Assign files to agents so all relevant files are covered.
3. Keep assignments practical and balanced by responsibility.

Project structure:
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

Constraints:
- Ensure file paths are repository-relative.
- Avoid duplicate file assignments unless a file genuinely needs multi-agent review.
- Do not include markdown code fences in the response body.
"""

# Legacy fallback prompt for models/pathways that cannot use structured outputs.
PHASE_2_LEGACY_XML_PROMPT = """You are a project documentation planner tasked with processing the <initial_findings>...</initial_findings> from the given <project_structure>...</project_structure> in order to:

1. Create a listing of a team of 3 to 5 agents that would be the best fit to analyze the contents of each file shown within the project structure.

2. Assign each file to the applicable agent you created until all files have been assigned.

# Approach

- Agent Creation: Identify roles and expertise suitable for the project's needs.

- File Assignment: Distribute files based on agent expertise to ensure efficient analysis.

---

{project_structure}

---

<initial_findings>
{phase1_results}
</initial_findings>

---

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
