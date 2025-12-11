"""
core/types/models.py

This module defines the model configuration types and predefined model configurations
used throughout the CursorRules Architect system.
"""

from typing import NamedTuple

from agentrules.core.agents.base import ModelProvider, ReasoningMode
from agentrules.core.types.tool_config import ToolConfig

# ====================================================
# Model Configuration Types
# This section defines types for model configuration.
# ====================================================

class ModelConfig(NamedTuple):
    """Configuration for a specific AI model."""
    provider: ModelProvider
    model_name: str
    reasoning: ReasoningMode = ReasoningMode.DISABLED
    temperature: float | None = None  # For temperature-based models like gpt-4.1
    tools_config: ToolConfig | None = None  # Tool configuration for this model
    text_verbosity: str | None = None  # GPT-5 family text verbosity control
    max_input_tokens: int | None = None  # Provider-advertised or conservative context window (input side)
    safety_margin_tokens: int | None = None  # Margin to reserve within the context window
    estimator_family: str | None = None  # Which estimator to use (anthropic_api, gemini_api, tiktoken, heuristic)

# ====================================================
# Predefined Model Configurations
# These are shorthand configurations that can be referenced in the MODEL_CONFIG.
# ====================================================

CLAUDE_BASIC = ModelConfig(
    provider=ModelProvider.ANTHROPIC,
    model_name="claude-sonnet-4-5",
    reasoning=ReasoningMode.DISABLED,
    tools_config={"enabled": False, "tools": None}
)

CLAUDE_WITH_REASONING = ModelConfig(
    provider=ModelProvider.ANTHROPIC,
    model_name="claude-sonnet-4-5",
    reasoning=ReasoningMode.ENABLED,
    tools_config={"enabled": False, "tools": None}
)

CLAUDE_HAIKU = ModelConfig(
    provider=ModelProvider.ANTHROPIC,
    model_name="claude-haiku-4-5",
    reasoning=ReasoningMode.DISABLED,
    tools_config={"enabled": False, "tools": None}
)

CLAUDE_HAIKU_WITH_REASONING = ModelConfig(
    provider=ModelProvider.ANTHROPIC,
    model_name="claude-haiku-4-5",
    reasoning=ReasoningMode.ENABLED,
    tools_config={"enabled": False, "tools": None}
)

CLAUDE_OPUS = ModelConfig(
    provider=ModelProvider.ANTHROPIC,
    model_name="claude-opus-4-1",
    reasoning=ReasoningMode.DISABLED,
    tools_config={"enabled": False, "tools": None}
)

CLAUDE_OPUS_WITH_REASONING = ModelConfig(
    provider=ModelProvider.ANTHROPIC,
    model_name="claude-opus-4-1",
    reasoning=ReasoningMode.ENABLED,
    tools_config={"enabled": False, "tools": None}
)

CLAUDE_OPUS_45 = ModelConfig(
    provider=ModelProvider.ANTHROPIC,
    model_name="claude-opus-4-5-20251101",
    reasoning=ReasoningMode.DISABLED,
    tools_config={"enabled": False, "tools": None}
)

CLAUDE_OPUS_45_WITH_REASONING = ModelConfig(
    provider=ModelProvider.ANTHROPIC,
    model_name="claude-opus-4-5-20251101",
    reasoning=ReasoningMode.ENABLED,
    tools_config={"enabled": False, "tools": None}
)

# The `CLAUDE_WITH_TOOLS` example is replaced by the factory function below
# to create a more flexible, provider-agnostic "Researcher" configuration.

def create_researcher_config(base_config: ModelConfig) -> ModelConfig:
    """
    Creates a 'Researcher' agent configuration for a specific provider and model.

    This factory function standardizes the creation of a research-oriented agent,
    which comes pre-configured to use tools (like web search) while respecting
    the reasoning mode chosen in the base configuration.

    Args:
        base_config: The base model configuration selected by the user.

    Returns:
        A ModelConfig instance configured for research.
    """
    return base_config._replace(
        tools_config={"enabled": True, "tools": None},
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

# xAI Grok models
GROK_4_0709 = ModelConfig(
    provider=ModelProvider.XAI,
    model_name="grok-4-0709",
    reasoning=ReasoningMode.MEDIUM,
    tools_config={"enabled": False, "tools": None}
)

GROK_4_FAST_REASONING = ModelConfig(
    provider=ModelProvider.XAI,
    model_name="grok-4-fast-reasoning",
    reasoning=ReasoningMode.MEDIUM,
    tools_config={"enabled": False, "tools": None}
)

GROK_4_FAST_NON_REASONING = ModelConfig(
    provider=ModelProvider.XAI,
    model_name="grok-4-fast-non-reasoning",
    reasoning=ReasoningMode.DISABLED,
    tools_config={"enabled": False, "tools": None}
)

GROK_CODE_FAST = ModelConfig(
    provider=ModelProvider.XAI,
    model_name="grok-code-fast-1",
    reasoning=ReasoningMode.MEDIUM,
    tools_config={"enabled": False, "tools": None}
)

# Google Gemini Models
GEMINI_FLASH = ModelConfig(
    provider=ModelProvider.GEMINI,
    model_name="gemini-2.5-flash",
    reasoning=ReasoningMode.DISABLED,
    tools_config={"enabled": False, "tools": None}
)

GEMINI_FLASH_DYNAMIC = ModelConfig(
    provider=ModelProvider.GEMINI,
    model_name="gemini-2.5-flash",
    reasoning=ReasoningMode.DYNAMIC,
    tools_config={"enabled": False, "tools": None}
)

GEMINI_PRO = ModelConfig(
    provider=ModelProvider.GEMINI,
    model_name="gemini-2.5-pro",
    reasoning=ReasoningMode.DYNAMIC,
    tools_config={"enabled": False, "tools": None}
)

# GPT-5 configurations (Responses API only)
GEMINI_3_PRO_PREVIEW = ModelConfig(
    provider=ModelProvider.GEMINI,
    model_name="gemini-3-pro-preview",
    reasoning=ReasoningMode.DYNAMIC,
    tools_config={"enabled": False, "tools": None}
)

GPT5_DEFAULT = ModelConfig(
    provider=ModelProvider.OPENAI,
    model_name="gpt-5",
    reasoning=ReasoningMode.MEDIUM,
    temperature=None,
    tools_config={"enabled": False, "tools": None},
    text_verbosity="medium"
)

GPT5_MINIMAL = ModelConfig(
    provider=ModelProvider.OPENAI,
    model_name="gpt-5",
    reasoning=ReasoningMode.MINIMAL,
    temperature=None,
    tools_config={"enabled": False, "tools": None},
    text_verbosity="low"
)

GPT5_HIGH = ModelConfig(
    provider=ModelProvider.OPENAI,
    model_name="gpt-5",
    reasoning=ReasoningMode.HIGH,
    temperature=None,
    tools_config={"enabled": False, "tools": None},
    text_verbosity="high"
)

GPT5_MINI = ModelConfig(
    provider=ModelProvider.OPENAI,
    model_name="gpt-5-mini",
    reasoning=ReasoningMode.HIGH,
    temperature=None,
    tools_config={"enabled": False, "tools": None},
    text_verbosity="medium",
)

# GPT-5.1 configurations
GPT5_1_DEFAULT = ModelConfig(
    provider=ModelProvider.OPENAI,
    model_name="gpt-5.1",
    reasoning=ReasoningMode.MEDIUM,
    temperature=None,
    tools_config={"enabled": False, "tools": None},
    text_verbosity="medium"
)

GPT5_1_MINIMAL = ModelConfig(
    provider=ModelProvider.OPENAI,
    model_name="gpt-5.1",
    reasoning=ReasoningMode.MINIMAL,
    temperature=None,
    tools_config={"enabled": False, "tools": None},
    text_verbosity="low"
)

GPT5_1_HIGH = ModelConfig(
    provider=ModelProvider.OPENAI,
    model_name="gpt-5.1",
    reasoning=ReasoningMode.HIGH,
    temperature=None,
    tools_config={"enabled": False, "tools": None},
    text_verbosity="high"
)

GPT5_1_CODEX = ModelConfig(
    provider=ModelProvider.OPENAI,
    model_name="gpt-5.1-codex",
    reasoning=ReasoningMode.MEDIUM,
    temperature=None,
    tools_config={"enabled": False, "tools": None},
    text_verbosity="medium"
)

# GPT-5.2 configurations (Responses API)
GPT5_2_DEFAULT = ModelConfig(
    provider=ModelProvider.OPENAI,
    model_name="gpt-5.2",
    reasoning=ReasoningMode.MEDIUM,
    temperature=None,
    tools_config={"enabled": False, "tools": None},
    text_verbosity="medium",
)

GPT5_2_MINIMAL = ModelConfig(
    provider=ModelProvider.OPENAI,
    model_name="gpt-5.2",
    reasoning=ReasoningMode.MINIMAL,
    temperature=None,
    tools_config={"enabled": False, "tools": None},
    text_verbosity="low",
)

GPT5_2_HIGH = ModelConfig(
    provider=ModelProvider.OPENAI,
    model_name="gpt-5.2",
    reasoning=ReasoningMode.HIGH,
    temperature=None,
    tools_config={"enabled": False, "tools": None},
    text_verbosity="high",
)

# -----------------------------------------------------------------------------
# Backward-compatibility aliases for older test suites and integrations
# These names map to the current model presets to avoid breaking older imports.
# -----------------------------------------------------------------------------
# Older naming used "O1" to refer to OpenAI's reasoning model; map to O3 presets.
O1_HIGH = O3_HIGH  # Deprecated alias
# Some suites used "O3_MINI_HIGH" which corresponds to today's O4-mini high effort
O3_MINI_HIGH = O4_MINI_HIGH  # Deprecated alias
