from __future__ import annotations

from agentrules.cli.services.codex_runtime import CodexRuntimeDiagnostics
from agentrules.cli.services.configuration import CodexRuntimeState
from agentrules.cli.ui.settings.codex import build_runtime_guidance
from agentrules.cli.ui.settings.menu import SETTINGS_CATEGORY_ENTRIES, build_settings_category_choices
from agentrules.cli.ui.settings.models import describe_researcher_phase_status
from agentrules.core.agents.codex import CodexAccountSummary, CodexModelInfo


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
    assert any("choose a `codex-*` preset" in note for note in guidance)
