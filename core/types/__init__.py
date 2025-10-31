"""
core/types package

This package contains type definitions for various components of the project.
"""

from .agent_config import AgentConfig
from .models import (
    ModelConfig,
    create_researcher_config,
    # Predefined model configurations
    CLAUDE_BASIC,
    CLAUDE_WITH_REASONING,
    O3_HIGH,
    O3_MEDIUM,
    O3_LOW,
    O4_MINI_HIGH,
    O4_MINI_MEDIUM,
    O4_MINI_LOW,
    GPT4_1_DEFAULT,
    GPT4_1_CREATIVE,
    GPT4_1_PRECISE,
    DEEPSEEK_REASONER,
    DEEPSEEK_CHAT,
    GEMINI_FLASH,
    GEMINI_PRO
) 