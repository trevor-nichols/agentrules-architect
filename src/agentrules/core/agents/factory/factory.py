"""
core/agents/factory/factory.py

This module provides factory functions for creating architect instances based on configuration.
It centralizes the instantiation logic for different types of agents.
"""

from agentrules.config.agents import MODEL_CONFIG
from agentrules.core.types.models import ModelConfig, create_researcher_config

from ..base import BaseArchitect, ModelProvider


class ArchitectFactory:
    """
    A factory for creating instances of architect agents.
    """
    @staticmethod
    def create_architect(
        model_config: ModelConfig,
        name: str,
        role: str,
        responsibilities: list[str],
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
            "tools_config": model_config.tools_config,
            "model_config": model_config,
        }
        text_verbosity = getattr(model_config, "text_verbosity", None)

        # Lazy import provider classes to avoid importing SDKs at module import time
        if provider == ModelProvider.ANTHROPIC:
            from ..anthropic import AnthropicArchitect  # noqa: E402
            return AnthropicArchitect(**common_args)
        elif provider == ModelProvider.OPENAI:
            from ..openai import OpenAIArchitect  # noqa: E402
            return OpenAIArchitect(
                temperature=model_config.temperature,
                text_verbosity=text_verbosity,
                **common_args
            )
        elif provider == ModelProvider.DEEPSEEK:
            from ..deepseek import DeepSeekArchitect  # noqa: E402
            return DeepSeekArchitect(**common_args)
        elif provider == ModelProvider.GEMINI:
            from ..gemini import GeminiArchitect  # noqa: E402
            return GeminiArchitect(**common_args)
        elif provider == ModelProvider.XAI:
            from ..xai import XaiArchitect  # noqa: E402
            return XaiArchitect(**common_args)
        else:
            raise ValueError(f"Unknown model provider: {provider}")

def get_architect_for_phase(
    phase: str,
    name: str | None = None,
    role: str | None = None,
    responsibilities: list[str] | None = None,
    prompt_template: str | None = None
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
    responsibilities: list[str],
    prompt_template: str
) -> BaseArchitect:
    """
    Creates a specialized 'Researcher' architect with tool-using capabilities.
    """
    base_config = MODEL_CONFIG.get("researcher")
    if not base_config:
        raise ValueError("No model configuration found for 'researcher'")

    researcher_config = create_researcher_config(base_config)

    return ArchitectFactory.create_architect(
        model_config=researcher_config,
        name=name,
        role=role,
        responsibilities=responsibilities,
        prompt_template=prompt_template
    )
