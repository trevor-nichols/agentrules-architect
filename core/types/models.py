"""
core/types/models.py

This module defines the model configuration types and predefined model configurations
used throughout the CursorRules Architect system.
"""

from typing import Dict, Any, NamedTuple, Optional, List
from core.agents.base import ModelProvider, ReasoningMode
from core.types.tool_config import ToolConfig

# ====================================================
# Model Configuration Types
# This section defines types for model configuration.
# ====================================================

class ModelConfig(NamedTuple):
    """Configuration for a specific AI model."""
    provider: ModelProvider
    model_name: str
    reasoning: ReasoningMode = ReasoningMode.DISABLED
    temperature: Optional[float] = None  # For temperature-based models like gpt-4.1
    tools_config: Optional[ToolConfig] = None  # Tool configuration for this model

# ====================================================
# Predefined Model Configurations
# These are shorthand configurations that can be referenced in the MODEL_CONFIG.
# ====================================================

CLAUDE_BASIC = ModelConfig(
    provider=ModelProvider.ANTHROPIC,
    model_name="claude-sonnet-4-20250514",
    reasoning=ReasoningMode.DISABLED,
    tools_config={"enabled": False, "tools": None}
)

CLAUDE_WITH_REASONING = ModelConfig(
    provider=ModelProvider.ANTHROPIC,
    model_name="claude-sonnet-4-20250514",
    reasoning=ReasoningMode.ENABLED,
    tools_config={"enabled": False, "tools": None}
)

# The `CLAUDE_WITH_TOOLS` example is replaced by the factory function below
# to create a more flexible, provider-agnostic "Researcher" configuration.

def create_researcher_config(provider: ModelProvider, model_name: str) -> ModelConfig:
    """
    Creates a 'Researcher' agent configuration for a specific provider and model.

    This factory function standardizes the creation of a research-oriented agent,
    which comes pre-configured to use tools (like web search) and has reasoning
    enabled by default.

    Args:
        provider: The model provider (e.g., ModelProvider.ANTHROPIC).
        model_name: The specific model name (e.g., "claude-sonnet-4-20250514").

    Returns:
        A ModelConfig instance configured for research.
    """
    return ModelConfig(
        provider=provider,
        model_name=model_name,
        reasoning=ReasoningMode.ENABLED,  # Reasoning is crucial for research
        tools_config={"enabled": True, "tools": None}  # Ready for tools like web_search
    )

# O1 configurations with different reasoning levels
O3_HIGH = ModelConfig(
    provider=ModelProvider.OPENAI,
    model_name="o3",
    reasoning=ReasoningMode.HIGH,
    tools_config={"enabled": False, "tools": None}
)

O3_MEDIUM = ModelConfig(
    provider=ModelProvider.OPENAI,
    model_name="o3",
    reasoning=ReasoningMode.MEDIUM,
    tools_config={"enabled": False, "tools": None}
)

O3_LOW = ModelConfig(
    provider=ModelProvider.OPENAI,
    model_name="o3",
    reasoning=ReasoningMode.LOW,
    tools_config={"enabled": False, "tools": None}
)

# O4-mini configurations with different reasoning levels
O4_MINI_HIGH = ModelConfig(
    provider=ModelProvider.OPENAI,
    model_name="o4-mini",
    reasoning=ReasoningMode.HIGH,
    tools_config={"enabled": False, "tools": None}
)

O4_MINI_MEDIUM = ModelConfig(
    provider=ModelProvider.OPENAI,
    model_name="o4-mini",
    reasoning=ReasoningMode.MEDIUM,
    tools_config={"enabled": False, "tools": None}
)

O4_MINI_LOW = ModelConfig(
    provider=ModelProvider.OPENAI,
    model_name="o4-mini",
    reasoning=ReasoningMode.LOW,
    tools_config={"enabled": False, "tools": None}
)

# gpt-4.1 configurations with different temperature values
GPT4_1_DEFAULT = ModelConfig(
    provider=ModelProvider.OPENAI,
    model_name="gpt-4.1",
    reasoning=ReasoningMode.TEMPERATURE,
    temperature=0.7,  # Default temperature
    tools_config={"enabled": False, "tools": None}
)

GPT4_1_CREATIVE = ModelConfig(
    provider=ModelProvider.OPENAI,
    model_name="gpt-4.1",
    reasoning=ReasoningMode.TEMPERATURE,
    temperature=0.9,  # Higher temperature for more creative outputs
    tools_config={"enabled": False, "tools": None}
)

GPT4_1_PRECISE = ModelConfig(
    provider=ModelProvider.OPENAI,
    model_name="gpt-4.1",
    reasoning=ReasoningMode.TEMPERATURE,
    temperature=0.2,  # Lower temperature for more precise/deterministic outputs
    tools_config={"enabled": False, "tools": None}
)

# DeepSeek configurations
DEEPSEEK_REASONER = ModelConfig(
    provider=ModelProvider.DEEPSEEK,
    model_name="deepseek-reasoner",
    reasoning=ReasoningMode.ENABLED,  # Always enabled for reasoner
    tools_config={"enabled": False, "tools": None}
)

DEEPSEEK_CHAT = ModelConfig(
    provider=ModelProvider.DEEPSEEK,
    model_name="deepseek-chat",
    reasoning=ReasoningMode.DISABLED,
    tools_config={"enabled": False, "tools": None}
)

# Google Gemini Models
GEMINI_FLASH = ModelConfig(
    provider=ModelProvider.GEMINI,
    model_name="gemini-2.5-flash",
    reasoning=ReasoningMode.DISABLED,
    tools_config={"enabled": False, "tools": None}
)

GEMINI_PRO = ModelConfig(
    provider=ModelProvider.GEMINI,
    model_name="gemini-2.5-pro",
    reasoning=ReasoningMode.ENABLED,
    tools_config={"enabled": False, "tools": None}
) 

# -----------------------------------------------------------------------------
# Backward-compatibility aliases for older test suites and integrations
# These names map to the current model presets to avoid breaking older imports.
# -----------------------------------------------------------------------------
# Older naming used "O1" to refer to OpenAI's reasoning model; map to O3 presets.
O1_HIGH = O3_HIGH  # Deprecated alias
# Some suites used "O3_MINI_HIGH" which corresponds to today's O4-mini high effort
O3_MINI_HIGH = O4_MINI_HIGH  # Deprecated alias
