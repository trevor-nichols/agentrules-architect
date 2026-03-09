from __future__ import annotations

from rich.console import Console

from agentrules.cli.context import CliContext
from agentrules.cli.services.codex_runtime import CodexRuntimeDiagnostics
from agentrules.cli.services.configuration import CodexRuntimeState
from agentrules.cli.ui.settings import codex as codex_settings
from agentrules.cli.ui.settings import models as model_settings
from agentrules.cli.ui.settings.codex import build_runtime_guidance
from agentrules.cli.ui.settings.menu import SETTINGS_CATEGORY_ENTRIES, build_settings_category_choices
from agentrules.cli.ui.settings.models import describe_researcher_phase_status
from agentrules.core.agents.codex import CodexAccountSummary, CodexModelInfo, CodexModelReasoningOption
from agentrules.core.configuration import model_presets


def test_settings_menu_separates_provider_keys_and_codex_runtime() -> None:
    choices = build_settings_category_choices()

    assert [choice.title for choice in choices] == [entry[0] for entry in SETTINGS_CATEGORY_ENTRIES]
    assert ("Provider API keys", "providers") in SETTINGS_CATEGORY_ENTRIES
    assert ("Codex runtime", "codex") in SETTINGS_CATEGORY_ENTRIES


def test_researcher_status_mentions_codex_as_alternative_when_tavily_missing() -> None:
    model_label, provider_label = describe_researcher_phase_status(
        researcher_key="gpt5-mini",
        researcher_mode="off",
        tavily_available=False,
        offline_mode=False,
        provider_availability={"codex": True},
    )

    assert model_label == "Needs Tavily or Codex preset"
    assert provider_label == ""


def test_researcher_status_uses_selected_codex_preset_without_tavily() -> None:
    model_label, provider_label = describe_researcher_phase_status(
        researcher_key="codex-gpt-5.3-codex",
        researcher_mode="on",
        tavily_available=False,
        offline_mode=False,
        provider_availability={"codex": True},
    )

    assert model_label.startswith("Codex GPT-5.3 Codex")
    assert model_label.endswith("(On)")
    assert provider_label == "Codex App Server"


def test_codex_runtime_guidance_describes_inherit_mode_and_next_step() -> None:
    state = CodexRuntimeState(
        cli_path="codex",
        home_strategy="inherit",
        managed_home=None,
        effective_home="/tmp/codex-home",
        executable_path="/usr/local/bin/codex",
        is_available=True,
    )
    diagnostics = CodexRuntimeDiagnostics(
        executable_path="/usr/local/bin/codex",
        codex_home="/tmp/codex-home",
        command=("codex", "app-server"),
        user_agent="codex/1.0",
        models=(),
    )

    guidance = build_runtime_guidance(state, diagnostics)

    assert any("reuses your existing Codex CLI state" in note for note in guidance)
    assert any("Sign in with ChatGPT here" in note for note in guidance)


def test_codex_runtime_guidance_describes_managed_mode_after_sign_in() -> None:
    state = CodexRuntimeState(
        cli_path="codex",
        home_strategy="managed",
        managed_home=None,
        effective_home="/tmp/managed-codex-home",
        executable_path="/usr/local/bin/codex",
        is_available=True,
    )
    diagnostics = CodexRuntimeDiagnostics(
        executable_path="/usr/local/bin/codex",
        codex_home="/tmp/managed-codex-home",
        command=("codex", "app-server"),
        user_agent="codex/1.0",
        account=CodexAccountSummary(
            account_type="chatgpt",
            auth_mode="chatgpt",
            email="codex@example.com",
            plan_type="pro",
            requires_openai_auth=True,
            is_authenticated=True,
            raw_account={"type": "chatgpt"},
        ),
        models=(
            CodexModelInfo(
                id="gpt-5.3-codex",
                model="gpt-5.3-codex",
                display_name="GPT-5.3 Codex",
                description="",
                hidden=False,
                default_reasoning_effort="medium",
                supported_reasoning_efforts=(),
                input_modalities=("text",),
                supports_personality=False,
                is_default=True,
                upgrade=None,
                availability_message=None,
                raw={},
            ),
        ),
    )

    guidance = build_runtime_guidance(state, diagnostics)

    assert any("AgentRules-owned CODEX_HOME" in note for note in guidance)
    assert any("choose a Codex preset" in note for note in guidance)


def test_codex_runtime_models_view_waits_for_acknowledgement(monkeypatch) -> None:
    state = CodexRuntimeState(
        cli_path="codex",
        home_strategy="managed",
        managed_home=None,
        effective_home="/tmp/codex-home",
        executable_path="/usr/local/bin/codex",
        is_available=True,
    )
    diagnostics = CodexRuntimeDiagnostics(
        executable_path="/usr/local/bin/codex",
        codex_home="/tmp/codex-home",
        command=("codex", "app-server"),
        user_agent="codex/1.0",
        models=(
            CodexModelInfo(
                id="gpt-5.3-codex",
                model="gpt-5.3-codex",
                display_name="GPT-5.3 Codex",
                description="Frontier coding model.",
                hidden=False,
                default_reasoning_effort="medium",
                supported_reasoning_efforts=(),
                input_modalities=("text",),
                supports_personality=True,
                is_default=True,
                upgrade=None,
                availability_message=None,
                raw={},
            ),
        ),
    )
    context = CliContext(console=Console(record=True))
    events: list[str] = []

    class _Prompt:
        def __init__(self, answer: str | None, event_label: str) -> None:
            self._answer = answer
            self._event_label = event_label

        def ask(self) -> str | None:
            events.append(self._event_label)
            return self._answer

    selections = iter(("__MODELS__", "__BACK__"))

    def _select(*_args, **_kwargs):
        answer = next(selections)
        return _Prompt(answer, f"select:{answer}")

    def _text(*args, **_kwargs):
        prompt = args[0] if args else ""
        events.append(f"prompt:{prompt}")
        return _Prompt("", "models_ack")

    monkeypatch.setattr(codex_settings.configuration, "get_codex_runtime_state", lambda: state)
    monkeypatch.setattr(
        codex_settings.codex_runtime,
        "get_codex_runtime_diagnostics",
        lambda **_kwargs: diagnostics,
    )
    monkeypatch.setattr(codex_settings.questionary, "select", _select)
    monkeypatch.setattr(codex_settings.questionary, "text", _text)
    monkeypatch.setattr(codex_settings, "_render_runtime_summary", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(codex_settings, "_render_models_table", lambda *_args, **_kwargs: events.append("render_models"))

    codex_settings.configure_codex_runtime(context)

    assert events == [
        "select:__MODELS__",
        "render_models",
        "prompt:Press Enter to return to Codex runtime actions:",
        "models_ack",
        "select:__BACK__",
    ]


def test_model_settings_loads_runtime_codex_presets_from_catalog(monkeypatch) -> None:
    diagnostics = CodexRuntimeDiagnostics(
        executable_path="/usr/local/bin/codex",
        codex_home="/tmp/codex-home",
        command=("codex", "app-server"),
        user_agent="codex/1.0",
        models=(
            CodexModelInfo(
                id="gpt-5.3-codex",
                model="gpt-5.3-codex",
                display_name="GPT-5.3 Codex",
                description="Already in static presets.",
                hidden=False,
                default_reasoning_effort="medium",
                supported_reasoning_efforts=(),
                input_modalities=("text",),
                supports_personality=True,
                is_default=True,
                upgrade=None,
                availability_message=None,
                raw={},
            ),
            CodexModelInfo(
                id="gpt-6-codex-preview",
                model="gpt-6-codex-preview",
                display_name="GPT-6 Codex Preview",
                description="Runtime-only model.",
                hidden=False,
                default_reasoning_effort="medium",
                supported_reasoning_efforts=(),
                input_modalities=("text",),
                supports_personality=True,
                is_default=False,
                upgrade=None,
                availability_message=None,
                raw={},
            ),
        ),
    )

    monkeypatch.setattr(
        model_settings.codex_runtime,
        "get_codex_runtime_diagnostics",
        lambda **_kwargs: diagnostics,
    )

    runtime_presets = model_settings._load_runtime_codex_presets({"codex": True})
    runtime_keys = {preset.key for preset in runtime_presets}

    assert model_presets.make_codex_runtime_preset_key("gpt-5.3-codex", reasoning_effort="medium") in runtime_keys
    assert (
        model_presets.make_codex_runtime_preset_key("gpt-6-codex-preview", reasoning_effort="medium")
        in runtime_keys
    )


def test_model_settings_loads_runtime_codex_reasoning_variants(monkeypatch) -> None:
    diagnostics = CodexRuntimeDiagnostics(
        executable_path="/usr/local/bin/codex",
        codex_home="/tmp/codex-home",
        command=("codex", "app-server"),
        user_agent="codex/1.0",
        models=(
            CodexModelInfo(
                id="gpt-6-codex-preview",
                model="gpt-6-codex-preview",
                display_name="GPT-6 Codex Preview",
                description="Runtime-only model.",
                hidden=False,
                default_reasoning_effort="medium",
                supported_reasoning_efforts=(
                    CodexModelReasoningOption(reasoning_effort="none", description="No reasoning"),
                    CodexModelReasoningOption(reasoning_effort="medium", description="Balanced"),
                    CodexModelReasoningOption(reasoning_effort="xhigh", description="Deepest reasoning"),
                ),
                input_modalities=("text",),
                supports_personality=True,
                is_default=True,
                upgrade=None,
                availability_message=None,
                raw={},
            ),
        ),
    )

    monkeypatch.setattr(
        model_settings.codex_runtime,
        "get_codex_runtime_diagnostics",
        lambda **_kwargs: diagnostics,
    )

    runtime_presets = model_settings._load_runtime_codex_presets({"codex": True})
    runtime_keys = {preset.key for preset in runtime_presets}

    assert model_presets.make_codex_runtime_preset_key("gpt-6-codex-preview", reasoning_effort="none") in runtime_keys
    assert (
        model_presets.make_codex_runtime_preset_key("gpt-6-codex-preview", reasoning_effort="medium")
        in runtime_keys
    )
    assert model_presets.make_codex_runtime_preset_key("gpt-6-codex-preview", reasoning_effort="xhigh") in runtime_keys


def test_model_settings_merge_replaces_static_codex_choices() -> None:
    static_codex_preset = model_presets.PresetInfo(
        key="codex-gpt-5.3-codex",
        label="Codex GPT-5.3 Codex",
        description="Static preset",
        provider=model_presets.ModelProvider.CODEX,
    )
    openai_preset = model_presets.PresetInfo(
        key="gpt5-mini",
        label="GPT-5 Mini",
        description="Static OpenAI preset",
        provider=model_presets.ModelProvider.OPENAI,
    )
    runtime_codex_preset = model_presets.PresetInfo(
        key=model_presets.make_codex_runtime_preset_key("gpt-5.3-codex"),
        label="Codex: gpt-5.3-codex",
        description="Runtime preset",
        provider=model_presets.ModelProvider.CODEX,
    )

    merged = model_settings._merge_presets_with_runtime_codex(
        [openai_preset, static_codex_preset],
        (runtime_codex_preset,),
    )
    merged_keys = [preset.key for preset in merged]

    assert "gpt5-mini" in merged_keys
    assert "codex-gpt-5.3-codex" not in merged_keys
    assert model_presets.make_codex_runtime_preset_key("gpt-5.3-codex") in merged_keys


def test_model_settings_normalizes_static_codex_selection_to_runtime_effort_variant() -> None:
    runtime_codex_presets = (
        model_presets.PresetInfo(
            key=model_presets.make_codex_runtime_preset_key("gpt-5.3-codex", reasoning_effort="low"),
            label="Codex: gpt-5.3-codex (low)",
            description="Runtime preset",
            provider=model_presets.ModelProvider.CODEX,
        ),
        model_presets.PresetInfo(
            key=model_presets.make_codex_runtime_preset_key("gpt-5.3-codex", reasoning_effort="medium"),
            label="Codex: gpt-5.3-codex (medium)",
            description="Runtime preset",
            provider=model_presets.ModelProvider.CODEX,
        ),
    )

    normalized = model_settings._normalize_codex_selection_key("codex-gpt-5.3-codex", runtime_codex_presets)

    assert normalized == model_presets.make_codex_runtime_preset_key("gpt-5.3-codex", reasoning_effort="medium")


def test_researcher_status_supports_runtime_codex_key_without_tavily() -> None:
    runtime_key = model_presets.make_codex_runtime_preset_key("gpt-6-codex-preview")

    model_label, provider_label = describe_researcher_phase_status(
        researcher_key=runtime_key,
        researcher_mode="on",
        tavily_available=False,
        offline_mode=False,
        provider_availability={"codex": True},
    )

    assert model_label.startswith("Codex: gpt-6-codex-preview")
    assert model_label.endswith("(On)")
    assert provider_label == "Codex App Server"
