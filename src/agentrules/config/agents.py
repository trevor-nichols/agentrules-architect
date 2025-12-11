"""
config/agents.py
This module provides configurations for AI models used in different phases of analysis.
It allows users to easily configure which models to use for each phase by updating
the `MODEL_CONFIG` dictionary.

Users can specify a different model for each phase and whether to use reasoning.
"""

from typing import TypedDict

from agentrules.core.agents.base import ModelProvider
from agentrules.core.types.models import (
    CLAUDE_BASIC,
    CLAUDE_HAIKU,
    CLAUDE_HAIKU_WITH_REASONING,
    CLAUDE_OPUS,
    CLAUDE_OPUS_45,
    CLAUDE_OPUS_45_WITH_REASONING,
    CLAUDE_OPUS_WITH_REASONING,
    CLAUDE_WITH_REASONING,
    DEEPSEEK_CHAT,
    DEEPSEEK_REASONER,
    GEMINI_3_PRO_PREVIEW,
    GEMINI_FLASH,
    GEMINI_FLASH_DYNAMIC,
    GEMINI_PRO,
    GPT4_1_CREATIVE,
    GPT4_1_DEFAULT,
    GPT4_1_PRECISE,
    GPT5_1_CODEX,
    GPT5_1_DEFAULT,
    GPT5_1_HIGH,
    GPT5_1_MINIMAL,
    GPT5_2_DEFAULT,
    GPT5_2_HIGH,
    GPT5_2_MINIMAL,
    GPT5_DEFAULT,
    GPT5_HIGH,
    GPT5_MINI,
    GPT5_MINIMAL,
    GROK_4_0709,
    GROK_4_FAST_NON_REASONING,
    GROK_4_FAST_REASONING,
    GROK_CODE_FAST,
    O3_HIGH,
    O3_LOW,
    O3_MEDIUM,
    O4_MINI_HIGH,
    O4_MINI_LOW,
    O4_MINI_MEDIUM,
    ModelConfig,
)

# ====================================================
# Phase Model Configuration
# Define which model to use for each phase.
# ====================================================

class PresetDefinition(TypedDict):
    """Shape of a model preset entry."""
    config: ModelConfig
    label: str
    description: str
    provider: ModelProvider


def _apply_model_limits(config: ModelConfig) -> ModelConfig:
    """
    Attach provisional context window metadata and estimator hints to a ModelConfig.

    Values are conservative and logging-only; refine once telemetry is available.
    """
    name = config.model_name.lower()
    provider = config.provider

    limit: int | None = getattr(config, "max_input_tokens", None)
    estimator_family: str | None = getattr(config, "estimator_family", None)

    if provider == ModelProvider.ANTHROPIC:
        limit = limit or 200_000
        estimator_family = estimator_family or "anthropic_api"
    elif provider == ModelProvider.GEMINI:
        estimator_family = estimator_family or "gemini_api"
        if limit is None:
            if "3-pro" in name:
                limit = 1_000_000
            else:
                limit = 1_048_576
    elif provider == ModelProvider.OPENAI:
        estimator_family = estimator_family or "tiktoken"
        if limit is None:
            if "o3" in name or "o4-mini" in name:
                limit = 200_000
            elif "gpt-4.1" in name:
                limit = 128_000
            elif "gpt-5.1" in name or "gpt-5" in name:
                limit = 400_000
    elif provider == ModelProvider.DEEPSEEK:
        limit = limit or 64_000
        estimator_family = estimator_family or "tiktoken"
    elif provider == ModelProvider.XAI:
        limit = limit or 256_000
        estimator_family = estimator_family or "tiktoken"

    return config._replace(
        max_input_tokens=limit,
        estimator_family=estimator_family,
        safety_margin_tokens=getattr(config, "safety_margin_tokens", None),
    )


def _preset(
    *,
    config: ModelConfig,
    label: str,
    description: str,
    provider: ModelProvider,
) -> PresetDefinition:
    """Typed helper to construct preset definitions."""
    return PresetDefinition(
        config=_apply_model_limits(config),
        label=label,
        description=description,
        provider=provider,
    )


MODEL_PRESETS: dict[str, PresetDefinition] = {
    "gemini-3-pro-preview": _preset(
        config=GEMINI_3_PRO_PREVIEW,
        label="Gemini 3 Pro (Preview)",
        description=(
            "Newest Gemini tier with 1M token context, high reasoning depth, and "
            "thinking_level controls."
        ),
        provider=ModelProvider.GEMINI,
    ),
    "gemini-flash": _preset(
        config=GEMINI_FLASH,
        label="Gemini 2.5 Flash",
        description="Fast, low-cost summarization and planning.",
        provider=ModelProvider.GEMINI,
    ),
    "gemini-flash-thinking": _preset(
        config=GEMINI_FLASH_DYNAMIC,
        label="Gemini 2.5 Flash (Thinking)",
        description="Flash with dynamic thinking enabled (auto thinking budget).",
        provider=ModelProvider.GEMINI,
    ),
    "gemini-pro": _preset(
        config=GEMINI_PRO,
        label="Gemini 2.5 Pro",
        description="Gemini Pro with dynamic thinking (auto thinking budget).",
        provider=ModelProvider.GEMINI,
    ),
    "claude-sonnet": _preset(
        config=CLAUDE_BASIC,
        label="Claude Sonnet 4.5",
        description="Balanced Claude 4.5 release for default analysis work.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-sonnet-reasoning": _preset(
        config=CLAUDE_WITH_REASONING,
        label="Claude Sonnet 4.5 (Thinking)",
        description="Enables extended thinking for deeper investigations.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-haiku": _preset(
        config=CLAUDE_HAIKU,
        label="Claude Haiku 4.5",
        description="Latency-optimized Claude 4.5 tier for rapid iteration.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-haiku-reasoning": _preset(
        config=CLAUDE_HAIKU_WITH_REASONING,
        label="Claude Haiku 4.5 (Thinking)",
        description="Fast model with extended thinking enabled.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-opus": _preset(
        config=CLAUDE_OPUS,
        label="Claude Opus 4.1",
        description="Premium Claude tier prioritizing accuracy over latency.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-opus-reasoning": _preset(
        config=CLAUDE_OPUS_WITH_REASONING,
        label="Claude Opus 4.1 (Thinking)",
        description="Most capable Claude model with extended thinking.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-opus-4.5": _preset(
        config=CLAUDE_OPUS_45,
        label="Claude Opus 4.5",
        description="Newest Opus 4.5 release; improved reasoning depth and safety.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-opus-4.5-reasoning": _preset(
        config=CLAUDE_OPUS_45_WITH_REASONING,
        label="Claude Opus 4.5 (Thinking)",
        description="Opus 4.5 with extended thinking enabled for hardest tasks.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "o3-low": _preset(
        config=O3_LOW,
        label="OpenAI o3 (low effort)",
        description="Low reasoning effort for lightweight tasks.",
        provider=ModelProvider.OPENAI,
    ),
    "o3-medium": _preset(
        config=O3_MEDIUM,
        label="OpenAI o3 (medium effort)",
        description="Balanced reasoning effort for most tasks.",
        provider=ModelProvider.OPENAI,
    ),
    "o3-high": _preset(
        config=O3_HIGH,
        label="OpenAI o3 (high effort)",
        description="Maximum reasoning effort for critical phases.",
        provider=ModelProvider.OPENAI,
    ),
    "o4-mini-low": _preset(
        config=O4_MINI_LOW,
        label="OpenAI o4-mini (low effort)",
        description="Efficient modality-friendly reasoning.",
        provider=ModelProvider.OPENAI,
    ),
    "o4-mini-medium": _preset(
        config=O4_MINI_MEDIUM,
        label="OpenAI o4-mini (medium effort)",
        description="Balanced o4-mini configuration.",
        provider=ModelProvider.OPENAI,
    ),
    "o4-mini-high": _preset(
        config=O4_MINI_HIGH,
        label="OpenAI o4-mini (high effort)",
        description="Highest reasoning effort for o4-mini.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt4.1-default": _preset(
        config=GPT4_1_DEFAULT,
        label="GPT-4.1 (temperature 0.7)",
        description="Default GPT-4.1 temperature.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt4.1-creative": _preset(
        config=GPT4_1_CREATIVE,
        label="GPT-4.1 (temperature 0.9)",
        description="Creativity focused output.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt4.1-precise": _preset(
        config=GPT4_1_PRECISE,
        label="GPT-4.1 (temperature 0.2)",
        description="Precise, deterministic responses.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt5-default": _preset(
        config=GPT5_DEFAULT,
        label="GPT-5 (medium reasoning)",
        description="GPT-5 via Responses API with medium reasoning and verbosity.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt5-mini": _preset(
        config=GPT5_MINI,
        label="GPT-5 Mini (high reasoning)",
        description="Cost-efficient GPT-5 Mini with 400k context and high reasoning.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt5-minimal": _preset(
        config=GPT5_MINIMAL,
        label="GPT-5 (minimal reasoning)",
        description="GPT-5 minimal reasoning and low verbosity for speed.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt5-high": _preset(
        config=GPT5_HIGH,
        label="GPT-5 (high reasoning)",
        description="GPT-5 via Responses API with high reasoning depth and verbosity.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt51-default": _preset(
        config=GPT5_1_DEFAULT,
        label="GPT-5.1 (medium reasoning)",
        description="GPT-5.1 via Responses API with medium reasoning and verbosity.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt51-minimal": _preset(
        config=GPT5_1_MINIMAL,
        label="GPT-5.1 (minimal reasoning)",
        description="GPT-5.1 minimal reasoning and low verbosity for speed.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt51-high": _preset(
        config=GPT5_1_HIGH,
        label="GPT-5.1 (high reasoning)",
        description="GPT-5.1 via Responses API with high reasoning depth and verbosity.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt52-default": _preset(
        config=GPT5_2_DEFAULT,
        label="GPT-5.2 (medium reasoning)",
        description="GPT-5.2 via Responses API with medium reasoning and verbosity.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt52-minimal": _preset(
        config=GPT5_2_MINIMAL,
        label="GPT-5.2 (minimal reasoning)",
        description="GPT-5.2 minimal reasoning and low verbosity for speed.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt52-high": _preset(
        config=GPT5_2_HIGH,
        label="GPT-5.2 (high reasoning)",
        description="GPT-5.2 via Responses API with high reasoning depth and verbosity.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt-5.1-codex": _preset(
        config=GPT5_1_CODEX,
        label="GPT-5.1 Codex",
        description="Coding-optimized GPT-5.1 variant via Responses API with medium reasoning.",
        provider=ModelProvider.OPENAI,
    ),
    "deepseek-reasoner": _preset(
        config=DEEPSEEK_REASONER,
        label="DeepSeek Reasoner",
        description="DeepSeek reasoning agent.",
        provider=ModelProvider.DEEPSEEK,
    ),
    "deepseek-chat": _preset(
        config=DEEPSEEK_CHAT,
        label="DeepSeek Chat",
        description="Conversational DeepSeek model.",
        provider=ModelProvider.DEEPSEEK,
    ),
    "grok-4-0709": _preset(
        config=GROK_4_0709,
        label="Grok 4 (July 09)",
        description="Latest Grok 4 release with balanced reasoning effort.",
        provider=ModelProvider.XAI,
    ),
    "grok-4-fast-reasoning": _preset(
        config=GROK_4_FAST_REASONING,
        label="Grok 4 Fast (Reasoning)",
        description="Lower latency Grok 4 reasoning tier.",
        provider=ModelProvider.XAI,
    ),
    "grok-4-fast-non-reasoning": _preset(
        config=GROK_4_FAST_NON_REASONING,
        label="Grok 4 Fast (Non-Reasoning)",
        description="Cost-efficient Grok tier without reasoning tokens.",
        provider=ModelProvider.XAI,
    ),
    "grok-code-fast": _preset(
        config=GROK_CODE_FAST,
        label="Grok Code Fast",
        description="Grok code assistant tuned for reasoning over codebases.",
        provider=ModelProvider.XAI,
    ),
}

MODEL_PRESET_DEFAULTS: dict[str, str] = {
    "phase1": "gpt5-mini",
    "phase2": "gpt5-mini",
    "phase3": "gpt5-mini",
    "phase4": "gpt5-mini",
    "phase5": "gpt5-mini",
    "final": "gpt5-mini",
    "researcher": "gpt5-mini",
}


def _build_default_model_config() -> dict[str, ModelConfig]:
    config: dict[str, ModelConfig] = {}
    for phase, preset_key in MODEL_PRESET_DEFAULTS.items():
        preset: PresetDefinition = MODEL_PRESETS[preset_key]
        config[phase] = preset["config"]
    return config


# Default model configuration (mutated at runtime when overrides are applied)
MODEL_CONFIG = _build_default_model_config()
