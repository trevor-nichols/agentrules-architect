"""Backward-compatible GeminiAgent wrapper."""

from __future__ import annotations

from typing import Any

from .architect import GeminiArchitect


class GeminiAgent:
    """
    Legacy wrapper retained for compatibility with historical code paths.

    New implementations should depend on ``GeminiArchitect`` directly.
    """

    def __init__(
        self,
        name: str,
        role: str,
        responsibilities: list[str],
        prompt_template: str | None = None,
        api_key: str | None = None,
    ):
        self.name = name
        self.role = role
        self.responsibilities = responsibilities
        self._architect = GeminiArchitect(
            name=name,
            role=role,
            responsibilities=responsibilities,
            prompt_template=prompt_template,
            api_key=api_key,
            tools_config=None,
        )
        self.prompt_template = prompt_template or self._architect.prompt_template

    def _format_prompt(self, context: dict[str, Any]) -> str:
        return self._architect.format_prompt(context)

    def format_prompt(self, context: dict[str, Any]) -> str:
        return self._format_prompt(context)

    async def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        return await self._architect.analyze(context)

    async def create_analysis_plan(self, phase1_results: dict, prompt: str | None = None) -> dict:
        return await self._architect.create_analysis_plan(phase1_results, prompt)

    async def synthesize_findings(self, phase3_results: dict, prompt: str | None = None) -> dict:
        return await self._architect.synthesize_findings(phase3_results, prompt)

    async def final_analysis(self, consolidated_report: dict, prompt: str | None = None) -> dict:
        return await self._architect.final_analysis(consolidated_report, prompt)
