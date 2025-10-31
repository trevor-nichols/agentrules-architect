"""
core/agents/openai.py

This module provides the OpenAIArchitect class for interacting with OpenAI models.
It handles the creation and execution of agent-based analysis using OpenAI models.

This module is used by the main analysis process to perform specialized analysis tasks.
"""

# ====================================================
# Importing Necessary Libraries
# This section imports all the required libraries and modules.
# These are external code packages that provide extra functions.
# ====================================================

import json
import logging
from typing import Any, Mapping, Optional, Tuple

from openai import OpenAI

from config.prompts.final_analysis_prompt import format_final_analysis_prompt
from config.prompts.phase_2_prompts import format_phase2_prompt
from config.prompts.phase_4_prompts import format_phase4_prompt
from core.agents.base import BaseArchitect, ModelProvider, ReasoningMode

# ====================================================
# Initialize OpenAI Client
# This section sets up the connection to the OpenAI API.
# It creates a client object that allows us to interact with OpenAI.
# ====================================================

# Initialize the OpenAI client
openai_client = OpenAI()

# ====================================================
# Setup Logger
# This part sets up a logger to track and record events.
# It helps in debugging and monitoring the application.
# ====================================================

# Get logger
logger = logging.getLogger("project_extractor")

# ====================================================
# Define the OpenAIArchitect Class
# This section defines a class called OpenAIArchitect.
# A class is like a blueprint for creating objects that have specific functions and data.
# ====================================================

class OpenAIArchitect(BaseArchitect):
    """
    Architect class for interacting with OpenAI models.

    This class provides a structured way to create specialized architects that use
    OpenAI models for different analysis tasks. It now supports tool usage.
    """

    # ====================================================
    # Initialization Function (__init__)
    # This function is called when a new OpenAIArchitect object is created.
    # It sets the initial state of the architect.
    # ====================================================
    def __init__(
        self,
        model_name: str = "o3",
        reasoning: Optional[ReasoningMode] = None,
        temperature: Optional[float] = None,
        name: Optional[str] = None,
        role: Optional[str] = None,
        responsibilities: Optional[list[str]] = None,
        prompt_template: Optional[str] = None,
        tools_config: Optional[dict] = None,
        text_verbosity: Optional[str] = None
    ):
        """
        Initialize an OpenAI architect with a specific model.

        Args:
            model_name: The OpenAI model to use (default: "o3")
            reasoning: Reasoning mode (defaults based on model type)
            temperature: Temperature value for temperature-based models like gpt-4.1
            name: Optional name for specialized roles
            role: Optional role description
            responsibilities: Optional list of responsibilities
            prompt_template: Optional custom prompt template to use
            tools_config: Optional configuration for tools the model can use
        """
        effective_reasoning: ReasoningMode
        # Set default reasoning based on model
        if reasoning is None:
            if model_name in ["o3", "o4-mini"]:
                effective_reasoning = ReasoningMode.HIGH
            elif model_name == "gpt-4.1":
                effective_reasoning = ReasoningMode.TEMPERATURE
            elif model_name.startswith("gpt-5"):
                effective_reasoning = ReasoningMode.MEDIUM
            else:
                effective_reasoning = ReasoningMode.DISABLED
        else:
            effective_reasoning = reasoning

        # Set default temperature for gpt-4.1 if not specified
        if (
            model_name == "gpt-4.1"
            and temperature is None
            and effective_reasoning == ReasoningMode.TEMPERATURE
        ):
            temperature = 0.7  # Default temperature for gpt-4.1

        super().__init__(
            provider=ModelProvider.OPENAI,
            model_name=model_name,
            reasoning=effective_reasoning,
            temperature=temperature,
            name=name,
            role=role,
            responsibilities=responsibilities,
            tools_config=tools_config
        )

        # Store the prompt template
        self.prompt_template = prompt_template or self._get_default_prompt_template()
        self.text_verbosity = text_verbosity
        self._use_responses_api = self._should_use_responses_api(model_name)

    def _get_default_prompt_template(self) -> str:
        """Get the default prompt template for the agent."""
        return """You are {agent_name}, responsible for {agent_role}.

Your specific responsibilities are:
{agent_responsibilities}

Analyze this project context and provide a detailed report focused on your domain:

{context}

Format your response as a structured report with clear sections and findings."""

    @staticmethod
    def _should_use_responses_api(model_name: str) -> bool:
        """Determine if the Responses API should be used for the given model."""
        return model_name.startswith("gpt-5")

    def format_prompt(self, context: dict) -> str:
        """
        Format the prompt template with the agent's information and context.

        Args:
            context: Dictionary containing the context for analysis

        Returns:
            Formatted prompt string
        """
        responsibilities_str = "\n".join(f"- {r}" for r in self.responsibilities) if self.responsibilities else ""
        context_str = json.dumps(context, indent=2) if isinstance(context, dict) else str(context)

        return self.prompt_template.format(
            agent_name=self.name or "OpenAI Architect",
            agent_role=self.role or "analyzing the project",
            agent_responsibilities=responsibilities_str,
            context=context_str
        )

    # ====================================================
    # Helper Methods
    # These methods help with common tasks needed by the public methods.
    # ====================================================

    def _prepare_request(self, content: str, tools: Optional[list[Any]] = None) -> Tuple[str, dict[str, Any]]:
        """Prepare the API request payload and select the correct endpoint."""
        if self._use_responses_api:
            params: dict[str, Any] = {
                "model": self.model_name,
                "input": content
            }

            reasoning_payload = self._build_responses_reasoning_payload()
            if reasoning_payload:
                params["reasoning"] = reasoning_payload

            text_config = self._build_text_config()
            if text_config:
                params["text"] = text_config

            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"

            return "responses", params

        params = {
            "model": self.model_name,
            "messages": [{
                "role": "user",
                "content": content
            }]
        }

        if self.model_name in ["o3", "o4-mini"]:
            reasoning_mode = self.reasoning
            if reasoning_mode == ReasoningMode.ENABLED:
                params["reasoning_effort"] = "high"
            elif reasoning_mode == ReasoningMode.MINIMAL:
                params["reasoning_effort"] = ReasoningMode.LOW.value
            elif reasoning_mode in [ReasoningMode.LOW, ReasoningMode.MEDIUM, ReasoningMode.HIGH]:
                params["reasoning_effort"] = reasoning_mode.value
            else:
                params["reasoning_effort"] = "medium"
        elif self.model_name == "gpt-4.1" or self.reasoning == ReasoningMode.TEMPERATURE:
            if self.temperature is not None:
                params["temperature"] = self.temperature

        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"

        return "chat", params

    def _build_responses_reasoning_payload(self) -> Optional[dict[str, str]]:
        """Build reasoning payload for the Responses API if applicable."""
        if self.reasoning in [ReasoningMode.MINIMAL, ReasoningMode.LOW, ReasoningMode.MEDIUM, ReasoningMode.HIGH]:
            return {"effort": self.reasoning.value}
        if self.reasoning == ReasoningMode.ENABLED:
            return {"effort": ReasoningMode.MEDIUM.value}
        return None

    def _build_text_config(self) -> Optional[dict[str, Any]]:
        """Construct text output configuration for Responses API."""
        if not self.text_verbosity:
            return None
        return {"verbosity": self.text_verbosity}

    @staticmethod
    def _as_dict(obj: Any) -> dict[str, Any]:
        """Best-effort conversion of OpenAI SDK objects to plain dicts."""
        if isinstance(obj, dict):
            return obj
        for attr in ("model_dump", "to_dict", "dict"):
            method = getattr(obj, attr, None)
            if not callable(method):
                continue

            result: Any
            try:
                result = method()
            except TypeError:
                try:
                    result = method(mode="python")  # type: ignore[arg-type]
                except Exception:
                    continue
            except Exception:
                continue

            if isinstance(result, Mapping):
                return dict(result)
            if hasattr(result, "__dict__"):
                return {
                    key: value
                    for key, value in vars(result).items()
                    if not key.startswith("_")
                }

        if hasattr(obj, "__dict__"):
            return {
                key: value
                for key, value in obj.__dict__.items()
                if not key.startswith("_")
            }
        return {}

    def _parse_model_response(self, response: Any, api_type: str) -> Tuple[Optional[str], Optional[list[dict[str, Any]]]]:
        """Normalize the response payload across Chat Completions and Responses API."""
        if api_type == "responses":
            return self._parse_responses_output(response)
        return self._parse_chat_output(response)

    def _execute_request(self, api_type: str, params: dict[str, Any]) -> Any:
        """Dispatch the prepared payload to the appropriate OpenAI endpoint."""
        if api_type == "responses":
            return openai_client.responses.create(**params)
        return openai_client.chat.completions.create(**params)

    def _parse_chat_output(self, response: Any) -> Tuple[Optional[str], Optional[list[dict[str, Any]]]]:
        message = response.choices[0].message
        findings = message.content or None
        tool_calls = None
        if message.tool_calls:
            tool_calls = [
                {
                    "id": call.id,
                    "type": call.type,
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments
                    }
                }
                for call in message.tool_calls
                if getattr(call, "type", None) == "function"
            ] or None
        return findings, tool_calls

    def _parse_responses_output(self, response: Any) -> Tuple[Optional[str], Optional[list[dict[str, Any]]]]:
        response_dict = self._as_dict(response)
        output_items = response_dict.get("output", []) or []
        text_segments: list[str] = []
        tool_calls: list[dict[str, Any]] = []

        for item in output_items:
            item_dict = self._as_dict(item)
            if item_dict.get("type") != "message":
                continue
            for part in item_dict.get("content", []) or []:
                part_dict = self._as_dict(part)
                part_type = part_dict.get("type")
                if part_type == "output_text":
                    text_value = part_dict.get("text")
                    if text_value:
                        text_segments.append(str(text_value))
                elif part_type in {"function_call", "custom_tool_call"}:
                    normalized = self._normalize_tool_call(part_dict)
                    if normalized:
                        tool_calls.append(normalized)

        if not text_segments:
            aggregated = response_dict.get("output_text") or getattr(response, "output_text", None)
            if aggregated:
                text_segments.append(str(aggregated))

        findings = "\n".join(text_segments).strip() if text_segments else None
        normalized_tool_calls = tool_calls or None
        return findings, normalized_tool_calls

    @staticmethod
    def _normalize_tool_call(part_dict: Mapping[str, Any]) -> Optional[dict[str, Any]]:
        """Convert Responses API tool call parts into the legacy tool_call schema."""
        part_type = part_dict.get("type")
        call_id = part_dict.get("id") or part_dict.get("call_id")
        if part_type == "function_call":
            return {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": part_dict.get("name"),
                    "arguments": part_dict.get("arguments", "")
                }
            }
        if part_type == "custom_tool_call":
            return {
                "id": call_id,
                "type": "custom",
                "name": part_dict.get("name"),
                "input": part_dict.get("input")
            }
        return None

    # ====================================================
    # Analyze Method
    # This method implements the abstract analyze method from BaseArchitect.
    # ====================================================

    async def analyze(self, context: dict, tools: Optional[list[Any]] = None) -> dict:
        """
        Run analysis using the OpenAI model, potentially using tools.

        Args:
            context: Dictionary containing the context for analysis
            tools: Optional list of tools the model can use.
                   Follows OpenAI's tool definition format.

        Returns:
            Dictionary containing the analysis results, potential tool calls, or error information
        """
        try:
            # Check if the context already contains a formatted prompt
            if "formatted_prompt" in context:
                content = context["formatted_prompt"]
            else:
                # Format the prompt using the template
                content = self.format_prompt(context)

            # Determine which tools to use
            final_tools = None
            if tools or (self.tools_config and self.tools_config.get("enabled", False)):
                tool_list = tools or self.tools_config.get("tools", [])
                if tool_list:
                    from core.agent_tools.tool_manager import ToolManager
                    final_tools = ToolManager.get_provider_tools(tool_list, ModelProvider.OPENAI)

            # Build request payload and endpoint selection
            api_type, params = self._prepare_request(content, tools=final_tools)

            # Try to get the model config name
            from core.utils.model_config_helper import get_model_config_name
            model_config_name = get_model_config_name(self)

            agent_name = self.name or "OpenAI Architect"
            detail_suffix = " with tools enabled" if final_tools else ""
            api_label = "Responses API" if api_type == "responses" else "Chat Completions API"
            logger.info(
                f"[bold blue]{agent_name}:[/bold blue] Sending request to {self.model_name} "
                f"via {api_label} (Config: {model_config_name}){detail_suffix}"
            )

            # Call the OpenAI API
            response = self._execute_request(api_type, params)

            logger.info(
                f"[bold green]{agent_name}:[/bold green] Received response from {self.model_name}"
            )

            findings, tool_calls = self._parse_model_response(response, api_type)

            results = {
                "agent": agent_name,
                "findings": findings,
                "tool_calls": tool_calls
            }

            if tool_calls:
                logger.info(f"[bold blue]{agent_name}:[/bold blue] Model requested tool call(s).")

            return results
        except Exception as e:
            agent_name = self.name or "OpenAI Architect"
            logger.error(f"[bold red]Error in {agent_name}:[/bold red] {str(e)}")
            return {
                "agent": agent_name,
                "error": str(e)
            }

    # ------------------------------------
    # Phase 2: Analysis Planning
    # ------------------------------------
    async def create_analysis_plan(self, phase1_results: dict, prompt: Optional[str] = None) -> dict:
        """
        Create an analysis plan based on Phase 1 results.
        (Does not currently support tool usage for this specific task)

        Args:
            phase1_results: Dictionary containing the results from Phase 1
            prompt: Optional custom prompt to use instead of the default

        Returns:
            Dictionary containing the analysis plan
        """
        try:
            # Use the provided prompt or the default one
            content = prompt or format_phase2_prompt(phase1_results)

            api_type, params = self._prepare_request(content)
            response = self._execute_request(api_type, params)
            plan, _ = self._parse_model_response(response, api_type)

            return {
                "plan": plan or "No plan generated"
            }
        except Exception as e:
            logger.error(f"Error in analysis plan creation: {str(e)}")
            return {
                "error": str(e)
            }

    # ---------------------------------------
    # Phase 4: Findings Synthesis
    # ---------------------------------------
    async def synthesize_findings(self, phase3_results: dict, prompt: Optional[str] = None) -> dict:
        """
        Synthesize findings from Phase 3.
        (Does not currently support tool usage for this specific task)

        Args:
            phase3_results: Dictionary containing the results from Phase 3
            prompt: Optional custom prompt to use instead of the default

        Returns:
            Dictionary containing the synthesis
        """
        try:
            # Use the provided prompt or the default one
            content = prompt or format_phase4_prompt(phase3_results)

            api_type, params = self._prepare_request(content)
            response = self._execute_request(api_type, params)
            analysis, _ = self._parse_model_response(response, api_type)

            return {
                "analysis": analysis or "No synthesis generated"
            }
        except Exception as e:
            logger.error(f"Error in findings synthesis: {str(e)}")
            return {
                "error": str(e)
            }

    # -----------------------------------
    # Final Analysis
    # -----------------------------------
    async def final_analysis(self, consolidated_report: dict, prompt: Optional[str] = None) -> dict:
        """
        Perform final analysis on the consolidated report.
        (Does not currently support tool usage for this specific task)

        Args:
            consolidated_report: Dictionary containing the consolidated report
            prompt: Optional custom prompt to use instead of the default

        Returns:
            Dictionary containing the final analysis
        """
        try:
            # Use the provided prompt or the default one
            content = prompt or format_final_analysis_prompt(consolidated_report)

            api_type, params = self._prepare_request(content)
            response = self._execute_request(api_type, params)
            analysis, _ = self._parse_model_response(response, api_type)

            return {
                "analysis": analysis or "No final analysis generated"
            }
        except Exception as e:
            logger.error(f"Error in final analysis: {str(e)}")
            return {
                "error": str(e)
            }

    # -----------------------------------
    # Consolidate Results - Implemented for compatibility
    # -----------------------------------
    async def consolidate_results(self, all_results: dict, prompt: Optional[str] = None) -> dict:
        """
        Consolidate results from all previous phases.
        (Does not currently support tool usage for this specific task)

        This is implemented for compatibility with the base class but not the
        primary function of the OpenAI model in the current architecture.

        Args:
            all_results: Dictionary containing all phase results
            prompt: Optional custom prompt to use

        Returns:
            Dictionary containing the consolidated report
        """
        try:
            # Use the provided prompt or format a default one
            content = prompt or (
                "Consolidate these results into a comprehensive report:\n\n"
                f"{json.dumps(all_results, indent=2)}"
            )

            api_type, params = self._prepare_request(content)
            response = self._execute_request(api_type, params)
            report, _ = self._parse_model_response(response, api_type)

            return {
                "phase": "Consolidation",
                "report": report or "No report generated"
            }
        except Exception as e:
            logger.error(f"Error in consolidation: {str(e)}")
            return {
                "phase": "Consolidation",
                "error": str(e)
            }

# ====================================================
# Legacy OpenAIAgent Class
# Maintained for backward compatibility
# ====================================================

class OpenAIAgent:
    """
    Agent class for interacting with OpenAI models.

    This class provides a structured way to create specialized agents that use
    OpenAI models for different analysis tasks.

    Note: This class is maintained for backward compatibility. New code should use
    OpenAIArchitect instead.
    """

    def __init__(self, model: str = "o3", temperature: Optional[float] = None):
        """
        Initialize an OpenAI agent with a specific model.

        Args:
            model: The OpenAI model to use (default: "o3")
            temperature: Temperature value for temperature-based models like gpt-4.1
        """
        self.model = model

        # Create underlying OpenAIArchitect with appropriate reasoning mode
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

    # Note: Legacy methods don't pass 'tools' parameter
    async def create_analysis_plan(self, phase1_results: dict, prompt: Optional[str] = None) -> dict:
        """
        Create an analysis plan based on Phase 1 results using o3 model.

        Args:
            phase1_results: Dictionary containing the results from Phase 1
            prompt: Optional custom prompt to use instead of the default

        Returns:
            Dictionary containing the analysis plan and token usage
        """
        return await self._architect.create_analysis_plan(phase1_results, prompt)

    async def synthesize_findings(self, phase3_results: dict, prompt: Optional[str] = None) -> dict:
        """
        Synthesize findings from Phase 3 using o3 model.

        Args:
            phase3_results: Dictionary containing the results from Phase 3
            prompt: Optional custom prompt to use instead of the default

        Returns:
            Dictionary containing the synthesis and token usage
        """
        return await self._architect.synthesize_findings(phase3_results, prompt)

    async def final_analysis(self, consolidated_report: dict, prompt: Optional[str] = None) -> dict:
        """
        Perform final analysis on the consolidated report using o3 model.

        Args:
            consolidated_report: Dictionary containing the consolidated report
            prompt: Optional custom prompt to use instead of the default

        Returns:
            Dictionary containing the final analysis and token usage
        """
        return await self._architect.final_analysis(consolidated_report, prompt)
