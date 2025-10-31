"""
tests/utils/offline_stubs.py

Offline stubs to run smoke tests without real API calls.
Monkeypatches the architect factory to return a DummyArchitect that
produces deterministic outputs and, for the Researcher, emits a Tavily
tool call to exercise the tool execution path.
"""

from typing import Any, Dict, List, Optional

from core.agents.base import BaseArchitect, ReasoningMode, ModelProvider


class DummyArchitect(BaseArchitect):
    """A non-networking architect that returns deterministic outputs."""

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
        print(f"[offline] analyze called for: {agent_name}")
        # For the researcher, emit a Tavily tool call so Phase 1 can exercise tool execution.
        if "Researcher" in (agent_name or "") and tools:
            print("[offline] emitting tool call for researcher")
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
        # Default offline result
        return {
            "agent": agent_name,
            "findings": f"Offline analysis by {agent_name}",
        }

    async def create_analysis_plan(self, phase1_results: Dict, prompt: Optional[str] = None) -> Dict:
        print("[offline] create_analysis_plan called")
        # Try to load canned XML plan for Phase 3 test; fallback to tiny inline plan
        plan = None
        try:
            with open("tests/phase_3_test/test3_input.xml", "r", encoding="utf-8") as f:
                plan = f.read()
        except Exception:
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
        print("[offline] synthesize_findings called")
        return {"analysis": "Offline synthesis of agent findings"}

    async def final_analysis(self, consolidated_report: Dict, prompt: Optional[str] = None) -> Dict:
        print("[offline] final_analysis called")
        # Begin with "You are" so clean_cursorrules checker passes
        return {"analysis": "You are an offline final analysis assistant. Provide concise Cursor rules."}

    async def consolidate_results(self, all_results: Dict, prompt: Optional[str] = None) -> Dict:
        print("[offline] consolidate_results called")
        return {"phase": "Consolidation", "report": "Offline consolidated report"}


def patch_factory_offline() -> None:
    """Monkeypatch the architect factory functions to return DummyArchitects."""
    from core.agents.factory import factory as fact
    import core.agents as agents_pkg
    from config.agents import MODEL_CONFIG

    def _make_dummy(name: Optional[str], role: Optional[str], responsibilities: Optional[List[str]]):
        # Provider selection is irrelevant offline; keep provider/model_name values presentable.
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
        # Ensure name contains Researcher to trigger tool call generation
        return _make_dummy(name or "Researcher Agent", role or "research", responsibilities)

    # Patch both the module-level factory functions and the package-level re-exports
    fact.get_architect_for_phase = get_architect_for_phase_stub  # type: ignore
    fact.get_researcher_architect = get_researcher_architect_stub  # type: ignore
    # Re-exported by core.agents and core.agents.factory package __init__
    try:
        agents_pkg.get_architect_for_phase = get_architect_for_phase_stub  # type: ignore
    except Exception:
        pass
    try:
        # Package-level attribute
        from core.agents import factory as factory_pkg  # type: ignore
        factory_pkg.get_architect_for_phase = get_architect_for_phase_stub  # type: ignore
    except Exception:
        pass
