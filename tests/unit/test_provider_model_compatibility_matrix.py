"""Cross-provider model registry and request-contract compatibility matrix."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from agentrules.config.agents import MODEL_PRESETS
from agentrules.core.agents.anthropic.request_builder import prepare_request as prepare_anthropic
from agentrules.core.agents.base import ModelProvider, ReasoningMode
from agentrules.core.agents.deepseek.config import resolve_model_defaults as resolve_deepseek_defaults
from agentrules.core.agents.deepseek.request_builder import prepare_request as prepare_deepseek
from agentrules.core.agents.gemini.capabilities import resolve_thinking_level
from agentrules.core.agents.openai.config import resolve_model_defaults as resolve_openai_defaults
from agentrules.core.agents.openai.request_builder import prepare_request as prepare_openai
from agentrules.core.agents.xai.config import resolve_model_defaults as resolve_xai_defaults
from agentrules.core.agents.xai.request_builder import prepare_request as prepare_xai
from agentrules.core.configuration import model_presets
from agentrules.core.types.models import CLAUDE_CODE_RUNTIME_DEFAULT_MODEL, ModelConfig


@dataclass(frozen=True)
class ModelContract:
    preset_key: str
    provider: ModelProvider
    model_name: str
    reasoning: ReasoningMode
    context_limit: int
    wire_reasoning: object
    anthropic_effort: str | None = None


DIRECT_MODEL_CONTRACTS = (
    ModelContract(
        "deepseek-v4-flash",
        ModelProvider.DEEPSEEK,
        "deepseek-v4-flash",
        ReasoningMode.HIGH,
        1_000_000,
        ("enabled", "high"),
    ),
    ModelContract(
        "deepseek-v4-flash-non-reasoning",
        ModelProvider.DEEPSEEK,
        "deepseek-v4-flash",
        ReasoningMode.DISABLED,
        1_000_000,
        ("disabled", None),
    ),
    ModelContract(
        "deepseek-v4-pro", ModelProvider.DEEPSEEK, "deepseek-v4-pro", ReasoningMode.HIGH, 1_000_000, ("enabled", "high")
    ),
    ModelContract(
        "deepseek-v4-pro-max",
        ModelProvider.DEEPSEEK,
        "deepseek-v4-pro",
        ReasoningMode.XHIGH,
        1_000_000,
        ("enabled", "max"),
    ),
    ModelContract(
        "deepseek-v4-pro-non-reasoning",
        ModelProvider.DEEPSEEK,
        "deepseek-v4-pro",
        ReasoningMode.DISABLED,
        1_000_000,
        ("disabled", None),
    ),
    ModelContract(
        "gpt56-sol-none", ModelProvider.OPENAI, "gpt-5.6-sol", ReasoningMode.DISABLED, 1_050_000, ("responses", "none")
    ),
    ModelContract(
        "gpt56-sol-low", ModelProvider.OPENAI, "gpt-5.6-sol", ReasoningMode.LOW, 1_050_000, ("responses", "low")
    ),
    ModelContract(
        "gpt56-sol-default",
        ModelProvider.OPENAI,
        "gpt-5.6-sol",
        ReasoningMode.MEDIUM,
        1_050_000,
        ("responses", "medium"),
    ),
    ModelContract(
        "gpt56-sol-high", ModelProvider.OPENAI, "gpt-5.6-sol", ReasoningMode.HIGH, 1_050_000, ("responses", "high")
    ),
    ModelContract(
        "gpt56-sol-xhigh", ModelProvider.OPENAI, "gpt-5.6-sol", ReasoningMode.XHIGH, 1_050_000, ("responses", "xhigh")
    ),
    ModelContract(
        "gpt56-sol-max", ModelProvider.OPENAI, "gpt-5.6-sol", ReasoningMode.MAX, 1_050_000, ("responses", "max")
    ),
    ModelContract(
        "gpt56-terra-default",
        ModelProvider.OPENAI,
        "gpt-5.6-terra",
        ReasoningMode.MEDIUM,
        1_050_000,
        ("responses", "medium"),
    ),
    ModelContract(
        "gpt56-terra-high", ModelProvider.OPENAI, "gpt-5.6-terra", ReasoningMode.HIGH, 1_050_000, ("responses", "high")
    ),
    ModelContract(
        "gpt56-luna-low", ModelProvider.OPENAI, "gpt-5.6-luna", ReasoningMode.LOW, 1_050_000, ("responses", "low")
    ),
    ModelContract(
        "gpt56-luna-default",
        ModelProvider.OPENAI,
        "gpt-5.6-luna",
        ReasoningMode.MEDIUM,
        1_050_000,
        ("responses", "medium"),
    ),
    ModelContract(
        "claude-sonnet-5",
        ModelProvider.ANTHROPIC,
        "claude-sonnet-5",
        ReasoningMode.DISABLED,
        1_000_000,
        ("disabled", None),
    ),
    ModelContract(
        "claude-sonnet-5-reasoning-low",
        ModelProvider.ANTHROPIC,
        "claude-sonnet-5",
        ReasoningMode.DYNAMIC,
        1_000_000,
        ("adaptive", "low"),
        "low",
    ),
    ModelContract(
        "claude-sonnet-5-reasoning-medium",
        ModelProvider.ANTHROPIC,
        "claude-sonnet-5",
        ReasoningMode.DYNAMIC,
        1_000_000,
        ("adaptive", "medium"),
        "medium",
    ),
    ModelContract(
        "claude-sonnet-5-reasoning-high",
        ModelProvider.ANTHROPIC,
        "claude-sonnet-5",
        ReasoningMode.DYNAMIC,
        1_000_000,
        ("adaptive", "high"),
        "high",
    ),
    ModelContract(
        "claude-sonnet-5-reasoning-xhigh",
        ModelProvider.ANTHROPIC,
        "claude-sonnet-5",
        ReasoningMode.DYNAMIC,
        1_000_000,
        ("adaptive", "xhigh"),
        "xhigh",
    ),
    ModelContract(
        "claude-sonnet-5-reasoning-max",
        ModelProvider.ANTHROPIC,
        "claude-sonnet-5",
        ReasoningMode.DYNAMIC,
        1_000_000,
        ("adaptive", "max"),
        "max",
    ),
    ModelContract(
        "claude-fable-5-reasoning-low",
        ModelProvider.ANTHROPIC,
        "claude-fable-5",
        ReasoningMode.DYNAMIC,
        1_000_000,
        (None, "low"),
        "low",
    ),
    ModelContract(
        "claude-fable-5-reasoning-medium",
        ModelProvider.ANTHROPIC,
        "claude-fable-5",
        ReasoningMode.DYNAMIC,
        1_000_000,
        (None, "medium"),
        "medium",
    ),
    ModelContract(
        "claude-fable-5-reasoning-high",
        ModelProvider.ANTHROPIC,
        "claude-fable-5",
        ReasoningMode.DYNAMIC,
        1_000_000,
        (None, "high"),
        "high",
    ),
    ModelContract(
        "claude-fable-5-reasoning-xhigh",
        ModelProvider.ANTHROPIC,
        "claude-fable-5",
        ReasoningMode.DYNAMIC,
        1_000_000,
        (None, "xhigh"),
        "xhigh",
    ),
    ModelContract(
        "claude-fable-5-reasoning-max",
        ModelProvider.ANTHROPIC,
        "claude-fable-5",
        ReasoningMode.DYNAMIC,
        1_000_000,
        (None, "max"),
        "max",
    ),
    ModelContract(
        "claude-opus", ModelProvider.ANTHROPIC, "claude-opus-4-8", ReasoningMode.DISABLED, 1_000_000, (None, None)
    ),
    ModelContract(
        "claude-opus-reasoning",
        ModelProvider.ANTHROPIC,
        "claude-opus-4-8",
        ReasoningMode.DYNAMIC,
        1_000_000,
        ("adaptive", None),
    ),
    ModelContract("grok-4.5", ModelProvider.XAI, "grok-4.5", ReasoningMode.HIGH, 500_000, "high"),
    ModelContract("grok-4.5-reasoning-medium", ModelProvider.XAI, "grok-4.5", ReasoningMode.MEDIUM, 500_000, "medium"),
    ModelContract("grok-4.5-reasoning-low", ModelProvider.XAI, "grok-4.5", ReasoningMode.LOW, 500_000, "low"),
    ModelContract(
        "grok-4.20-reasoning", ModelProvider.XAI, "grok-4.20-0309-reasoning", ReasoningMode.ENABLED, 1_000_000, None
    ),
    ModelContract(
        "grok-4.20-non-reasoning",
        ModelProvider.XAI,
        "grok-4.20-0309-non-reasoning",
        ReasoningMode.DISABLED,
        1_000_000,
        None,
    ),
    ModelContract(
        "gemini-3.5-flash", ModelProvider.GEMINI, "gemini-3.5-flash", ReasoningMode.MEDIUM, 1_048_576, "medium"
    ),
    ModelContract(
        "gemini-3.1-pro-preview",
        ModelProvider.GEMINI,
        "gemini-3.1-pro-preview",
        ReasoningMode.DYNAMIC,
        1_048_576,
        "high",
    ),
    ModelContract(
        "gemini-3.1-flash-lite",
        ModelProvider.GEMINI,
        "gemini-3.1-flash-lite",
        ReasoningMode.MINIMAL,
        1_048_576,
        "minimal",
    ),
)


@pytest.mark.parametrize("contract", DIRECT_MODEL_CONTRACTS, ids=lambda row: row.preset_key)
def test_direct_provider_model_contract_matrix(contract: ModelContract) -> None:
    config = model_presets.get_model_config_for_preset_key(contract.preset_key)

    assert config is not None
    assert config.provider == contract.provider
    assert config.model_name == contract.model_name
    assert config.reasoning == contract.reasoning
    assert config.max_input_tokens == contract.context_limit
    assert config.anthropic_effort == contract.anthropic_effort
    assert _resolve_wire_reasoning(config) == contract.wire_reasoning


@pytest.mark.parametrize(
    ("legacy_key", "replacement_key"),
    [
        (legacy_key, info.replacement_key)
        for legacy_key, info in model_presets.DEPRECATED_PRESETS.items()
        if info.replacement_key is not None
    ],
)
def test_every_compatibility_key_resolves_to_its_canonical_replacement(
    legacy_key: str,
    replacement_key: str,
) -> None:
    assert legacy_key in MODEL_PRESETS
    assert replacement_key in MODEL_PRESETS
    assert model_presets.resolve_runtime_preset_key(legacy_key) == replacement_key
    assert model_presets.get_model_config_for_preset_key(legacy_key) == MODEL_PRESETS[replacement_key]["config"]


def test_local_runtime_selection_modes_remain_runtime_owned() -> None:
    codex_default = model_presets.get_model_config_for_preset_key(model_presets.CODEX_RUNTIME_DEFAULT_KEY)
    codex_future = model_presets.get_model_config_for_preset_key(
        model_presets.make_codex_runtime_preset_key(
            "gpt-5.6-sol",
            reasoning_effort="extreme",
        )
    )

    assert codex_default is not None
    assert codex_default.provider == ModelProvider.CODEX
    assert codex_default.model_name == model_presets.CODEX_RUNTIME_DEFAULT_MODEL_NAME
    assert codex_default.reasoning == ReasoningMode.DYNAMIC
    assert codex_future is not None
    assert codex_future.runtime_reasoning_effort == "extreme"

    claude_runtime_modes = {
        "claude-code-default": CLAUDE_CODE_RUNTIME_DEFAULT_MODEL,
        "claude-code-best": "best",
        "claude-code-sonnet": "sonnet",
        "claude-code-opus": "opus",
        "claude-code-fable": "fable",
    }
    for preset_key, expected_model in claude_runtime_modes.items():
        preset = MODEL_PRESETS[preset_key]
        assert preset["provider"] == ModelProvider.CLAUDE_CODE
        assert preset["config"].model_name == expected_model
        assert "Moving" in preset["label"]


def _resolve_wire_reasoning(config: ModelConfig) -> object:
    provider = config.provider
    if provider == ModelProvider.OPENAI:
        defaults = resolve_openai_defaults(config.model_name)
        prepared = prepare_openai(
            model_name=config.model_name,
            content="contract",
            reasoning=config.reasoning,
            temperature=config.temperature,
            tools=None,
            text_verbosity=config.text_verbosity,
            use_responses_api=defaults.use_responses_api,
        )
        reasoning = prepared.payload.get("reasoning") or {}
        return (prepared.api, reasoning.get("effort"))

    if provider == ModelProvider.ANTHROPIC:
        prepared = prepare_anthropic(
            model_name=config.model_name,
            prompt="contract",
            reasoning=config.reasoning,
            effort=config.anthropic_effort,
            tools=None,
        )
        thinking = prepared.payload.get("thinking") or {}
        output_config = prepared.payload.get("output_config") or {}
        return (thinking.get("type"), output_config.get("effort"))

    if provider == ModelProvider.DEEPSEEK:
        prepared = prepare_deepseek(
            model_name=config.model_name,
            content="contract",
            reasoning=config.reasoning,
            defaults=resolve_deepseek_defaults(config.model_name),
            tools=None,
        )
        thinking = prepared.payload["extra_body"]["thinking"]["type"]
        return (thinking, prepared.payload.get("reasoning_effort"))

    if provider == ModelProvider.XAI:
        prepared = prepare_xai(
            model_name=config.model_name,
            content="contract",
            reasoning=config.reasoning,
            defaults=resolve_xai_defaults(config.model_name),
            tools=None,
        )
        return prepared.payload.get("reasoning_effort")

    if provider == ModelProvider.GEMINI:
        thinking_levels = SimpleNamespace(
            MINIMAL="minimal",
            LOW="low",
            MEDIUM="medium",
            HIGH="high",
        )
        return resolve_thinking_level(
            model_name=config.model_name,
            reasoning_mode=config.reasoning,
            thinking_level_enum=thinking_levels,
        )

    raise AssertionError(f"No direct request contract for provider {provider!r}")
