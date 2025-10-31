"""
config/agents.py

This module provides configurations for AI models used in different phases of analysis.
It allows users to easily configure which models to use for each phase by updating
the `MODEL_CONFIG` dictionary.

Users can specify a different model for each phase and whether to use reasoning.
"""

from typing import Dict

from core.agents.base import ModelProvider
from core.types.models import (
    ModelConfig,
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
    GEMINI_PRO,
    create_researcher_config,
)

# ====================================================
# Phase Model Configuration
# Define which model to use for each phase.
# ====================================================

MODEL_PRESETS: Dict[str, Dict[str, object]] = {
    "gemini-flash": {
        "config": GEMINI_FLASH,
        "label": "Gemini 2.5 Flash",
        "description": "Fast, low-cost summarization and planning.",
        "provider": ModelProvider.GEMINI,
    },
    "gemini-pro": {
        "config": GEMINI_PRO,
        "label": "Gemini 2.5 Pro",
        "description": "Stronger reasoning with higher latency and cost.",
        "provider": ModelProvider.GEMINI,
    },
    "claude-sonnet": {
        "config": CLAUDE_BASIC,
        "label": "Claude Sonnet 4",
        "description": "Balanced quality and speed for general analysis.",
        "provider": ModelProvider.ANTHROPIC,
    },
    "claude-sonnet-reasoning": {
        "config": CLAUDE_WITH_REASONING,
        "label": "Claude Sonnet 4 (Reasoning)",
        "description": "Enhanced reasoning mode for complex investigations.",
        "provider": ModelProvider.ANTHROPIC,
    },
    "o3-low": {
        "config": O3_LOW,
        "label": "OpenAI o3 (low effort)",
        "description": "Low reasoning effort for lightweight tasks.",
        "provider": ModelProvider.OPENAI,
    },
    "o3-medium": {
        "config": O3_MEDIUM,
        "label": "OpenAI o3 (medium effort)",
        "description": "Balanced reasoning effort for most tasks.",
        "provider": ModelProvider.OPENAI,
    },
    "o3-high": {
        "config": O3_HIGH,
        "label": "OpenAI o3 (high effort)",
        "description": "Maximum reasoning effort for critical phases.",
        "provider": ModelProvider.OPENAI,
    },
    "o4-mini-low": {
        "config": O4_MINI_LOW,
        "label": "OpenAI o4-mini (low effort)",
        "description": "Efficient modality-friendly reasoning.",
        "provider": ModelProvider.OPENAI,
    },
    "o4-mini-medium": {
        "config": O4_MINI_MEDIUM,
        "label": "OpenAI o4-mini (medium effort)",
        "description": "Balanced o4-mini configuration.",
        "provider": ModelProvider.OPENAI,
    },
    "o4-mini-high": {
        "config": O4_MINI_HIGH,
        "label": "OpenAI o4-mini (high effort)",
        "description": "Highest reasoning effort for o4-mini.",
        "provider": ModelProvider.OPENAI,
    },
    "gpt4.1-default": {
        "config": GPT4_1_DEFAULT,
        "label": "GPT-4.1 (temperature 0.7)",
        "description": "Default GPT-4.1 temperature.",
        "provider": ModelProvider.OPENAI,
    },
    "gpt4.1-creative": {
        "config": GPT4_1_CREATIVE,
        "label": "GPT-4.1 (temperature 0.9)",
        "description": "Creativity focused output.",
        "provider": ModelProvider.OPENAI,
    },
    "gpt4.1-precise": {
        "config": GPT4_1_PRECISE,
        "label": "GPT-4.1 (temperature 0.2)",
        "description": "Precise, deterministic responses.",
        "provider": ModelProvider.OPENAI,
    },
    "deepseek-reasoner": {
        "config": DEEPSEEK_REASONER,
        "label": "DeepSeek Reasoner",
        "description": "DeepSeek reasoning agent.",
        "provider": ModelProvider.DEEPSEEK,
    },
    "deepseek-chat": {
        "config": DEEPSEEK_CHAT,
        "label": "DeepSeek Chat",
        "description": "Conversational DeepSeek model.",
        "provider": ModelProvider.DEEPSEEK,
    },
}

MODEL_PRESET_DEFAULTS: Dict[str, str] = {
    "phase1": "gemini-flash",
    "phase2": "gemini-flash",
    "phase3": "gemini-flash",
    "phase4": "gemini-flash",
    "phase5": "gemini-flash",
    "final": "gemini-flash",
    "researcher": "gemini-flash",
}


def _build_default_model_config() -> Dict[str, ModelConfig]:
    config: Dict[str, ModelConfig] = {}
    for phase, preset_key in MODEL_PRESET_DEFAULTS.items():
        preset = MODEL_PRESETS[preset_key]
        config[phase] = preset["config"]
    return config


# Default model configuration (mutated at runtime when overrides are applied)
MODEL_CONFIG = _build_default_model_config()
