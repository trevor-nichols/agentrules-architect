from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

import questionary
from rich.console import Console

from agentrules.cli.context import CliContext
from agentrules.cli.ui.settings import models as model_settings
from agentrules.cli.ui.settings.models import describe_researcher_phase_status
from agentrules.cli.ui.settings.models import researcher as researcher_settings
from agentrules.cli.ui.settings.models.utils import (
    build_model_choice_state,
    compact_model_label,
    effective_current_labels,
    filter_deprecated_presets_for_selection,
)
from agentrules.core.agents.base import ModelProvider
from agentrules.core.configuration import model_presets
from agentrules.core.configuration.services.claude_code import ClaudeCodeVersion


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
        _preset(key="claude-code-sonnet", label="Claude Code Claude Sonnet 4.6", provider=ModelProvider.CLAUDE_CODE),
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
    assert [separator.title for separator in separators] == [
        "---- OpenAI ----",
        "---- Claude Code ----",
        "---- Anthropic ----",
    ]

    openai_choice = next(choice for choice in state.choices if getattr(choice, "value", None) == "openai-gpt5")
    assert isinstance(openai_choice.title, list)
    assert ("class:provider.openai", "[OA]") in openai_choice.title

    claude_code_choice = next(
        choice for choice in state.choices if getattr(choice, "value", None) == "claude-code-sonnet"
    )
    assert isinstance(claude_code_choice.title, list)
    assert ("class:provider.claude_code", "[CC]") in claude_code_choice.title

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


def test_gemini_argon_picker_discloses_paid_tier_on_model_group() -> None:
    presets = [
        model_presets.get_preset_info(key)
        for key in ("gemini-4-argon", "gemini-4-argon-reasoning-low", "gemini-4-argon-reasoning-high")
    ]
    assert all(preset is not None for preset in presets)
    state = build_model_choice_state(
        [preset for preset in presets if preset is not None],
        current_key=None,
        default_key=None,
        include_reset=False,
        reset_title="Reset",
    )

    paid_group = next(choice for choice in state.choices if choice.value in state.group_selection_map)
    assert "Gemini 4 Argon [Paid Tier]" in str(paid_group.title)


def test_compact_model_label_removes_provider_prefixes() -> None:
    assert compact_model_label("OpenAI O3", "openai", "OpenAI") == "O3"
    assert compact_model_label("Codex: gpt-5.3-codex", "codex", "Codex App Server") == "gpt-5.3-codex"
    assert (
        compact_model_label("Claude Code Claude Sonnet 4.6", "claude_code", "Claude Code")
        == "Claude Sonnet 4.6"
    )
    assert compact_model_label("Claude Sonnet 4.6", "anthropic", "Anthropic") == "Claude Sonnet 4.6"


def test_researcher_status_mentions_runtime_preset_when_claude_code_available() -> None:
    model_label, provider_label = describe_researcher_phase_status(
        configured_researcher_key="gpt55-default",
        researcher_key="gpt55-default",
        researcher_mode="off",
        tavily_available=False,
        offline_mode=False,
        provider_availability={
            ModelProvider.CLAUDE_CODE.value: True,
            ModelProvider.CODEX.value: False,
        },
    )

    assert model_label == "Needs Tavily or runtime preset"
    assert provider_label == ""


def test_effective_current_labels_marks_runtime_replacement_for_deprecated_saved_preset() -> None:
    model_label, provider_label = effective_current_labels(
        configured_key="gemini-3-pro-preview",
        effective_key="gemini-3.1-pro-preview",
    )

    assert model_label == "Gemini 3.1 Pro (Preview) [saved deprecated preset]"
    assert provider_label == "Google Gemini"


def test_selection_filter_hides_deprecated_presets_when_not_current() -> None:
    deprecated = model_presets.get_preset_info("gemini-3-pro-preview")
    replacement = model_presets.get_preset_info("gemini-3.1-pro-preview")
    assert deprecated is not None
    assert replacement is not None

    filtered = filter_deprecated_presets_for_selection(
        [deprecated, replacement],
        preserved_key=None,
    )

    assert [preset.key for preset in filtered] == ["gemini-3.1-pro-preview"]


def test_selection_filter_preserves_current_deprecated_preset_with_label() -> None:
    deprecated = model_presets.get_preset_info("gemini-3-pro-preview")
    replacement = model_presets.get_preset_info("gemini-3.1-pro-preview")
    assert deprecated is not None
    assert replacement is not None

    filtered = filter_deprecated_presets_for_selection(
        [deprecated, replacement],
        preserved_key="gemini-3-pro-preview",
    )

    assert [preset.key for preset in filtered] == ["gemini-3-pro-preview", "gemini-3.1-pro-preview"]
    assert filtered[0].label.endswith("[deprecated]")


def test_gemini_picker_discloses_scheduled_redirects_and_upstream_aliases() -> None:
    flash = model_presets.get_preset_info("gemini-flash")
    pro = model_presets.get_preset_info("gemini-pro")
    flash37 = model_presets.get_preset_info("gemini-3.7-flash")
    flash35 = model_presets.get_preset_info("gemini-3.5-flash")
    assert flash is not None
    assert pro is not None
    assert flash37 is not None
    assert flash35 is not None

    state = build_model_choice_state(
        [flash, pro, flash37, flash35],
        current_key="gemini-flash",
        default_key=None,
        include_reset=False,
        reset_title="Reset",
    )
    rendered_titles = [str(choice.title) for choice in state.choices if hasattr(choice, "title")]

    assert any("2.5 Flash [redirects 2026-12-01]" in title for title in rendered_titles)
    assert any("2.5 Pro [redirects 2026-12-01]" in title for title in rendered_titles)
    assert any("3.7 Flash (API Alias → 3.8 Flash" in title for title in rendered_titles)
    assert any("3.5 Flash (API Alias → 3.6 Flash" in title for title in rendered_titles)
    assert all("2026-10-16" not in title for title in rendered_titles)


def test_claude_code_picker_filters_pins_by_exact_runtime_version(monkeypatch) -> None:
    keys = (
        "claude-code-haiku-alias",
        "claude-code-fable-5.1",
        "claude-code-fable-5.2",
        "claude-code-opus-5.5",
        "claude-code-sonnet-5.5",
        "claude-code-haiku-5.5",
    )
    presets = [model_presets.get_preset_info(key) for key in keys]
    assert all(preset is not None for preset in presets)
    available_presets = [preset for preset in presets if preset is not None]
    runtime_version: ClaudeCodeVersion | None = ClaudeCodeVersion(2, 1, 280)
    monkeypatch.setattr(
        model_settings.configuration.CONFIG_MANAGER,
        "get_claude_code_runtime_version",
        lambda: runtime_version,
    )

    filtered = model_settings._filter_claude_code_presets_for_runtime(
        available_presets,
        preserved_key=None,
    )
    assert [preset.key for preset in filtered] == [
        "claude-code-haiku-alias",
        "claude-code-fable-5.1",
        "claude-code-opus-5.5",
    ]

    fable_key = "claude-code-fable-5.2"
    runtime_version = ClaudeCodeVersion(2, 1, 320)
    filtered = model_settings._filter_claude_code_presets_for_runtime(available_presets, preserved_key=None)
    assert fable_key not in [preset.key for preset in filtered]
    runtime_version = ClaudeCodeVersion(2, 1, 321)
    filtered = model_settings._filter_claude_code_presets_for_runtime(available_presets, preserved_key=None)
    fable = next(preset for preset in filtered if preset.key == fable_key)
    assert "30-day retention" in fable.label
    assert "medium effort" in fable.label

    runtime_version = None
    preserved = model_settings._filter_claude_code_presets_for_runtime(
        available_presets,
        preserved_key=fable_key,
    )
    assert [preset.key for preset in preserved] == ["claude-code-haiku-alias", fable_key]
    assert "runtime version unverified; needs 2.1.321+" in preserved[-1].label


def test_configure_models_preserves_saved_deprecated_preset_in_picker(monkeypatch) -> None:
    context = CliContext(console=Console(record=True, width=120))
    captured: dict[str, object] = {}
    deprecated = model_presets.get_preset_info("gemini-3-pro-preview")
    replacement = model_presets.get_preset_info("gemini-3.1-pro-preview")
    assert deprecated is not None
    assert replacement is not None

    class _Prompt:
        def __init__(self, answer: str | None) -> None:
            self._answer = answer

        def ask(self) -> str | None:
            return self._answer

    selections = iter(("phase3", "__DONE__"))

    monkeypatch.setattr(
        model_settings.questionary,
        "select",
        lambda *_args, **_kwargs: _Prompt(next(selections)),
    )
    monkeypatch.setattr(
        model_settings.configuration,
        "get_provider_availability",
        lambda: {ModelProvider.GEMINI.value: True},
    )
    monkeypatch.setattr(
        model_settings.configuration,
        "get_configured_presets",
        lambda: {"phase3": "gemini-3-pro-preview"},
    )
    monkeypatch.setattr(
        model_settings.configuration,
        "get_active_presets",
        lambda: {"phase3": "gemini-3.1-pro-preview"},
    )
    monkeypatch.setattr(model_settings.configuration, "get_researcher_mode", lambda: "off")
    monkeypatch.setattr(model_settings.configuration, "has_tavily_credentials", lambda: True)
    monkeypatch.setattr(
        model_settings.configuration,
        "get_available_presets_for_phase",
        lambda _phase, _availability: [deprecated, replacement],
    )
    monkeypatch.setattr(
        model_settings,
        "_load_runtime_codex_catalog",
        lambda _availability: model_settings._RuntimeCodexCatalog(
            visible_presets=(),
            executable_identities=None,
        ),
    )

    def _capture_general_phase(
        _context,
        _phase,
        _title,
        presets,
        current_key,
        default_key,
    ) -> bool:
        captured["preset_keys"] = [preset.key for preset in presets]
        captured["preset_labels"] = [preset.label for preset in presets]
        captured["current_key"] = current_key
        captured["default_key"] = default_key
        return False

    monkeypatch.setattr(model_settings, "_configure_general_phase", _capture_general_phase)

    model_settings.configure_models(context)

    assert captured["preset_keys"] == ["gemini-3-pro-preview", "gemini-3.1-pro-preview"]
    assert captured["current_key"] == "gemini-3-pro-preview"
    assert captured["default_key"] == model_presets.get_default_preset_key("phase3")
    preset_labels = captured["preset_labels"]
    assert isinstance(preset_labels, list)
    assert any(str(label).endswith("[deprecated]") for label in preset_labels)


def test_general_phase_selection_warns_when_deprecated_preset_selected(monkeypatch) -> None:
    context = CliContext(console=Console(record=True, width=120))
    saved: list[tuple[str, str | None]] = []
    preset = model_presets.get_preset_info("gemini-3-pro-preview")
    assert preset is not None

    class _Prompt:
        def ask(self) -> str:
            return "gemini-3-pro-preview"

    monkeypatch.setattr(model_settings.questionary, "select", lambda *_args, **_kwargs: _Prompt())
    monkeypatch.setattr(
        model_settings.configuration,
        "save_phase_model",
        lambda phase, key: saved.append((phase, key)),
    )

    updated = model_settings._configure_general_phase(
        context,
        "phase3",
        "Phase 3 – Deep Analysis",
        [preset],
        current_key=None,
        default_key=None,
    )

    assert updated is True
    assert saved == [("phase3", "gemini-3.1-pro-preview")]
    output = " ".join(context.console.export_text().split())
    assert "Selected preset is deprecated." in output
    assert "Saved replacement Gemini 3.1 Pro (Preview) [Google Gemini]." in output


def test_general_phase_selection_warns_before_scheduled_cutover(monkeypatch) -> None:
    context = CliContext(console=Console(record=True, width=120))
    saved: list[tuple[str, str | None]] = []
    monkeypatch.setattr(
        model_presets,
        "datetime",
        SimpleNamespace(now=lambda tz: datetime(2026, 11, 30, tzinfo=tz)),
    )
    preset = model_presets.get_preset_info("gemini-pro")
    assert preset is not None

    class _Prompt:
        def ask(self) -> str:
            return "gemini-pro"

    monkeypatch.setattr(model_settings.questionary, "select", lambda *_args, **_kwargs: _Prompt())
    monkeypatch.setattr(
        model_settings.configuration,
        "save_phase_model",
        lambda phase, key: saved.append((phase, key)),
    )

    updated = model_settings._configure_general_phase(
        context,
        "phase3",
        "Phase 3 – Deep Analysis",
        [preset],
        current_key="gemini-pro",
        default_key=None,
    )

    assert updated is True
    assert saved == [("phase3", "gemini-pro")]
    output = " ".join(context.console.export_text().split())
    assert "Selected preset is deprecated." in output
    assert "December 1, 2026" in output
    assert "Prefer Gemini 3.8 Flash" in output
    assert "Saved replacement" not in output


def test_researcher_selection_names_replacement_after_scheduled_cutover(monkeypatch) -> None:
    context = CliContext(console=Console(record=True, width=120))
    events: list[tuple[str, str | None]] = []
    monkeypatch.setattr(
        model_presets,
        "datetime",
        SimpleNamespace(now=lambda tz: datetime(2026, 12, 1, tzinfo=tz)),
    )
    preset = model_presets.get_preset_info("gemini-flash")
    assert preset is not None

    class _Prompt:
        def __init__(self, answer: str) -> None:
            self._answer = answer

        def ask(self) -> str:
            return self._answer

    selections = iter(("on", "gemini-flash"))

    monkeypatch.setattr(
        researcher_settings.questionary,
        "select",
        lambda *_args, **_kwargs: _Prompt(next(selections)),
    )
    monkeypatch.setattr(
        researcher_settings.configuration,
        "save_phase_model",
        lambda phase, key: events.append((phase, key)),
    )
    monkeypatch.setattr(
        researcher_settings.configuration,
        "save_researcher_mode",
        lambda mode: events.append(("researcher_mode", mode)),
    )

    updated = researcher_settings.configure_researcher_phase(
        context,
        [preset],
        current_key="gemini-flash",
        default_key=None,
        current_mode="off",
        tavily_available=True,
        offline_mode=False,
    )

    assert updated is True
    assert events == [("researcher", "gemini-3.5-flash-lite"), ("researcher_mode", "on")]
    output = " ".join(context.console.export_text().split())
    assert "Selected preset is deprecated." in output
    assert "minimal thinking" in output
    assert "Saved replacement Gemini 3.5 Flash-Lite (Minimal Thinking, Recommended for Throughput) [Google Gemini]." in output
