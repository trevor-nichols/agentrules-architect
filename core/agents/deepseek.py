import os
import logging
from typing import Dict, Optional, List, Any
import json
import asyncio
from openai import OpenAI

# Import the base classes
from .base import BaseArchitect, ModelProvider, ReasoningMode

# Set up logging
logger = logging.getLogger("project_extractor")

# Placeholder for the DeepSeek client import
# In actual implementation, you would import the appropriate client
# import deepseek

class DeepSeekArchitect(BaseArchitect):
    """
    Architect class for interacting with DeepSeek models.
    
    This class implements the BaseArchitect abstract class to provide
    methods for using both DeepSeek-Chat and DeepSeek-Reasoner models.
    
    The API is OpenAI-compatible. 'deepseek-chat' supports tool calling,
    while 'deepseek-reasoner' provides a 'reasoning_content' field.
    """
    
    def __init__(
        self, 
        model_name: str = "deepseek-chat",
        reasoning: ReasoningMode = ReasoningMode.DISABLED,
        temperature: Optional[float] = None,
        name: Optional[str] = None,
        role: Optional[str] = None,
        responsibilities: Optional[List[str]] = None,
        prompt_template: Optional[str] = None,
        base_url: str = "https://api.deepseek.com",
        tools_config: Optional[Dict] = None
    ):
        """
        Initialize a DeepSeek architect.
        
        Args:
            model_name: The DeepSeek model to use (e.g., "deepseek-chat", "deepseek-reasoner")
            reasoning: Enabled for "deepseek-reasoner", disabled otherwise.
            temperature: Not supported for DeepSeek models.
            name: Optional name of the architect 
            role: Optional role description
            responsibilities: Optional list of responsibilities
            prompt_template: Optional custom prompt template
            base_url: The base URL for the DeepSeek API
            tools_config: Optional configuration for tools the model can use.
        """
        # Set reasoning mode based on model
        if model_name == "deepseek-reasoner":
            reasoning = ReasoningMode.ENABLED
        else:
            reasoning = ReasoningMode.DISABLED
        
        temperature = None  # Not supported by DeepSeek models
        
        super().__init__(
            provider=ModelProvider.DEEPSEEK,
            model_name=model_name,
            reasoning=reasoning,
            temperature=temperature,
            name=name,
            role=role,
            responsibilities=responsibilities,
            tools_config=tools_config
        )
        self.prompt_template = prompt_template or self._get_default_prompt_template()
        self.base_url = base_url
        
        # Setup DeepSeek client (using OpenAI SDK)
        self.client = OpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY"),
            base_url=self.base_url
        )

    def _get_default_prompt_template(self) -> str:
        """Get the default prompt template for DeepSeek models."""
        return """You are {agent_name}, a code architecture analyst with expertise in {agent_role}.

Your responsibilities:
{agent_responsibilities}

Please analyze the following context and provide a detailed analysis:

Context:
{context}

Provide your analysis in a structured format with clear sections and actionable insights.
"""

    def format_prompt(self, context: Dict[str, Any]) -> str:
        """Format the analysis prompt with the provided context."""
        responsibilities_text = "\n".join([f"- {r}" for r in self.responsibilities]) if self.responsibilities else "Analyzing code architecture and patterns"
        
        return self.prompt_template.format(
            agent_name=self.name or "DeepSeek Architect",
            agent_role=self.role or "code architecture analysis",
            agent_responsibilities=responsibilities_text,
            context=json.dumps(context, indent=2)
        )
    
    def _get_api_parameters(self, messages: List[Dict], tools: Optional[List[Any]] = None) -> Dict:
        """
        Get the API parameters for a DeepSeek model.
        
        Args:
            messages: The messages to send to the model
            tools: Optional list of tools for function calling
            
        Returns:
            Dictionary of API parameters
        """
        params = {
            "model": self.model_name,
            "messages": messages,
        }
        
        if self.model_name == "deepseek-reasoner":
            params["max_tokens"] = 4000
        
        # Add tools if provided (both models support this)
        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"
            
        return params

    async def analyze(self, context: Dict, tools: Optional[List[Any]] = None) -> Dict:
        """
        Perform analysis on the provided context using a DeepSeek model.
        
        Args:
            context: Dictionary containing the information to analyze
            tools: Optional list of tools for function calling.
            
        Returns:
            Dictionary containing the analysis results, reasoning, and/or tool calls.
        """
        try:
            # Check if context contains a formatted prompt
            if "formatted_prompt" in context:
                content = context["formatted_prompt"]
            else:
                content = self.format_prompt(context)
            
            # Create messages format
            messages = [{"role": "user", "content": content}]
            
            # Determine which tools to use
            final_tools = None
            # Only enable tools for non-reasoner model
            if self.model_name != "deepseek-reasoner":
                if tools or (self.tools_config and self.tools_config.get("enabled", False)):
                    tool_list = tools or self.tools_config.get("tools", [])
                    if tool_list:
                        from core.agent_tools.tool_manager import ToolManager
                        # DeepSeek is OpenAI compatible, ToolManager should handle this
                        final_tools = ToolManager.get_provider_tools(tool_list, ModelProvider.DEEPSEEK)

            # Get API parameters, passing tools if available.
            params = self._get_api_parameters(messages, tools=final_tools)
            
            # Get the model configuration name
            from core.utils.model_config_helper import get_model_config_name
            model_config_name = get_model_config_name(self)
            
            agent_name = self.name or f"DeepSeek {self.model_name.replace('-', ' ').title()}"
            logger.info(f"[bold teal]{agent_name}:[/bold teal] Sending request to {self.model_name} (Config: {model_config_name})" +
                        (" with tools enabled" if tools else ""))
            
            # Call the DeepSeek API via OpenAI SDK
            response = self.client.chat.completions.create(**params)
            
            logger.info(f"[bold green]{agent_name}:[/bold green] Received response from {self.model_name}")
            
            message = response.choices[0].message
            
            # Prepare results dictionary
            results = {
                "agent": agent_name,
                "findings": message.content,
                "reasoning": None,
                "tool_calls": None
            }

            # Check for reasoning content (for deepseek-reasoner)
            if hasattr(message, 'reasoning_content') and message.reasoning_content:
                results["reasoning"] = message.reasoning_content

            # Check for tool calls (for deepseek-chat)
            if message.tool_calls:
                logger.info(f"[bold teal]{agent_name}:[/bold teal] Model requested tool call(s).")
                results["tool_calls"] = [
                    {
                        "id": call.id,
                        "type": call.type,
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments  # Arguments are a JSON string
                        }
                    } 
                    for call in message.tool_calls if call.type == 'function'
                ]
                # Clear findings if only tool calls are present
                if not message.content:
                    results["findings"] = None

            return results
        except Exception as e:
            agent_name = self.name or "DeepSeek Architect"
            logger.error(f"[bold red]Error in {agent_name}:[/bold red] {str(e)}")
            return {
                "agent": agent_name,
                "error": str(e)
            }
    
    # Phase-specific methods
    async def create_analysis_plan(self, phase1_results: Dict, prompt: Optional[str] = None) -> Dict:
        """Create an analysis plan based on Phase 1 results."""
        context = {"phase1_results": phase1_results, "formatted_prompt": prompt} if prompt else {"phase1_results": phase1_results}
        result = await self.analyze(context)
        
        return {
            "agent": self.name or "DeepSeek Architect",
            "plan": result.get("findings", "No plan generated"),
            "reasoning": result.get("reasoning"),
            "error": result.get("error")
        }
    
    async def synthesize_findings(self, phase3_results: Dict, prompt: Optional[str] = None) -> Dict:
        """Synthesize findings from Phase 3."""
        context = {"phase3_results": phase3_results, "formatted_prompt": prompt} if prompt else {"phase3_results": phase3_results}
        result = await self.analyze(context)
        
        return {
            "agent": self.name or "DeepSeek Architect",
            "analysis": result.get("findings", "No synthesis generated"),
            "reasoning": result.get("reasoning"),
            "error": result.get("error")
        }
    
    async def final_analysis(self, consolidated_report: Dict, prompt: Optional[str] = None) -> Dict:
        """Provide final analysis on the consolidated report."""
        context = {"consolidated_report": consolidated_report, "formatted_prompt": prompt} if prompt else {"consolidated_report": consolidated_report}
        result = await self.analyze(context)
        
        return {
            "agent": self.name or "DeepSeek Architect",
            "analysis": result.get("findings", "No final analysis generated"),
            "reasoning": result.get("reasoning"),
            "error": result.get("error")
        }
    
    async def consolidate_results(self, all_results: Dict, prompt: Optional[str] = None) -> Dict:
        """Consolidate all phase results."""
        context = {"all_results": all_results, "formatted_prompt": prompt} if prompt else {"all_results": all_results}
        result = await self.analyze(context)
        
        return {
            "phase": "Consolidation",
            "report": result.get("findings", "No report generated"),
            "reasoning": result.get("reasoning"),
            "error": result.get("error")
        }

# Simpler Agent class for basic usage
class DeepSeekAgent:
    """
    Agent class for interacting with DeepSeek Reasoner model.
    
    This class provides a simpler interface for DeepSeek Reasoner focused on
    specific analysis tasks.
    """
    
    def __init__(
        self, 
        name: Optional[str] = None,
        role: Optional[str] = None,
        responsibilities: Optional[List[str]] = None
    ):
        """
        Initialize a DeepSeek Reasoner agent.
        
        Args:
            name: Optional agent name
            role: Optional role description
            responsibilities: Optional list of responsibilities
        """
        # Create the architect instance
        self.architect = DeepSeekArchitect(
            name=name,
            role=role,
            responsibilities=responsibilities
        )
    
    async def analyze(self, context: Dict) -> Dict:
        """Analyze the provided context."""
        return await self.architect.analyze(context)
        
    async def create_analysis_plan(self, phase1_results: Dict, prompt: Optional[str] = None) -> Dict:
        """Create an analysis plan based on Phase 1 results."""
        return await self.architect.create_analysis_plan(phase1_results, prompt)
    
    async def synthesize_findings(self, phase3_results: Dict, prompt: Optional[str] = None) -> Dict:
        """Synthesize findings from Phase 3."""
        return await self.architect.synthesize_findings(phase3_results, prompt)
    
    async def final_analysis(self, consolidated_report: Dict, prompt: Optional[str] = None) -> Dict:
        """Provide final analysis on the consolidated report."""
        return await self.architect.final_analysis(consolidated_report, prompt)
