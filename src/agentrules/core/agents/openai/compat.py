"""Backward-compatible agent shim for legacy imports."""

from __future__ import annotations

from agentrules.core.agents.base import ReasoningMode

from .architect import OpenAIArchitect


class OpenAIAgent:
    """
    Deprecated wrapper retained for callers that still expect the legacy API.

    Prefer instantiating :class:`OpenAIArchitect` directly.
    """

    def __init__(self, model: str = "gpt-5.6-sol", temperature: float | None = None):
        self.model = model

        if model in ["o3", "o4-mini"]:
            self._architect = OpenAIArchitect(model_name=model, reasoning=ReasoningMode.HIGH)
        elif model == "gpt-4.1":
            self._architect = OpenAIArchitect(
                model_name=model,
                reasoning=ReasoningMode.TEMPERATURE,
                temperature=temperature,
            )
        else:
            self._architect = OpenAIArchitect(model_name=model)

    async def create_analysis_plan(self, phase1_results: dict, prompt: str | None = None) -> dict:
        """Delegate to the architect implementation."""
        return await self._architect.create_analysis_plan(phase1_results, prompt)

    async def synthesize_findings(self, phase3_results: dict, prompt: str | None = None) -> dict:
        """Delegate to the architect implementation."""
        return await self._architect.synthesize_findings(phase3_results, prompt)

    async def final_analysis(self, consolidated_report: dict, prompt: str | None = None) -> dict:
        """Delegate to the architect implementation."""
        return await self._architect.final_analysis(consolidated_report, prompt)
