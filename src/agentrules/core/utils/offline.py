"""
core/utils/offline.py

Offline stubs to run the full pipeline without real API calls.
Provides patch_factory_offline() that swaps provider architects with
DummyArchitects returning deterministic outputs and emits a Tavily
tool call for the Researcher to exercise tool execution.
"""

import os
from typing import Any

from agentrules.config.agents import MODEL_CONFIG
from agentrules.core.agents.base import BaseArchitect, ModelProvider, ReasoningMode


class DummyArchitect(BaseArchitect):
    def __init__(
        self,
        provider: ModelProvider = ModelProvider.OPENAI,
        model_name: str = "offline-dummy",
        reasoning: ReasoningMode = ReasoningMode.DISABLED,
        name: str | None = None,
        role: str | None = None,
        responsibilities: list[str] | None = None,
        prompt_template: str | None = None,
        tools_config: dict | None = None,
    ) -> None:
        super().__init__(
            provider=provider,
            model_name=model_name,
            reasoning=reasoning,
            name=name,
            role=role,
            responsibilities=responsibilities or [],
            tools_config=tools_config or {"enabled": False, "tools": None},
        )
        self.prompt_template = prompt_template or ""

    async def analyze(self, context: dict[str, Any], tools: list[Any] | None = None) -> dict[str, Any]:
        agent_name = self.name or "Dummy Architect"
        if "Researcher" in (agent_name or "") and tools:
            return {
                "agent": agent_name,
                "findings": None,
                "tool_calls": [
                    {
                        "id": "toolcall_1",
                        "type": "function",
                        "function": {
                            "name": "tavily_web_search",
                            "arguments": '{"query": "Flask documentation", "search_depth": "basic", "max_results": 1}'
                        },
                    }
                ],
            }
        return {
            "agent": agent_name,
            "findings": f"Offline analysis by {agent_name}",
        }

    async def create_analysis_plan(self, phase1_results: dict, prompt: str | None = None) -> dict:
        plan = (
            "<analysis_plan>\n"
            "  <agent_1 name=\"Code Analysis Agent\">\n"
            "    <description>Analyzes code quality and patterns</description>\n"
            "    <file_assignments>\n"
            "      <file_path>tests/tests_input/main.py</file_path>\n"
            "    </file_assignments>\n"
            "  </agent_1>\n"
            "</analysis_plan>\n"
        )
        return {"plan": plan}

    async def synthesize_findings(self, phase3_results: dict, prompt: str | None = None) -> dict:
        return {"analysis": "Offline synthesis of agent findings"}

    async def final_analysis(self, consolidated_report: dict, prompt: str | None = None) -> dict:
        return {"analysis": "You are an offline final analysis assistant. Provide concise Agent rules."}

    async def consolidate_results(self, all_results: dict, prompt: str | None = None) -> dict:
        return {"phase": "Consolidation", "report": "Offline consolidated report"}


def patch_factory_offline() -> None:
    from agentrules.core.agents.factory import factory as fact

    os.environ.setdefault("OFFLINE", "1")

    def _make_dummy(name: str | None, role: str | None, responsibilities: list[str] | None):
        model_config = next(iter(MODEL_CONFIG.values()))
        return DummyArchitect(
            provider=model_config.provider,
            model_name=f"offline-{model_config.model_name}",
            reasoning=model_config.reasoning,
            name=name,
            role=role,
            responsibilities=responsibilities or [],
        )

    def get_architect_for_phase_stub(
        phase: str,
        name: str | None = None,
        role: str | None = None,
        responsibilities: list[str] | None = None,
        prompt_template: str | None = None,
        system_prompt: str | None = None,
    ) -> BaseArchitect:
        agent_name = name or f"{phase.title()} Architect (Offline)"
        agent_role = role or "analyzing the project offline"
        return _make_dummy(agent_name, agent_role, responsibilities)

    def get_researcher_architect_stub(
        name: str,
        role: str,
        responsibilities: list[str],
        prompt_template: str | None = None,
        system_prompt: str | None = None,
    ) -> BaseArchitect:
        return _make_dummy(name or "Researcher Agent", role or "research", responsibilities)

    fact.get_architect_for_phase = get_architect_for_phase_stub  # type: ignore
    fact.get_researcher_architect = get_researcher_architect_stub  # type: ignore
