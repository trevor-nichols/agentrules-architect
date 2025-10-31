"""Compatibility wrapper mirroring the legacy ``DeepSeekAgent`` facade."""

from __future__ import annotations

from typing import Any

from .architect import DeepSeekArchitect


class DeepSeekAgent:
    """
    Thin wrapper maintained for backward compatibility.

    Prefer instantiating :class:`DeepSeekArchitect` directly.
    """

    def __init__(
        self,
        name: str | None = None,
        role: str | None = None,
        responsibilities: list[str] | None = None,
        **architect_kwargs: Any,
    ) -> None:
        self.architect = DeepSeekArchitect(
            name=name,
            role=role,
            responsibilities=responsibilities,
            **architect_kwargs,
        )

    async def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        return await self.architect.analyze(context)

    async def create_analysis_plan(self, phase1_results: dict, prompt: str | None = None) -> dict[str, Any]:
        return await self.architect.create_analysis_plan(phase1_results, prompt)

    async def synthesize_findings(self, phase3_results: dict, prompt: str | None = None) -> dict[str, Any]:
        return await self.architect.synthesize_findings(phase3_results, prompt)

    async def final_analysis(self, consolidated_report: dict, prompt: str | None = None) -> dict[str, Any]:
        return await self.architect.final_analysis(consolidated_report, prompt)

    async def consolidate_results(self, all_results: dict, prompt: str | None = None) -> dict[str, Any]:
        return await self.architect.consolidate_results(all_results, prompt)

