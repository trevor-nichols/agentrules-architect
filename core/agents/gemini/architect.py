"""Gemini provider implementation of ``BaseArchitect``."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from google.genai import types as genai_types

from core.agents.base import BaseArchitect, ModelProvider, ReasoningMode

from .client import build_gemini_client, generate_content_async
from .prompting import default_prompt_template, format_prompt
from .response_parser import parse_generate_response
from .tooling import resolve_tool_config

logger = logging.getLogger("project_extractor")


class GeminiArchitect(BaseArchitect):
    """Architect class for interacting with Google's Gemini models."""

    def __init__(
        self,
        model_name: str = "gemini-2.0-flash",
        reasoning: ReasoningMode = ReasoningMode.DISABLED,
        name: str | None = None,
        role: str | None = None,
        responsibilities: list[str] | None = None,
        prompt_template: str | None = None,
        api_key: str | None = None,
        tools_config: dict[str, Any] | None = None,
    ):
        super().__init__(
            provider=ModelProvider.GEMINI,
            model_name=model_name,
            reasoning=reasoning,
            name=name,
            role=role,
            responsibilities=responsibilities,
            tools_config=tools_config,
        )
        self.prompt_template = prompt_template or default_prompt_template()
        env_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        resolved_key = api_key or env_key
        should_attempt_client = api_key is not None or env_key is not None or os.environ.get(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )
        if should_attempt_client:
            self.client, self._client_error_hint = build_gemini_client(resolved_key)
        else:
            self.client = None
            self._client_error_hint = (
                "Gemini client not initialized. Provide GEMINI_API_KEY, GOOGLE_API_KEY, "
                "GOOGLE_APPLICATION_CREDENTIALS, or pass api_key directly to GeminiArchitect."
            )

    # Public API -----------------------------------------------------------------
    def format_prompt(self, context: dict[str, Any]) -> str:
        return format_prompt(
            template=self.prompt_template,
            agent_name=self.name or "Gemini Architect",
            agent_role=self.role or "analyzing the project",
            responsibilities=self.responsibilities,
            context=context,
        )

    async def analyze(self, context: dict[str, Any], tools: list[Any] | None = None) -> dict[str, Any]:
        client = self.client
        if client is None:
            return self._client_not_initialized_result()

        prompt = context.get("formatted_prompt") or self.format_prompt(context)

        config_kwargs: dict[str, Any] = {}
        if self.role:
            config_kwargs["system_instruction"] = (
                f"You are {self.name or 'an AI assistant'}, responsible for {self.role}."
            )

        api_tools = resolve_tool_config(tools, self.tools_config)
        if api_tools:
            config_kwargs["tools"] = api_tools

        if self.reasoning == ReasoningMode.ENABLED:
            config_kwargs["thinking_config"] = genai_types.ThinkingConfig(thinking_budget=16000)

        generation_config = genai_types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

        agent_name = self.name or "Gemini Architect"
        details: list[str] = []
        if self.reasoning == ReasoningMode.ENABLED:
            details.append("with thinking")
        if api_tools:
            details.append("with tools enabled")
        detail_suffix = f" ({', '.join(details)})" if details else ""

        from core.utils.model_config_helper import get_model_config_name  # Local import to avoid cycle

        model_config_name = get_model_config_name(self)
        logger.info(
            f"[bold magenta]{agent_name}:[/bold magenta] Sending request to {self.model_name} "
            f"(Config: {model_config_name}){detail_suffix}"
        )

        response = await generate_content_async(
            client,
            model=self.model_name,
            contents=prompt,
            config=generation_config,
        )

        logger.info(f"[bold green]{agent_name}:[/bold green] Received response from {self.model_name}")

        parsed = parse_generate_response(response)
        result: dict[str, Any] = {
            "agent": agent_name,
            "findings": parsed.findings,
        }
        if parsed.function_calls:
            result["function_calls"] = parsed.function_calls
            logger.info(f"[bold magenta]{agent_name}:[/bold magenta] Model requested function call(s).")
            if not parsed.findings:
                result["findings"] = None

        return result

    async def create_analysis_plan(self, phase1_results: dict, prompt: str | None = None) -> dict[str, Any]:
        context: dict[str, Any] = {"phase1_results": phase1_results}
        if prompt:
            context["formatted_prompt"] = prompt
        result = await self.analyze(context)
        return {
            "plan": result.get("findings", "No plan generated"),
            "error": result.get("error"),
        }

    async def synthesize_findings(self, phase3_results: dict, prompt: str | None = None) -> dict[str, Any]:
        context: dict[str, Any] = {"phase3_results": phase3_results}
        if prompt:
            context["formatted_prompt"] = prompt
        result = await self.analyze(context)
        return {
            "analysis": result.get("findings", "No synthesis generated"),
            "error": result.get("error"),
        }

    async def final_analysis(self, consolidated_report: dict, prompt: str | None = None) -> dict[str, Any]:
        context: dict[str, Any] = {"consolidated_report": consolidated_report}
        if prompt:
            context["formatted_prompt"] = prompt
        result = await self.analyze(context)
        return {
            "analysis": result.get("findings", "No final analysis generated"),
            "error": result.get("error"),
        }

    async def consolidate_results(self, all_results: dict, prompt: str | None = None) -> dict[str, Any]:
        client = self.client
        if client is None:
            return {
                "phase": "Consolidation",
                "error": self._client_error_hint or "Gemini client not initialized.",
            }

        content = prompt or (
            "Consolidate these results into a comprehensive report:\n\n"
            f"{json.dumps(all_results, indent=2)}"
        )

        model_name = self._resolve_consolidation_model()
        response = await generate_content_async(
            client,
            model=model_name,
            contents=content,
            config=None,
        )

        parsed = parse_generate_response(response)
        return {
            "phase": "Consolidation",
            "report": parsed.findings or "No report generated",
        }

    # Internal helpers -----------------------------------------------------------
    def _resolve_consolidation_model(self) -> str:
        if self.reasoning != ReasoningMode.ENABLED:
            return self.model_name
        if "gemini-2.0-flash" in self.model_name:
            return "gemini-2.0-flash-thinking-exp"
        if "gemini-2.5-pro" in self.model_name:
            return "gemini-2.5-pro-exp-03-25"
        return self.model_name

    def _client_not_initialized_result(self) -> dict[str, Any]:
        message = self._client_error_hint or "Gemini client not initialized."
        return {
            "agent": self.name or "Gemini Architect",
            "error": message,
        }
