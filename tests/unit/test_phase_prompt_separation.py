from agentrules.config.prompts.phase_1_prompts import PHASE_1_BASE_PROMPT
from agentrules.config.prompts.phase_3_prompts import (
    format_phase3_prompt,
    format_phase3_system_prompt,
)


def test_phase1_user_prompt_excludes_persona_directive() -> None:
    assert "You are" not in PHASE_1_BASE_PROMPT
    assert "{context}" in PHASE_1_BASE_PROMPT


def test_phase3_user_prompt_contains_payload_not_persona() -> None:
    prompt = format_phase3_prompt(
        {
            "tree_structure": ["src/main.py"],
            "assigned_files": ["src/main.py"],
            "file_contents": {"src/main.py": "print('ok')"},
        }
    )
    assert "You are" not in prompt
    assert "FILE CONTENTS:" in prompt


def test_phase3_system_prompt_contains_behavior_and_role() -> None:
    system_prompt = format_phase3_system_prompt(
        agent_name="Architecture Agent",
        agent_role="architecture review",
        responsibilities=["Map module boundaries"],
    )
    assert "You are Architecture Agent" in system_prompt
    assert "Map module boundaries" in system_prompt
