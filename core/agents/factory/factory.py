"""
core/agents/factory/factory.py

This module provides factory functions for creating architect instances based on configuration.
It centralizes the instantiation logic for different types of agents.
"""

from typing import List, Optional
from ..base import BaseArchitect, ModelProvider
from core.types.models import ModelConfig, create_researcher_config
from config.agents import MODEL_CONFIG

class ArchitectFactory:
    """
    A factory for creating instances of architect agents.
    """
    @staticmethod
    def create_architect(
        model_config: ModelConfig,
        name: str,
        role: str,
        responsibilities: List[str],
        prompt_template: str
    ) -> BaseArchitect:
        """
        Create an architect instance based on the provided model configuration.
        """
        provider = model_config.provider
        
        common_args = {
            "model_name": model_config.model_name,
            "reasoning": model_config.reasoning,
            "name": name,
            "role": role,
            "responsibilities": responsibilities,
            "prompt_template": prompt_template,
            "tools_config": model_config.tools_config
        }

        # Lazy import provider classes to avoid importing SDKs at module import time
        if provider == ModelProvider.ANTHROPIC:
            from ..anthropic import AnthropicArchitect  # noqa: WPS433
            return AnthropicArchitect(**common_args)
        elif provider == ModelProvider.OPENAI:
            from ..openai import OpenAIArchitect  # noqa: WPS433
            return OpenAIArchitect(temperature=model_config.temperature, **common_args)
        elif provider == ModelProvider.DEEPSEEK:
            from ..deepseek import DeepSeekArchitect  # noqa: WPS433
            return DeepSeekArchitect(**common_args)
        elif provider == ModelProvider.GEMINI:
            from ..gemini import GeminiArchitect  # noqa: WPS433
            return GeminiArchitect(**common_args)
        else:
            raise ValueError(f"Unknown model provider: {provider}")

def get_architect_for_phase(
    phase: str,
    name: Optional[str] = None,
    role: Optional[str] = None,
    responsibilities: Optional[List[str]] = None,
    prompt_template: Optional[str] = None
) -> BaseArchitect:
    """
    Get the appropriate architect for a given phase based on the MODEL_CONFIG.

    Supports two usage modes:
    - Full persona mode: provide name/role/responsibilities/prompt_template
    - Phase-only mode: provide only phase; factory supplies sensible defaults
    """
    model_config = MODEL_CONFIG.get(phase)
    if not model_config:
        raise ValueError(f"No model configuration found for phase: {phase}")

    # Provide sensible defaults when caller doesn't supply a persona
    default_name = name or f"{phase.title()} Architect"
    default_role = role or "analyzing the project"
    default_responsibilities = responsibilities or []
    default_prompt = (
        prompt_template
        or (
            "You are {agent_name}, responsible for {agent_role}.\n\n"
            "Analyze the following context and provide a clear, structured answer.\n\n{context}"
        )
    )

    return ArchitectFactory.create_architect(
        model_config=model_config,
        name=default_name,
        role=default_role,
        responsibilities=default_responsibilities,
        prompt_template=default_prompt
    )

def get_researcher_architect(
    name: str,
    role: str,
    responsibilities: List[str],
    prompt_template: str
) -> BaseArchitect:
    """
    Creates a specialized 'Researcher' architect with tool-using capabilities.
    """
    base_config = MODEL_CONFIG.get("researcher")
    if not base_config:
        raise ValueError("No model configuration found for 'researcher'")

    researcher_config = create_researcher_config(
        provider=base_config.provider,
        model_name=base_config.model_name
    )

    return ArchitectFactory.create_architect(
        model_config=researcher_config,
        name=name,
        role=role,
        responsibilities=responsibilities,
        prompt_template=prompt_template
    )
