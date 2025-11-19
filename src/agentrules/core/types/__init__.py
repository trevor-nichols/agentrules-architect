"""
core/types package

This package contains type definitions for various components of the project.
"""

from .agent_config import AgentConfig
from .models import (
    # Predefined model configurations
    CLAUDE_BASIC,
    CLAUDE_WITH_REASONING,
    DEEPSEEK_CHAT,
    DEEPSEEK_REASONER,
    GEMINI_FLASH,
    GEMINI_FLASH_DYNAMIC,
    GEMINI_PRO,
    GEMINI_3_PRO_PREVIEW,
    GPT4_1_CREATIVE,
    GPT4_1_DEFAULT,
    GPT4_1_PRECISE,
    O3_HIGH,
    O3_LOW,
    O3_MEDIUM,
    O4_MINI_HIGH,
    O4_MINI_LOW,
    O4_MINI_MEDIUM,
    ModelConfig,
    create_researcher_config,
)

__all__ = [
    "AgentConfig",
    "CLAUDE_BASIC",
    "CLAUDE_WITH_REASONING",
    "DEEPSEEK_CHAT",
    "DEEPSEEK_REASONER",
    "GEMINI_FLASH",
    "GEMINI_FLASH_DYNAMIC",
    "GEMINI_PRO",
    "GEMINI_3_PRO_PREVIEW",
    "GPT4_1_CREATIVE",
    "GPT4_1_DEFAULT",
    "GPT4_1_PRECISE",
    "O3_HIGH",
    "O3_LOW",
    "O3_MEDIUM",
    "O4_MINI_HIGH",
    "O4_MINI_LOW",
    "O4_MINI_MEDIUM",
    "ModelConfig",
    "create_researcher_config",
]
