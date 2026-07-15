"""
config/agents.py
This module provides configurations for AI models used in different phases of analysis.
It allows users to easily configure which models to use for each phase by updating
the `MODEL_CONFIG` dictionary.

Users can specify a different model for each phase and whether to use reasoning.
"""

from typing import TypedDict

from agentrules.core.agents.base import ModelProvider, ReasoningMode
from agentrules.core.types.models import (
    CLAUDE_BASIC,
    CLAUDE_CODE_RUNTIME_DEFAULT_MODEL,
    CLAUDE_FABLE_5,
    CLAUDE_HAIKU,
    CLAUDE_HAIKU_WITH_REASONING,
    CLAUDE_OPUS,
    CLAUDE_OPUS_45,
    CLAUDE_OPUS_45_WITH_REASONING,
    CLAUDE_OPUS_46,
    CLAUDE_OPUS_46_WITH_REASONING,
    CLAUDE_OPUS_47,
    CLAUDE_OPUS_47_WITH_REASONING,
    CLAUDE_OPUS_48,
    CLAUDE_OPUS_48_WITH_REASONING,
    CLAUDE_OPUS_WITH_REASONING,
    CLAUDE_SONNET_5,
    CLAUDE_SONNET_5_WITH_REASONING,
    CLAUDE_SONNET_46,
    CLAUDE_SONNET_46_WITH_REASONING,
    CLAUDE_WITH_REASONING,
    DEEPSEEK_CHAT,
    DEEPSEEK_REASONER,
    DEEPSEEK_V4_FLASH,
    DEEPSEEK_V4_FLASH_NON_REASONING,
    DEEPSEEK_V4_PRO,
    DEEPSEEK_V4_PRO_MAX,
    DEEPSEEK_V4_PRO_NON_REASONING,
    GEMINI_3_1_FLASH_LITE,
    GEMINI_3_1_FLASH_LITE_PREVIEW,
    GEMINI_3_1_PRO_PREVIEW,
    GEMINI_3_5_FLASH,
    GEMINI_3_FLASH_PREVIEW,
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
    GPT5_2_CODEX,
    GPT5_2_DEFAULT,
    GPT5_2_HIGH,
    GPT5_2_MINIMAL,
    GPT5_3_CODEX,
    GPT5_4_2026_03_05,
    GPT5_4_MINI_HIGH,
    GPT5_4_MINI_LOW,
    GPT5_4_MINI_MEDIUM,
    GPT5_4_MINI_NONE,
    GPT5_4_MINI_XHIGH,
    GPT5_4_NANO_HIGH,
    GPT5_4_NANO_LOW,
    GPT5_4_NANO_MEDIUM,
    GPT5_4_NANO_NONE,
    GPT5_4_NANO_XHIGH,
    GPT5_5_DEFAULT,
    GPT5_5_HIGH,
    GPT5_5_LOW,
    GPT5_5_NONE,
    GPT5_5_XHIGH,
    GPT5_6_LUNA_DEFAULT,
    GPT5_6_LUNA_LOW,
    GPT5_6_SOL_DEFAULT,
    GPT5_6_SOL_HIGH,
    GPT5_6_SOL_LOW,
    GPT5_6_SOL_MAX,
    GPT5_6_SOL_NONE,
    GPT5_6_SOL_XHIGH,
    GPT5_6_TERRA_DEFAULT,
    GPT5_6_TERRA_HIGH,
    GPT5_DEFAULT,
    GPT5_HIGH,
    GPT5_MINI,
    GPT5_MINIMAL,
    GROK_4_0709,
    GROK_4_1_FAST_NON_REASONING,
    GROK_4_1_FAST_REASONING,
    GROK_4_3,
    GROK_4_3_NON_REASONING,
    GROK_4_3_REASONING_MEDIUM,
    GROK_4_FAST_NON_REASONING,
    GROK_4_FAST_REASONING,
    GROK_BUILD_0_1,
    GROK_CODE_FAST,
    O3_HIGH,
    O3_LOW,
    O3_MEDIUM,
    O4_MINI_HIGH,
    O4_MINI_LOW,
    O4_MINI_MEDIUM,
    ModelConfig,
    create_claude_code_config,
    create_codex_config,
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


_XAI_1M_CONTEXT_MODELS: frozenset[str] = frozenset(
    {
        "grok-4.3",
        "grok-4.3-latest",
        "grok-latest",
        "grok-3",
        "grok-3-latest",
        "grok-3-beta",
        "grok-3-fast",
        "grok-3-fast-latest",
        "grok-3-fast-beta",
        "grok-3-mini",
        "grok-3-mini-latest",
        "grok-3-mini-beta",
        "grok-3-mini-fast",
        "grok-3-mini-fast-latest",
        "grok-3-mini-fast-beta",
        "grok-3-mini-high",
        "grok-3-mini-high-beta",
        "grok-3-mini-fast-high",
        "grok-3-mini-fast-high-beta",
        "grok-4-0709",
        "grok-4",
        "grok-4-latest",
        "grok-4-fast-reasoning",
        "grok-4-fast",
        "grok-4-fast-reasoning-latest",
        "grok-4-fast-non-reasoning",
        "grok-4-fast-non-reasoning-latest",
        "grok-4-1-fast-reasoning",
        "grok-4-1-fast",
        "grok-4-1-fast-reasoning-latest",
        "grok-4-1-fast-non-reasoning",
        "grok-4-1-fast-non-reasoning-latest",
    }
)


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
        if limit is None:
            if (
                name.startswith("claude-fable-5")
                or name.startswith("claude-sonnet-5")
                or name.startswith("claude-opus-4-6")
                or name.startswith("claude-opus-4-7")
                or name.startswith("claude-opus-4-8")
                or name.startswith("claude-sonnet-4-6")
            ):
                limit = 1_000_000
            else:
                limit = 200_000
        estimator_family = estimator_family or "anthropic_api"
    elif provider == ModelProvider.GEMINI:
        estimator_family = estimator_family or "gemini_api"
        if limit is None:
            if "3-pro" in name:
                limit = 1_000_000
            else:
                limit = 1_048_576
    elif provider in {ModelProvider.OPENAI, ModelProvider.CODEX}:
        estimator_family = estimator_family or "tiktoken"
        if limit is None:
            if "o3" in name or "o4-mini" in name:
                limit = 200_000
            elif "gpt-4.1" in name:
                limit = 128_000
            elif name.startswith("gpt-5.6"):
                limit = 1_050_000
            elif "gpt-5.1" in name or "gpt-5" in name:
                limit = 400_000
    elif provider == ModelProvider.DEEPSEEK:
        if limit is None:
            limit = 1_000_000 if name.startswith("deepseek-v4-") else 64_000
        estimator_family = estimator_family or "tiktoken"
    elif provider == ModelProvider.XAI:
        if limit is None:
            limit = 1_000_000 if name in _XAI_1M_CONTEXT_MODELS else 256_000
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


def _derive_codex_runtime_preset(
    base_preset: PresetDefinition,
    *,
    label: str | None = None,
    description: str | None = None,
) -> PresetDefinition:
    base_label = base_preset["label"]
    base_description = base_preset["description"]
    return _preset(
        config=create_codex_config(base_preset["config"]),
        label=label or f"Codex {base_label}",
        description=description or f"{base_description} Routed through the Codex app-server runtime.",
        provider=ModelProvider.CODEX,
    )


def _derive_claude_code_runtime_preset(
    base_preset: PresetDefinition,
    *,
    label: str | None = None,
    description: str | None = None,
) -> PresetDefinition:
    base_label = base_preset["label"]
    base_description = base_preset["description"]
    return _preset(
        config=create_claude_code_config(base_preset["config"]),
        label=label or f"Claude Code {base_label}",
        description=description or f"{base_description} Routed through the Claude Code Agent SDK runtime.",
        provider=ModelProvider.CLAUDE_CODE,
    )


def _claude_code_runtime_managed_preset(
    *,
    model_name: str,
    label: str,
    description: str,
    reasoning: ReasoningMode = ReasoningMode.DISABLED,
) -> PresetDefinition:
    config = create_claude_code_config(CLAUDE_SONNET_5)._replace(
        model_name=model_name,
        reasoning=reasoning,
        max_input_tokens=1_000_000,
        anthropic_effort=None,
    )
    return _preset(
        config=config,
        label=label,
        description=description,
        provider=ModelProvider.CLAUDE_CODE,
    )


BASE_MODEL_PRESETS: dict[str, PresetDefinition] = {
    "gemini-3.5-flash": _preset(
        config=GEMINI_3_5_FLASH,
        label="Gemini 3.5 Flash",
        description="Stable Gemini 3.5 Flash release for agentic coding and long-horizon tasks.",
        provider=ModelProvider.GEMINI,
    ),
    "gemini-3-flash-preview": _preset(
        config=GEMINI_3_FLASH_PREVIEW,
        label="Gemini 3 Flash (Preview)",
        description="Gemini 3 Flash with balanced thinking_level controls.",
        provider=ModelProvider.GEMINI,
    ),
    "gemini-3-pro-preview": _preset(
        config=GEMINI_3_PRO_PREVIEW,
        label="Gemini 3 Pro (Preview, Deprecated)",
        description=(
            "Retired Gemini 3 Pro preview preserved for backwards compatibility. "
            "Prefer Gemini 3.1 Pro (Preview) for new configurations."
        ),
        provider=ModelProvider.GEMINI,
    ),
    "gemini-3.1-flash-lite": _preset(
        config=GEMINI_3_1_FLASH_LITE,
        label="Gemini 3.1 Flash-Lite",
        description="Stable low-latency Gemini 3.1 tier for high-volume, lightweight tasks.",
        provider=ModelProvider.GEMINI,
    ),
    "gemini-3.1-flash-lite-preview": _preset(
        config=GEMINI_3_1_FLASH_LITE_PREVIEW,
        label="Gemini 3.1 Flash-Lite (Preview, Deprecated)",
        description=(
            "Retired Gemini 3.1 Flash-Lite preview preserved for backwards compatibility. "
            "Prefer Gemini 3.1 Flash-Lite for new configurations."
        ),
        provider=ModelProvider.GEMINI,
    ),
    "gemini-3.1-pro-preview": _preset(
        config=GEMINI_3_1_PRO_PREVIEW,
        label="Gemini 3.1 Pro (Preview)",
        description="Gemini 3.1 Pro preview with high reasoning depth via thinking_level.",
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
    "claude-sonnet-4.6": _preset(
        config=CLAUDE_SONNET_46,
        label="Claude Sonnet 4.6",
        description="Claude Sonnet 4.6 release with adaptive thinking support.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-sonnet-4.6-reasoning-high": _preset(
        config=CLAUDE_SONNET_46_WITH_REASONING._replace(anthropic_effort="high"),
        label="Claude Sonnet 4.6 (Adaptive Thinking, High Effort)",
        description="Claude Sonnet 4.6 adaptive thinking with high effort for deep analysis.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-sonnet-4.6-reasoning-medium": _preset(
        config=CLAUDE_SONNET_46_WITH_REASONING._replace(anthropic_effort="medium"),
        label="Claude Sonnet 4.6 (Adaptive Thinking, Medium Effort)",
        description="Claude Sonnet 4.6 adaptive thinking with medium effort for balanced runs.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-sonnet-4.6-reasoning-low": _preset(
        config=CLAUDE_SONNET_46_WITH_REASONING._replace(anthropic_effort="low"),
        label="Claude Sonnet 4.6 (Adaptive Thinking, Low Effort)",
        description="Claude Sonnet 4.6 adaptive thinking with low effort for faster iteration.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-sonnet-5": _preset(
        config=CLAUDE_SONNET_5,
        label="Claude Sonnet 5 (Thinking Disabled)",
        description="Claude Sonnet 5 with thinking explicitly disabled, structured output, and 1M context.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-sonnet-5-reasoning-low": _preset(
        config=CLAUDE_SONNET_5_WITH_REASONING._replace(anthropic_effort="low"),
        label="Claude Sonnet 5 (Adaptive Thinking, Low Effort)",
        description="Claude Sonnet 5 adaptive thinking at low effort for scoped, latency-sensitive work.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-sonnet-5-reasoning-medium": _preset(
        config=CLAUDE_SONNET_5_WITH_REASONING._replace(anthropic_effort="medium"),
        label="Claude Sonnet 5 (Adaptive Thinking, Medium Effort)",
        description="Claude Sonnet 5 adaptive thinking at medium effort for balanced cost and quality.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-sonnet-5-reasoning-high": _preset(
        config=CLAUDE_SONNET_5_WITH_REASONING._replace(anthropic_effort="high"),
        label="Claude Sonnet 5 (Adaptive Thinking, High Effort)",
        description="Claude Sonnet 5 adaptive thinking at its default high effort for complex work.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-sonnet-5-reasoning-xhigh": _preset(
        config=CLAUDE_SONNET_5_WITH_REASONING._replace(anthropic_effort="xhigh"),
        label="Claude Sonnet 5 (Adaptive Thinking, XHigh Effort)",
        description="Claude Sonnet 5 adaptive thinking at xhigh effort for difficult coding and agentic work.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-sonnet-5-reasoning-max": _preset(
        config=CLAUDE_SONNET_5_WITH_REASONING._replace(anthropic_effort="max"),
        label="Claude Sonnet 5 (Adaptive Thinking, Max Effort)",
        description="Claude Sonnet 5 adaptive thinking at maximum effort for quality-first workloads.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-fable-5-reasoning-low": _preset(
        config=CLAUDE_FABLE_5._replace(anthropic_effort="low"),
        label="Claude Fable 5 (Always-Adaptive, Low Effort)",
        description="Claude Fable 5 always-on adaptive thinking at low effort with 1M context.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-fable-5-reasoning-medium": _preset(
        config=CLAUDE_FABLE_5._replace(anthropic_effort="medium"),
        label="Claude Fable 5 (Always-Adaptive, Medium Effort)",
        description="Claude Fable 5 always-on adaptive thinking at medium effort with 1M context.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-fable-5-reasoning-high": _preset(
        config=CLAUDE_FABLE_5._replace(anthropic_effort="high"),
        label="Claude Fable 5 (Always-Adaptive, High Effort)",
        description="Claude Fable 5 always-on adaptive thinking at high effort with 1M context.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-fable-5-reasoning-xhigh": _preset(
        config=CLAUDE_FABLE_5._replace(anthropic_effort="xhigh"),
        label="Claude Fable 5 (Always-Adaptive, XHigh Effort)",
        description="Claude Fable 5 always-on adaptive thinking at xhigh effort for long-horizon agentic work.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-fable-5-reasoning-max": _preset(
        config=CLAUDE_FABLE_5._replace(anthropic_effort="max"),
        label="Claude Fable 5 (Always-Adaptive, Max Effort)",
        description="Claude Fable 5 always-on adaptive thinking at maximum effort for the hardest workloads.",
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
        label="Claude Opus 4.8 (Generic Key)",
        description="Generic Opus compatibility key updated to Claude Opus 4.8 before Opus 4.1 retirement.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-opus-reasoning": _preset(
        config=CLAUDE_OPUS_WITH_REASONING,
        label="Claude Opus 4.8 (Generic Key, Adaptive Thinking)",
        description="Generic Opus reasoning key updated to Claude Opus 4.8 adaptive thinking at provider defaults.",
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
    "claude-opus-4.6": _preset(
        config=CLAUDE_OPUS_46,
        label="Claude Opus 4.6",
        description="Claude Opus 4.6 release; supports adaptive thinking and higher output limits.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-opus-4.6-reasoning": _preset(
        config=CLAUDE_OPUS_46_WITH_REASONING._replace(anthropic_effort="high"),
        label="Claude Opus 4.6 (Adaptive Thinking, High Effort)",
        description="Opus 4.6 adaptive thinking with high effort (default) for deep reasoning.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-opus-4.6-reasoning-medium": _preset(
        config=CLAUDE_OPUS_46_WITH_REASONING._replace(anthropic_effort="medium"),
        label="Claude Opus 4.6 (Adaptive Thinking, Medium Effort)",
        description="Opus 4.6 adaptive thinking with medium effort for balanced speed/cost.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-opus-4.6-reasoning-low": _preset(
        config=CLAUDE_OPUS_46_WITH_REASONING._replace(anthropic_effort="low"),
        label="Claude Opus 4.6 (Adaptive Thinking, Low Effort)",
        description="Opus 4.6 adaptive thinking with low effort for faster, cheaper runs.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-opus-4.6-reasoning-max": _preset(
        config=CLAUDE_OPUS_46_WITH_REASONING._replace(anthropic_effort="max"),
        label="Claude Opus 4.6 (Adaptive Thinking, Max Effort)",
        description="Opus 4.6 adaptive thinking with max effort for the absolute highest capability.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-opus-4.7": _preset(
        config=CLAUDE_OPUS_47,
        label="Claude Opus 4.7",
        description="Claude Opus 4.7 release with adaptive-only thinking and 1M context support.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-opus-4.7-reasoning": _preset(
        config=CLAUDE_OPUS_47_WITH_REASONING._replace(anthropic_effort="high"),
        label="Claude Opus 4.7 (Adaptive Thinking, High Effort)",
        description="Opus 4.7 adaptive thinking with the default high effort level.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-opus-4.7-reasoning-medium": _preset(
        config=CLAUDE_OPUS_47_WITH_REASONING._replace(anthropic_effort="medium"),
        label="Claude Opus 4.7 (Adaptive Thinking, Medium Effort)",
        description="Opus 4.7 adaptive thinking with medium effort for balanced cost and quality.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-opus-4.7-reasoning-low": _preset(
        config=CLAUDE_OPUS_47_WITH_REASONING._replace(anthropic_effort="low"),
        label="Claude Opus 4.7 (Adaptive Thinking, Low Effort)",
        description="Opus 4.7 adaptive thinking with low effort for faster iteration.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-opus-4.7-reasoning-xhigh": _preset(
        config=CLAUDE_OPUS_47_WITH_REASONING._replace(anthropic_effort="xhigh"),
        label="Claude Opus 4.7 (Adaptive Thinking, XHigh Effort)",
        description="Opus 4.7 adaptive thinking with xhigh effort for coding and agentic work.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-opus-4.7-reasoning-max": _preset(
        config=CLAUDE_OPUS_47_WITH_REASONING._replace(anthropic_effort="max"),
        label="Claude Opus 4.7 (Adaptive Thinking, Max Effort)",
        description="Opus 4.7 adaptive thinking with max effort for the highest available capability.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-opus-4.8": _preset(
        config=CLAUDE_OPUS_48,
        label="Claude Opus 4.8",
        description="Latest Claude Opus release with adaptive-only thinking, 1M context, and stronger agentic coding.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-opus-4.8-reasoning": _preset(
        config=CLAUDE_OPUS_48_WITH_REASONING._replace(anthropic_effort="high"),
        label="Claude Opus 4.8 (Adaptive Thinking, High Effort)",
        description="Opus 4.8 adaptive thinking with the default high effort level.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-opus-4.8-reasoning-medium": _preset(
        config=CLAUDE_OPUS_48_WITH_REASONING._replace(anthropic_effort="medium"),
        label="Claude Opus 4.8 (Adaptive Thinking, Medium Effort)",
        description="Opus 4.8 adaptive thinking with medium effort for balanced runs.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-opus-4.8-reasoning-low": _preset(
        config=CLAUDE_OPUS_48_WITH_REASONING._replace(anthropic_effort="low"),
        label="Claude Opus 4.8 (Adaptive Thinking, Low Effort)",
        description="Opus 4.8 adaptive thinking with low effort for faster, cheaper runs.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-opus-4.8-reasoning-xhigh": _preset(
        config=CLAUDE_OPUS_48_WITH_REASONING._replace(anthropic_effort="xhigh"),
        label="Claude Opus 4.8 (Adaptive Thinking, XHigh Effort)",
        description="Opus 4.8 adaptive thinking with xhigh effort for long-horizon coding and agentic tasks.",
        provider=ModelProvider.ANTHROPIC,
    ),
    "claude-opus-4.8-reasoning-max": _preset(
        config=CLAUDE_OPUS_48_WITH_REASONING._replace(anthropic_effort="max"),
        label="Claude Opus 4.8 (Adaptive Thinking, Max Effort)",
        description="Opus 4.8 adaptive thinking with max effort for the deepest available reasoning.",
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
    "gpt55-none": _preset(
        config=GPT5_5_NONE,
        label="GPT-5.5 (no reasoning)",
        description="GPT-5.5 via Responses API with reasoning disabled and low verbosity for fast runs.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt55-low": _preset(
        config=GPT5_5_LOW,
        label="GPT-5.5 (low reasoning)",
        description="GPT-5.5 via Responses API with low reasoning effort and low verbosity.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt55-default": _preset(
        config=GPT5_5_DEFAULT,
        label="GPT-5.5 (medium reasoning)",
        description="GPT-5.5 via Responses API with medium reasoning and verbosity.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt55-high": _preset(
        config=GPT5_5_HIGH,
        label="GPT-5.5 (high reasoning)",
        description="GPT-5.5 via Responses API with high reasoning depth and high verbosity.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt55-xhigh": _preset(
        config=GPT5_5_XHIGH,
        label="GPT-5.5 (xhigh reasoning)",
        description="GPT-5.5 via Responses API with maximum supported reasoning depth and high verbosity.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt56-sol-none": _preset(
        config=GPT5_6_SOL_NONE,
        label="GPT-5.6 Sol (no reasoning)",
        description="Flagship GPT-5.6 Sol with reasoning disabled, low verbosity, and 1.05M context.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt56-sol-low": _preset(
        config=GPT5_6_SOL_LOW,
        label="GPT-5.6 Sol (low reasoning)",
        description="Flagship GPT-5.6 Sol with low reasoning, low verbosity, and 1.05M context.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt56-sol-default": _preset(
        config=GPT5_6_SOL_DEFAULT,
        label="GPT-5.6 Sol (medium reasoning)",
        description="Default flagship GPT-5.6 Sol with balanced reasoning, verbosity, and 1.05M context.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt56-sol-high": _preset(
        config=GPT5_6_SOL_HIGH,
        label="GPT-5.6 Sol (high reasoning)",
        description="Flagship GPT-5.6 Sol with high reasoning depth, high verbosity, and 1.05M context.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt56-sol-xhigh": _preset(
        config=GPT5_6_SOL_XHIGH,
        label="GPT-5.6 Sol (xhigh reasoning)",
        description="Flagship GPT-5.6 Sol with xhigh reasoning, high verbosity, and 1.05M context.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt56-sol-max": _preset(
        config=GPT5_6_SOL_MAX,
        label="GPT-5.6 Sol (max reasoning)",
        description="Flagship GPT-5.6 Sol at maximum reasoning effort for the hardest quality-first workloads.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt56-terra-default": _preset(
        config=GPT5_6_TERRA_DEFAULT,
        label="GPT-5.6 Terra (medium reasoning)",
        description="Balanced-cost GPT-5.6 Terra with medium reasoning, medium verbosity, and 1.05M context.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt56-terra-high": _preset(
        config=GPT5_6_TERRA_HIGH,
        label="GPT-5.6 Terra (high reasoning)",
        description="Balanced-cost GPT-5.6 Terra with high reasoning, high verbosity, and 1.05M context.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt56-luna-low": _preset(
        config=GPT5_6_LUNA_LOW,
        label="GPT-5.6 Luna (low reasoning)",
        description="High-volume GPT-5.6 Luna with low reasoning, low verbosity, and 1.05M context.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt56-luna-default": _preset(
        config=GPT5_6_LUNA_DEFAULT,
        label="GPT-5.6 Luna (medium reasoning)",
        description="High-volume GPT-5.6 Luna with balanced reasoning, verbosity, and 1.05M context.",
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
        label="GPT-5.1 (no reasoning)",
        description="Legacy GPT-5.1 low-verbosity preset with reasoning disabled for speed.",
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
        label="GPT-5.2 (no reasoning)",
        description="Legacy GPT-5.2 low-verbosity preset with reasoning disabled for speed.",
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
    "gpt-5.2-codex": _preset(
        config=GPT5_2_CODEX,
        label="GPT-5.2 Codex",
        description="Coding-optimized GPT-5.2 variant via Responses API with medium reasoning.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt-5.3-codex": _preset(
        config=GPT5_3_CODEX,
        label="GPT-5.3 Codex",
        description="Coding-optimized GPT-5.3 variant via Responses API with medium reasoning.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt-5.4-2026-03-05": _preset(
        config=GPT5_4_2026_03_05,
        label="GPT-5.4 2026-03-05",
        description="Pinned GPT-5.4 March 5 2026 snapshot via Responses API with medium reasoning.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt54-mini-none": _preset(
        config=GPT5_4_MINI_NONE,
        label="GPT-5.4 Mini (no reasoning)",
        description="GPT-5.4 Mini with reasoning disabled and low verbosity for fast, cost-sensitive work.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt54-mini-low": _preset(
        config=GPT5_4_MINI_LOW,
        label="GPT-5.4 Mini (low reasoning)",
        description="GPT-5.4 Mini with low reasoning effort and low verbosity for lightweight analysis.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt54-mini-medium": _preset(
        config=GPT5_4_MINI_MEDIUM,
        label="GPT-5.4 Mini (medium reasoning)",
        description="GPT-5.4 Mini with balanced reasoning and verbosity.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt54-mini-high": _preset(
        config=GPT5_4_MINI_HIGH,
        label="GPT-5.4 Mini (high reasoning)",
        description="GPT-5.4 Mini with high reasoning depth and high verbosity.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt54-mini-xhigh": _preset(
        config=GPT5_4_MINI_XHIGH,
        label="GPT-5.4 Mini (xhigh reasoning)",
        description="GPT-5.4 Mini with maximum supported reasoning depth and high verbosity.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt54-nano-none": _preset(
        config=GPT5_4_NANO_NONE,
        label="GPT-5.4 Nano (no reasoning)",
        description="GPT-5.4 Nano with reasoning disabled and low verbosity for the fastest GPT-5.4 tier.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt54-nano-low": _preset(
        config=GPT5_4_NANO_LOW,
        label="GPT-5.4 Nano (low reasoning)",
        description="GPT-5.4 Nano with low reasoning effort and low verbosity.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt54-nano-medium": _preset(
        config=GPT5_4_NANO_MEDIUM,
        label="GPT-5.4 Nano (medium reasoning)",
        description="GPT-5.4 Nano with balanced reasoning and verbosity.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt54-nano-high": _preset(
        config=GPT5_4_NANO_HIGH,
        label="GPT-5.4 Nano (high reasoning)",
        description="GPT-5.4 Nano with high reasoning depth and high verbosity.",
        provider=ModelProvider.OPENAI,
    ),
    "gpt54-nano-xhigh": _preset(
        config=GPT5_4_NANO_XHIGH,
        label="GPT-5.4 Nano (xhigh reasoning)",
        description="GPT-5.4 Nano with maximum supported reasoning depth and high verbosity.",
        provider=ModelProvider.OPENAI,
    ),
    "deepseek-v4-flash": _preset(
        config=DEEPSEEK_V4_FLASH,
        label="DeepSeek V4 Flash (Thinking, High)",
        description="Fast, cost-efficient DeepSeek V4 model with thinking enabled at high effort and 1M context.",
        provider=ModelProvider.DEEPSEEK,
    ),
    "deepseek-v4-flash-non-reasoning": _preset(
        config=DEEPSEEK_V4_FLASH_NON_REASONING,
        label="DeepSeek V4 Flash (Non-Thinking)",
        description="Fast, cost-efficient DeepSeek V4 model with thinking explicitly disabled and 1M context.",
        provider=ModelProvider.DEEPSEEK,
    ),
    "deepseek-v4-pro": _preset(
        config=DEEPSEEK_V4_PRO,
        label="DeepSeek V4 Pro (Thinking, High)",
        description="Highest-capability DeepSeek V4 model with thinking enabled at high effort and 1M context.",
        provider=ModelProvider.DEEPSEEK,
    ),
    "deepseek-v4-pro-max": _preset(
        config=DEEPSEEK_V4_PRO_MAX,
        label="DeepSeek V4 Pro (Thinking, Max)",
        description="DeepSeek V4 Pro with maximum reasoning effort and 1M context for the hardest tasks.",
        provider=ModelProvider.DEEPSEEK,
    ),
    "deepseek-v4-pro-non-reasoning": _preset(
        config=DEEPSEEK_V4_PRO_NON_REASONING,
        label="DeepSeek V4 Pro (Non-Thinking)",
        description="DeepSeek V4 Pro with thinking explicitly disabled and 1M context.",
        provider=ModelProvider.DEEPSEEK,
    ),
    "deepseek-reasoner": _preset(
        config=DEEPSEEK_REASONER,
        label="DeepSeek Reasoner (Legacy Key → V4 Flash)",
        description=(
            "Compatibility preset for saved configurations. Uses DeepSeek V4 Flash "
            "with thinking enabled at high effort because deepseek-reasoner retires July 24, 2026."
        ),
        provider=ModelProvider.DEEPSEEK,
    ),
    "deepseek-chat": _preset(
        config=DEEPSEEK_CHAT,
        label="DeepSeek Chat (Legacy Key → V4 Flash Non-Thinking)",
        description=(
            "Compatibility preset for saved configurations. Uses DeepSeek V4 Flash "
            "with thinking disabled because deepseek-chat retires July 24, 2026."
        ),
        provider=ModelProvider.DEEPSEEK,
    ),
    "grok-4.3": _preset(
        config=GROK_4_3,
        label="Grok 4.3",
        description="Canonical xAI flagship model with configurable reasoning effort and agentic tool calling.",
        provider=ModelProvider.XAI,
    ),
    "grok-4.3-reasoning-medium": _preset(
        config=GROK_4_3_REASONING_MEDIUM,
        label="Grok 4.3 (Reasoning Medium)",
        description="Canonical Grok 4.3 preset with balanced reasoning effort.",
        provider=ModelProvider.XAI,
    ),
    "grok-4.3-non-reasoning": _preset(
        config=GROK_4_3_NON_REASONING,
        label="Grok 4.3 (Non-Reasoning)",
        description="Canonical Grok 4.3 preset with explicit non-reasoning mode.",
        provider=ModelProvider.XAI,
    ),
    "grok-4-0709": _preset(
        config=GROK_4_0709,
        label="Grok 4 (July 09, Legacy)",
        description="Retired Grok 4 slug preserved for backwards compatibility; xAI routes requests to Grok 4.3.",
        provider=ModelProvider.XAI,
    ),
    "grok-4-fast-reasoning": _preset(
        config=GROK_4_FAST_REASONING,
        label="Grok 4 Fast (Reasoning, Legacy)",
        description=(
            "Retired Grok 4 fast reasoning slug preserved for backwards compatibility; "
            "xAI routes requests to Grok 4.3."
        ),
        provider=ModelProvider.XAI,
    ),
    "grok-4-fast-non-reasoning": _preset(
        config=GROK_4_FAST_NON_REASONING,
        label="Grok 4 Fast (Non-Reasoning, Legacy)",
        description=(
            "Retired Grok 4 fast non-reasoning slug preserved for backwards compatibility; "
            "xAI routes requests to Grok 4.3."
        ),
        provider=ModelProvider.XAI,
    ),
    "grok-4-1-fast-reasoning": _preset(
        config=GROK_4_1_FAST_REASONING,
        label="Grok 4.1 Fast (Reasoning, Legacy)",
        description=(
            "Retired Grok 4.1 fast reasoning slug preserved for backwards compatibility; "
            "xAI routes requests to Grok 4.3."
        ),
        provider=ModelProvider.XAI,
    ),
    "grok-4-1-fast-non-reasoning": _preset(
        config=GROK_4_1_FAST_NON_REASONING,
        label="Grok 4.1 Fast (Non-Reasoning, Legacy)",
        description=(
            "Retired Grok 4.1 fast non-reasoning slug preserved for backwards compatibility; "
            "xAI routes requests to Grok 4.3."
        ),
        provider=ModelProvider.XAI,
    ),
    "grok-build-0.1": _preset(
        config=GROK_BUILD_0_1,
        label="Grok Build 0.1",
        description="Canonical xAI coding model for agentic coding workflows and web development.",
        provider=ModelProvider.XAI,
    ),
    "grok-code-fast": _preset(
        config=GROK_CODE_FAST,
        label="Grok Code Fast (Legacy)",
        description=(
            "Retired Grok code slug preserved for backwards compatibility; "
            "xAI routes requests to Grok Build 0.1."
        ),
        provider=ModelProvider.XAI,
    ),
}


def _build_codex_runtime_presets() -> dict[str, PresetDefinition]:
    return {
        "codex-gpt-5.1-codex": _derive_codex_runtime_preset(BASE_MODEL_PRESETS["gpt-5.1-codex"]),
        "codex-gpt-5.2-codex": _derive_codex_runtime_preset(BASE_MODEL_PRESETS["gpt-5.2-codex"]),
        "codex-gpt-5.3-codex": _derive_codex_runtime_preset(BASE_MODEL_PRESETS["gpt-5.3-codex"]),
        "codex-gpt-5.4": _derive_codex_runtime_preset(
            BASE_MODEL_PRESETS["gpt-5.4-2026-03-05"],
            label="Codex GPT-5.4",
            description=(
                "GPT-5.4 pinned March 5 2026 snapshot routed through the Codex app-server runtime."
            ),
        ),
    }


def _build_claude_code_runtime_presets() -> dict[str, PresetDefinition]:
    return {
        "claude-code-default": _claude_code_runtime_managed_preset(
            model_name=CLAUDE_CODE_RUNTIME_DEFAULT_MODEL,
            label="Claude Code Runtime Default (Moving)",
            description=(
                "Omits the model override so Claude Code uses the account or organization default. "
                "The resolved model can change with runtime and account policy."
            ),
        ),
        "claude-code-best": _claude_code_runtime_managed_preset(
            model_name="best",
            label="Claude Code Best Alias (Moving)",
            description="Uses Claude Code's moving best alias; model, availability, and cost can change.",
        ),
        "claude-code-sonnet": _claude_code_runtime_managed_preset(
            model_name="sonnet",
            label="Claude Code Sonnet Alias (Moving)",
            description="Uses Claude Code's moving sonnet alias rather than a reproducible model ID.",
        ),
        "claude-code-opus": _claude_code_runtime_managed_preset(
            model_name="opus",
            label="Claude Code Opus Alias (Moving)",
            description="Uses Claude Code's moving opus alias rather than a reproducible model ID.",
        ),
        "claude-code-fable": _claude_code_runtime_managed_preset(
            model_name="fable",
            reasoning=ReasoningMode.DYNAMIC,
            label="Claude Code Fable Alias (Moving, Always Adaptive)",
            description=(
                "Uses Claude Code's moving fable alias with runtime-owned adaptive thinking; "
                "requires Claude Code 2.1.170 or later."
            ),
        ),
        "claude-code-sonnet-5": _derive_claude_code_runtime_preset(BASE_MODEL_PRESETS["claude-sonnet-5"]),
        "claude-code-sonnet-5-reasoning-low": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-sonnet-5-reasoning-low"]
        ),
        "claude-code-sonnet-5-reasoning-medium": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-sonnet-5-reasoning-medium"]
        ),
        "claude-code-sonnet-5-reasoning-high": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-sonnet-5-reasoning-high"]
        ),
        "claude-code-sonnet-5-reasoning-xhigh": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-sonnet-5-reasoning-xhigh"]
        ),
        "claude-code-sonnet-5-reasoning-max": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-sonnet-5-reasoning-max"]
        ),
        "claude-code-fable-5-reasoning-low": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-fable-5-reasoning-low"]
        ),
        "claude-code-fable-5-reasoning-medium": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-fable-5-reasoning-medium"]
        ),
        "claude-code-fable-5-reasoning-high": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-fable-5-reasoning-high"]
        ),
        "claude-code-fable-5-reasoning-xhigh": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-fable-5-reasoning-xhigh"]
        ),
        "claude-code-fable-5-reasoning-max": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-fable-5-reasoning-max"]
        ),
        "claude-code-sonnet-4.6": _derive_claude_code_runtime_preset(BASE_MODEL_PRESETS["claude-sonnet-4.6"]),
        "claude-code-sonnet-4.6-reasoning-high": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-sonnet-4.6-reasoning-high"]
        ),
        "claude-code-sonnet-4.6-reasoning-medium": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-sonnet-4.6-reasoning-medium"]
        ),
        "claude-code-sonnet-4.6-reasoning-low": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-sonnet-4.6-reasoning-low"]
        ),
        "claude-code-opus-4.6": _derive_claude_code_runtime_preset(BASE_MODEL_PRESETS["claude-opus-4.6"]),
        "claude-code-opus-4.6-reasoning": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-opus-4.6-reasoning"]
        ),
        "claude-code-opus-4.6-reasoning-medium": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-opus-4.6-reasoning-medium"]
        ),
        "claude-code-opus-4.6-reasoning-low": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-opus-4.6-reasoning-low"]
        ),
        "claude-code-opus-4.6-reasoning-max": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-opus-4.6-reasoning-max"]
        ),
        "claude-code-opus-4.7": _derive_claude_code_runtime_preset(BASE_MODEL_PRESETS["claude-opus-4.7"]),
        "claude-code-opus-4.7-reasoning": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-opus-4.7-reasoning"]
        ),
        "claude-code-opus-4.7-reasoning-medium": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-opus-4.7-reasoning-medium"]
        ),
        "claude-code-opus-4.7-reasoning-low": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-opus-4.7-reasoning-low"]
        ),
        "claude-code-opus-4.7-reasoning-xhigh": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-opus-4.7-reasoning-xhigh"]
        ),
        "claude-code-opus-4.7-reasoning-max": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-opus-4.7-reasoning-max"]
        ),
        "claude-code-opus-4.8": _derive_claude_code_runtime_preset(BASE_MODEL_PRESETS["claude-opus-4.8"]),
        "claude-code-opus-4.8-reasoning": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-opus-4.8-reasoning"]
        ),
        "claude-code-opus-4.8-reasoning-medium": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-opus-4.8-reasoning-medium"]
        ),
        "claude-code-opus-4.8-reasoning-low": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-opus-4.8-reasoning-low"]
        ),
        "claude-code-opus-4.8-reasoning-xhigh": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-opus-4.8-reasoning-xhigh"]
        ),
        "claude-code-opus-4.8-reasoning-max": _derive_claude_code_runtime_preset(
            BASE_MODEL_PRESETS["claude-opus-4.8-reasoning-max"]
        ),
        "claude-code-haiku": _derive_claude_code_runtime_preset(BASE_MODEL_PRESETS["claude-haiku"]),
    }


MODEL_PRESETS: dict[str, PresetDefinition] = {
    **BASE_MODEL_PRESETS,
    **_build_codex_runtime_presets(),
    **_build_claude_code_runtime_presets(),
}

MODEL_PRESET_DEFAULTS: dict[str, str] = {
    "phase1": "gpt56-sol-default",
    "phase2": "gpt56-sol-default",
    "phase3": "gpt56-sol-default",
    "phase4": "gpt56-sol-default",
    "phase5": "gpt56-sol-default",
    "final": "gpt56-sol-default",
    "researcher": "gpt56-sol-default",
}


def _build_default_model_config() -> dict[str, ModelConfig]:
    config: dict[str, ModelConfig] = {}
    for phase, preset_key in MODEL_PRESET_DEFAULTS.items():
        preset: PresetDefinition = MODEL_PRESETS[preset_key]
        config[phase] = preset["config"]
    return config


# Default model configuration (mutated at runtime when overrides are applied)
MODEL_CONFIG = _build_default_model_config()
