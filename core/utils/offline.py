"""
core/utils/offline.py

Offline stubs to run the full pipeline without real API calls.
Provides patch_factory_offline() that swaps provider architects with
DummyArchitects returning deterministic outputs and emits a Tavily
tool call for the Researcher to exercise tool execution.
"""

from typing import Any, Dict, List, Optional

from core.agents.base import BaseArchitect, ReasoningMode, ModelProvider
from config.agents import MODEL_CONFIG


class DummyArchitect(BaseArchitect):
    def __init__(
        self,
        provider: ModelProvider = ModelProvider.OPENAI,
        model_name: str = "offline-dummy",
        reasoning: ReasoningMode = ReasoningMode.DISABLED,
        name: Optional[str] = None,
        role: Optional[str] = None,
        responsibilities: Optional[List[str]] = None,
        prompt_template: Optional[str] = None,
        tools_config: Optional[Dict] = None,
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

    async def analyze(self, context: Dict[str, Any], tools: Optional[List[Any]] = None) -> Dict[str, Any]:
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

    async def create_analysis_plan(self, phase1_results: Dict, prompt: Optional[str] = None) -> Dict:
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

    async def synthesize_findings(self, phase3_results: Dict, prompt: Optional[str] = None) -> Dict:
        return {"analysis": "Offline synthesis of agent findings"}

    async def final_analysis(self, consolidated_report: Dict, prompt: Optional[str] = None) -> Dict:
        return {"analysis": "You are an offline final analysis assistant. Provide concise Cursor rules."}

    async def consolidate_results(self, all_results: Dict, prompt: Optional[str] = None) -> Dict:
        return {"phase": "Consolidation", "report": "Offline consolidated report"}


def patch_factory_offline() -> None:
    from core.agents.factory import factory as fact

    def _make_dummy(name: Optional[str], role: Optional[str], responsibilities: Optional[List[str]]):
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
        name: Optional[str] = None,
        role: Optional[str] = None,
        responsibilities: Optional[List[str]] = None,
        prompt_template: Optional[str] = None,
    ) -> BaseArchitect:
        agent_name = name or f"{phase.title()} Architect (Offline)"
        agent_role = role or "analyzing the project offline"
        return _make_dummy(agent_name, agent_role, responsibilities)

    def get_researcher_architect_stub(
        name: str,
        role: str,
        responsibilities: List[str],
        prompt_template: Optional[str] = None,
    ) -> BaseArchitect:
        return _make_dummy(name or "Researcher Agent", role or "research", responsibilities)

    fact.get_architect_for_phase = get_architect_for_phase_stub  # type: ignore
    fact.get_researcher_architect = get_researcher_architect_stub  # type: ignore

