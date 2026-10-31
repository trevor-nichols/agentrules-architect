"""Render the prompt templates with data that contains literal braces."""

from agentrules.config.prompts.final_analysis_prompt import format_final_analysis_prompt
from agentrules.config.prompts.phase_2_prompts import format_phase2_legacy_prompt, format_phase2_structured_prompt
from agentrules.config.prompts.phase_3_prompts import format_phase3_system_prompt
from agentrules.config.prompts.phase_5_prompts import format_phase5_prompt


def test_phase2_templates_render_structured_data_with_literal_braces() -> None:
    discovery = {"finding": '{"enabled": true}'}
    tree = ["src/{module}.py"]

    for render in (format_phase2_structured_prompt, format_phase2_legacy_prompt):
        prompt = render(discovery, tree)
        assert "src/{module}.py" in prompt
        assert '"finding": "{\\"enabled\\": true}"' in prompt
        assert "{project_structure}" not in prompt
        assert "{phase1_results}" not in prompt


def test_phase3_system_template_preserves_agent_values() -> None:
    prompt = format_phase3_system_prompt(
        agent_name="Agent {one}",
        agent_role="reviewing src/{module}.py",
        responsibilities=["Understand {settings}"],
    )

    assert "You are Agent {one}, responsible for reviewing src/{module}.py." in prompt
    assert "- Understand {settings}" in prompt


def test_phase5_and_final_templates_render_report_data() -> None:
    result = {"report": '{"model": "gpt-6-sol"}'}

    phase5 = format_phase5_prompt(result)
    final = format_final_analysis_prompt(result, ["src/{module}.py"], rules_filename="AGENTS.md")

    assert '"report": "{\\"model\\": \\"gpt-6-sol\\"}"' in phase5
    assert '"report": "{\\"model\\": \\"gpt-6-sol\\"}"' in final
    assert "src/{module}.py" in final
    assert "AGENTS.md" in final
