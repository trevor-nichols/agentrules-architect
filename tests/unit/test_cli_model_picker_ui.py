from __future__ import annotations

import questionary

from agentrules.cli.ui.settings.models.utils import (
    build_model_choice_state,
    compact_model_label,
)
from agentrules.core.agents.base import ModelProvider
from agentrules.core.configuration import model_presets


def _preset(
    *,
    key: str,
    label: str,
    provider: ModelProvider,
) -> model_presets.PresetInfo:
    return model_presets.PresetInfo(
        key=key,
        label=label,
        description="",
        provider=provider,
    )


def test_model_picker_adds_provider_separators_and_badges() -> None:
    presets = [
        _preset(key="openai-gpt5", label="OpenAI GPT-5", provider=ModelProvider.OPENAI),
        _preset(key="claude-sonnet", label="Claude Sonnet 4.6", provider=ModelProvider.ANTHROPIC),
    ]

    state = build_model_choice_state(
        presets,
        current_key="openai-gpt5",
        default_key="openai-gpt5",
        include_reset=True,
        reset_title="Reset to default",
    )

    separators = [choice for choice in state.choices if isinstance(choice, questionary.Separator)]
    assert [separator.title for separator in separators] == ["---- OpenAI ----", "---- Anthropic ----"]

    openai_choice = next(choice for choice in state.choices if getattr(choice, "value", None) == "openai-gpt5")
    assert isinstance(openai_choice.title, list)
    assert ("class:provider.openai", "[OA]") in openai_choice.title

    anthropic_choice = next(choice for choice in state.choices if getattr(choice, "value", None) == "claude-sonnet")
    assert isinstance(anthropic_choice.title, list)
    assert ("class:provider.anthropic", "[AN]") in anthropic_choice.title


def test_model_picker_group_choice_shows_variant_summary_and_defaults_to_group() -> None:
    presets = [
        _preset(key="gpt5-low", label="OpenAI GPT-5 (low)", provider=ModelProvider.OPENAI),
        _preset(key="gpt5-high", label="OpenAI GPT-5 (high)", provider=ModelProvider.OPENAI),
    ]

    state = build_model_choice_state(
        presets,
        current_key="gpt5-high",
        default_key="gpt5-low",
        include_reset=True,
        reset_title="Reset to default",
    )

    group_choice = next(choice for choice in state.choices if str(getattr(choice, "value", "")).startswith("__GROUP__"))
    assert isinstance(group_choice.title, list)
    assert ("class:text", "GPT-5") in group_choice.title
    assert ("class:status.variant", "2 options | current: High") in group_choice.title
    assert state.default_value == group_choice.value


def test_compact_model_label_removes_provider_prefixes() -> None:
    assert compact_model_label("OpenAI O3", "openai", "OpenAI") == "O3"
    assert compact_model_label("Codex: gpt-5.3-codex", "codex", "Codex App Server") == "gpt-5.3-codex"
    assert compact_model_label("Claude Sonnet 4.6", "anthropic", "Anthropic") == "Claude Sonnet 4.6"
