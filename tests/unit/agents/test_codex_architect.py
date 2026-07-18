from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from agentrules.config.agents import MODEL_PRESETS
from agentrules.core.agents.base import ReasoningMode
from agentrules.core.agents.codex import CodexError, CodexJsonRpcError, CodexModelInfo, CodexModelReasoningOption
from agentrules.core.agents.codex.architect import CodexArchitect
from agentrules.core.agents.codex.model_selection import resolve_model_selection
from agentrules.core.agents.factory.factory import ArchitectFactory
from agentrules.core.configuration import model_presets
from agentrules.core.configuration.manager import ConfigManager
from agentrules.core.configuration.repository import TomlConfigRepository

FAKE_SERVER = Path(__file__).resolve().parents[2] / "fakes" / "codex_app_server.py"


def _build_config_manager(tmp_path: Path) -> ConfigManager:
    manager = ConfigManager(repository=TomlConfigRepository(tmp_path / "config.toml"), environ={})
    manager.set_codex_cli_path(sys.executable)
    manager.set_codex_managed_home(str(tmp_path / "codex-home"))
    return manager


def _build_architect(
    tmp_path: Path,
    *,
    model_name: str = "gpt-5.3-codex",
    reasoning: ReasoningMode = ReasoningMode.MEDIUM,
    runtime_reasoning_effort: str | None = None,
) -> CodexArchitect:
    model_config = MODEL_PRESETS["codex-gpt-5.3-codex"]["config"]._replace(
        model_name=model_name,
        reasoning=reasoning,
        runtime_reasoning_effort=runtime_reasoning_effort,
    )
    return CodexArchitect(
        model_name=model_name,
        reasoning=reasoning,
        name="Codex Tester",
        role="repository analysis",
        responsibilities=["Inspect the codebase"],
        prompt_template="{context}",
        system_prompt="Use concise bullets.",
        model_config=model_config,
        config_manager=_build_config_manager(tmp_path),
        command=(sys.executable, "-u", str(FAKE_SERVER)),
        request_timeout_seconds=2.0,
    )


def test_factory_creates_codex_architect() -> None:
    architect = ArchitectFactory.create_architect(
        model_config=MODEL_PRESETS["codex-gpt-5.3-codex"]["config"],
        name="Codex Factory Agent",
        role="analysis",
        responsibilities=["Review the repository"],
        prompt_template="{context}",
        system_prompt="Use concise bullets.",
    )

    assert isinstance(architect, CodexArchitect)


def test_factory_carries_runtime_reasoning_effort_into_codex_architect() -> None:
    config = model_presets.get_model_config_for_preset_key(
        model_presets.make_codex_runtime_preset_key(
            "gpt-5.6-sol",
            reasoning_effort="extreme",
        )
    )
    assert config is not None

    architect = ArchitectFactory.create_architect(
        model_config=config,
        name="Codex Future Effort Agent",
        role="analysis",
        responsibilities=["Review the repository"],
        prompt_template="{context}",
        system_prompt="Use concise bullets.",
    )

    assert isinstance(architect, CodexArchitect)
    assert architect._runtime_reasoning_effort == "extreme"


def test_codex_prepare_request_sets_launch_overrides_and_output_schema(tmp_path: Path) -> None:
    architect = _build_architect(tmp_path)

    prepared = architect._prepare_request(
        "Inspect the architecture",
        system_prompt="Use concise bullets.",
        phase_name="phase4",
        cwd=str(tmp_path),
    )

    assert prepared.launch_config.config_overrides["developer_instructions"] == "Use concise bullets."
    assert prepared.thread_params["approvalPolicy"] == "never"
    assert prepared.thread_params["sandbox"] == "read-only"
    assert prepared.thread_params["ephemeral"] is True
    assert prepared.turn_params["sandboxPolicy"]["type"] == "readOnly"
    assert prepared.turn_params["summary"] == "concise"
    assert prepared.turn_params["outputSchema"]["properties"]["analysis"]["type"] == "string"


def test_resolve_model_selection_runtime_default_leaves_effort_unset_without_catalog_default() -> None:
    selection = resolve_model_selection(
        available_models=(
            CodexModelInfo(
                id="gpt-6-codex-preview",
                model="gpt-6-codex-preview",
                display_name="GPT-6 Codex Preview",
                description="Runtime-only model.",
                hidden=False,
                default_reasoning_effort=None,
                supported_reasoning_efforts=(
                    CodexModelReasoningOption(reasoning_effort="low", description="Lower latency"),
                    CodexModelReasoningOption(reasoning_effort="high", description="Deep reasoning"),
                ),
                input_modalities=("text",),
                supports_personality=True,
                is_default=True,
                upgrade=None,
                availability_message=None,
                raw={},
            ),
        ),
        requested_model_name=model_presets.CODEX_RUNTIME_DEFAULT_MODEL_NAME,
        requested_reasoning=ReasoningMode.DYNAMIC,
    )

    assert selection.model_name == "gpt-6-codex-preview"
    assert selection.reasoning_effort is None


def test_resolve_model_selection_runtime_default_uses_catalog_default_effort_when_available() -> None:
    selection = resolve_model_selection(
        available_models=(
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
                is_default=True,
                upgrade=None,
                availability_message=None,
                raw={},
            ),
        ),
        requested_model_name=model_presets.CODEX_RUNTIME_DEFAULT_MODEL_NAME,
        requested_reasoning=ReasoningMode.DYNAMIC,
    )

    assert selection.model_name == "gpt-6-codex-preview"
    assert selection.reasoning_effort == "medium"


def test_resolve_model_selection_runtime_default_falls_back_without_default_hint() -> None:
    selection = resolve_model_selection(
        available_models=(
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
        requested_model_name=model_presets.CODEX_RUNTIME_DEFAULT_MODEL_NAME,
        requested_reasoning=ReasoningMode.DYNAMIC,
    )

    assert selection.model_name is None
    assert selection.reasoning_effort is None
    assert selection.display_name == "Codex runtime default"


def test_resolve_model_selection_matches_legacy_catalog_alias() -> None:
    selection = resolve_model_selection(
        available_models=(
            CodexModelInfo(
                id="gpt-5.4-2026-03-05",
                model="gpt-5.4-2026-03-05",
                display_name="GPT-5.4 Snapshot",
                description="Legacy runtime identifier.",
                hidden=False,
                default_reasoning_effort="high",
                supported_reasoning_efforts=(
                    CodexModelReasoningOption(reasoning_effort="medium", description="Balanced"),
                    CodexModelReasoningOption(reasoning_effort="high", description="Deep reasoning"),
                ),
                input_modalities=("text",),
                supports_personality=True,
                is_default=False,
                upgrade=None,
                availability_message=None,
                raw={},
            ),
        ),
        requested_model_name="gpt-5.4",
        requested_reasoning=ReasoningMode.HIGH,
    )

    assert selection.model_name == "gpt-5.4-2026-03-05"
    assert selection.reasoning_effort == "high"


def test_resolve_model_selection_preserves_exact_legacy_model_when_present() -> None:
    selection = resolve_model_selection(
        available_models=(
            CodexModelInfo(
                id="gpt-5.4-2026-03-05",
                model="gpt-5.4-2026-03-05",
                display_name="GPT-5.4 Snapshot",
                description="Legacy runtime identifier.",
                hidden=True,
                default_reasoning_effort="high",
                supported_reasoning_efforts=(),
                input_modalities=("text",),
                supports_personality=True,
                is_default=False,
                upgrade=None,
                availability_message=None,
                raw={},
            ),
            CodexModelInfo(
                id="gpt-5.4",
                model="gpt-5.4",
                display_name="GPT-5.4",
                description="Canonical runtime identifier.",
                hidden=False,
                default_reasoning_effort="high",
                supported_reasoning_efforts=(),
                input_modalities=("text",),
                supports_personality=True,
                is_default=False,
                upgrade=None,
                availability_message=None,
                raw={},
            ),
        ),
        requested_model_name="gpt-5.4-2026-03-05",
        requested_reasoning=ReasoningMode.HIGH,
    )

    assert selection.model_name == "gpt-5.4-2026-03-05"
    assert selection.reasoning_effort == "high"


def test_resolve_model_selection_preserves_pinned_legacy_model_when_only_canonical_alias_is_listed() -> None:
    selection = resolve_model_selection(
        available_models=(
            CodexModelInfo(
                id="gpt-5.4",
                model="gpt-5.4",
                display_name="GPT-5.4",
                description="Canonical runtime identifier.",
                hidden=False,
                default_reasoning_effort="high",
                supported_reasoning_efforts=(),
                input_modalities=("text",),
                supports_personality=True,
                is_default=False,
                upgrade=None,
                availability_message=None,
                raw={},
            ),
        ),
        requested_model_name="gpt-5.4-2026-03-05",
        requested_reasoning=ReasoningMode.HIGH,
    )

    assert selection.model_name == "gpt-5.4-2026-03-05"
    assert selection.reasoning_effort == "high"


def test_resolve_model_selection_uses_runtime_effort_for_pinned_dynamic_model() -> None:
    selection = resolve_model_selection(
        available_models=(
            CodexModelInfo(
                id="gpt-5.2-codex",
                model="gpt-5.2-codex",
                display_name="GPT-5.2 Codex",
                description="Hidden compatibility model.",
                hidden=True,
                default_reasoning_effort="medium",
                supported_reasoning_efforts=(
                    CodexModelReasoningOption(reasoning_effort="low", description="Lower latency"),
                ),
                input_modalities=("text",),
                supports_personality=True,
                is_default=False,
                upgrade=None,
                availability_message=None,
                raw={},
            ),
        ),
        requested_model_name="gpt-5.2-codex",
        requested_reasoning=ReasoningMode.DYNAMIC,
    )

    assert selection.model_name == "gpt-5.2-codex"
    assert selection.reasoning_effort == "medium"


def test_resolve_model_selection_accepts_default_explicit_effort_when_catalog_lists_only_alternates() -> None:
    selection = resolve_model_selection(
        available_models=(
            CodexModelInfo(
                id="gpt-5.2-codex",
                model="gpt-5.2-codex",
                display_name="GPT-5.2 Codex",
                description="Hidden compatibility model.",
                hidden=True,
                default_reasoning_effort="medium",
                supported_reasoning_efforts=(
                    CodexModelReasoningOption(reasoning_effort="low", description="Lower latency"),
                ),
                input_modalities=("text",),
                supports_personality=True,
                is_default=False,
                upgrade=None,
                availability_message=None,
                raw={},
            ),
        ),
        requested_model_name="gpt-5.2-codex",
        requested_reasoning=ReasoningMode.MEDIUM,
    )

    assert selection.model_name == "gpt-5.2-codex"
    assert selection.reasoning_effort == "medium"


def test_resolve_model_selection_rejects_unsupported_non_default_explicit_effort() -> None:
    with pytest.raises(ValueError, match="does not support reasoning effort 'high'"):
        resolve_model_selection(
            available_models=(
                CodexModelInfo(
                    id="gpt-5.2-codex",
                    model="gpt-5.2-codex",
                    display_name="GPT-5.2 Codex",
                    description="Hidden compatibility model.",
                    hidden=True,
                    default_reasoning_effort="medium",
                    supported_reasoning_efforts=(
                        CodexModelReasoningOption(reasoning_effort="low", description="Lower latency"),
                    ),
                    input_modalities=("text",),
                    supports_personality=True,
                    is_default=False,
                    upgrade=None,
                    availability_message=None,
                    raw={},
                ),
            ),
            requested_model_name="gpt-5.2-codex",
            requested_reasoning=ReasoningMode.HIGH,
        )


def test_resolve_model_selection_preserves_safe_runtime_effort() -> None:
    selection = resolve_model_selection(
        available_models=(
            CodexModelInfo(
                id="gpt-6-codex-preview",
                model="gpt-6-codex-preview",
                display_name="GPT-6 Codex Preview",
                description="Runtime-only model.",
                hidden=False,
                default_reasoning_effort="medium",
                supported_reasoning_efforts=(
                    CodexModelReasoningOption(reasoning_effort="extreme", description="Future effort"),
                ),
                input_modalities=("text",),
                supports_personality=True,
                is_default=False,
                upgrade=None,
                availability_message=None,
                raw={},
            ),
        ),
        requested_model_name="gpt-6-codex-preview",
        requested_reasoning=ReasoningMode.DYNAMIC,
        requested_runtime_reasoning_effort="extreme",
    )

    assert selection.reasoning_effort == "extreme"


@pytest.mark.asyncio
async def test_codex_analyze_returns_plain_text_findings(tmp_path: Path) -> None:
    architect = _build_architect(tmp_path)

    result = await architect.analyze(
        {
            "formatted_prompt": "Inspect the main module.",
            "_codex_cwd": str(tmp_path),
        }
    )

    assert result["agent"] == "Codex Tester"
    assert result["error"] if "error" in result else None is None
    assert "Codex analyzed: Inspect the main module." in result["findings"]


@pytest.mark.asyncio
async def test_codex_analyze_sends_future_runtime_effort_unchanged(tmp_path: Path) -> None:
    architect = _build_architect(
        tmp_path,
        reasoning=ReasoningMode.DYNAMIC,
        runtime_reasoning_effort="extreme",
    )

    result = await architect.analyze(
        {
            "formatted_prompt": "REPORT_EFFORT",
            "_codex_cwd": str(tmp_path),
        }
    )

    assert result["findings"] == "Codex effort: extreme"


@pytest.mark.asyncio
async def test_codex_analyze_resolves_runtime_default_model(tmp_path: Path) -> None:
    architect = _build_architect(
        tmp_path,
        model_name=model_presets.CODEX_RUNTIME_DEFAULT_MODEL_NAME,
        reasoning=ReasoningMode.DYNAMIC,
    )

    result = await architect.analyze(
        {
            "formatted_prompt": "Inspect the default Codex runtime model.",
            "_codex_cwd": str(tmp_path),
        }
    )

    assert result["agent"] == "Codex Tester"
    assert result["error"] if "error" in result else None is None
    assert "Codex analyzed: Inspect the default Codex runtime model." in result["findings"]


@pytest.mark.asyncio
async def test_codex_analyze_falls_back_when_catalog_lookup_fails(tmp_path: Path) -> None:
    architect = _build_architect(
        tmp_path,
        model_name="gpt-5.4-2026-03-05",
        reasoning=ReasoningMode.HIGH,
    )

    with patch(
        "agentrules.core.agents.codex.architect.CodexAppServerClient.list_all_models",
        new_callable=AsyncMock,
    ) as mock_list_models:
        mock_list_models.side_effect = CodexError("catalog unavailable")
        result = await architect.analyze(
            {
                "formatted_prompt": "Inspect the fallback model flow.",
                "_codex_cwd": str(tmp_path),
            }
        )

    assert result["error"] if "error" in result else None is None
    assert "Codex analyzed: Inspect the fallback model flow." in result["findings"]


@pytest.mark.asyncio
async def test_codex_model_catalog_failure_preserves_configured_legacy_model_id(tmp_path: Path) -> None:
    architect = _build_architect(
        tmp_path,
        model_name="gpt-5.4-2026-03-05",
        reasoning=ReasoningMode.HIGH,
    )
    prepared = architect._prepare_request(
        "Inspect the legacy fallback model flow.",
        system_prompt="Use concise bullets.",
        phase_name=None,
        cwd=str(tmp_path),
    )
    client = AsyncMock()
    client.list_all_models.side_effect = CodexError("catalog unavailable")

    await architect._resolve_runtime_model_selection(client, prepared)

    assert prepared.thread_params["model"] == "gpt-5.4-2026-03-05"
    assert prepared.turn_params["model"] == "gpt-5.4-2026-03-05"
    assert prepared.turn_params["effort"] == "high"
    assert prepared.turn_params["summary"] == "concise"


@pytest.mark.asyncio
async def test_codex_runtime_selection_preserves_default_explicit_effort_and_summary(tmp_path: Path) -> None:
    architect = _build_architect(
        tmp_path,
        model_name="gpt-5.2-codex",
        reasoning=ReasoningMode.MEDIUM,
    )
    prepared = architect._prepare_request(
        "Inspect the hidden Codex compatibility preset.",
        system_prompt="Use concise bullets.",
        phase_name=None,
        cwd=str(tmp_path),
    )
    client = AsyncMock()
    client.list_all_models.return_value = (
        CodexModelInfo(
            id="gpt-5.2-codex",
            model="gpt-5.2-codex",
            display_name="GPT-5.2 Codex",
            description="Hidden compatibility model.",
            hidden=True,
            default_reasoning_effort="medium",
            supported_reasoning_efforts=(
                CodexModelReasoningOption(reasoning_effort="low", description="Lower latency"),
            ),
            input_modalities=("text",),
            supports_personality=True,
            is_default=False,
            upgrade=None,
            availability_message=None,
            raw={},
        ),
    )

    await architect._resolve_runtime_model_selection(client, prepared)

    assert prepared.thread_params["model"] == "gpt-5.2-codex"
    assert prepared.turn_params["model"] == "gpt-5.2-codex"
    assert prepared.turn_params["effort"] == "medium"
    assert prepared.turn_params["summary"] == "concise"


@pytest.mark.asyncio
async def test_codex_runtime_selection_preserves_pinned_legacy_model_when_catalog_only_lists_canonical_alias(
    tmp_path: Path,
) -> None:
    architect = _build_architect(
        tmp_path,
        model_name="gpt-5.4-2026-03-05",
        reasoning=ReasoningMode.HIGH,
    )
    prepared = architect._prepare_request(
        "Inspect the pinned legacy Codex preset.",
        system_prompt="Use concise bullets.",
        phase_name=None,
        cwd=str(tmp_path),
    )
    client = AsyncMock()
    client.list_all_models.return_value = (
        CodexModelInfo(
            id="gpt-5.4",
            model="gpt-5.4",
            display_name="GPT-5.4",
            description="Canonical runtime identifier.",
            hidden=False,
            default_reasoning_effort="high",
            supported_reasoning_efforts=(),
            input_modalities=("text",),
            supports_personality=True,
            is_default=False,
            upgrade=None,
            availability_message=None,
            raw={},
        ),
    )

    await architect._resolve_runtime_model_selection(client, prepared)

    assert prepared.thread_params["model"] == "gpt-5.4-2026-03-05"
    assert prepared.turn_params["model"] == "gpt-5.4-2026-03-05"
    assert prepared.turn_params["effort"] == "high"
    assert prepared.turn_params["summary"] == "concise"


@pytest.mark.asyncio
async def test_codex_thread_start_retries_known_alias_after_catalog_failure(tmp_path: Path) -> None:
    architect = _build_architect(
        tmp_path,
        model_name="gpt-5.4-2026-03-05",
        reasoning=ReasoningMode.HIGH,
    )
    prepared = architect._prepare_request(
        "Inspect the legacy retry model flow.",
        system_prompt="Use concise bullets.",
        phase_name=None,
        cwd=str(tmp_path),
    )
    client = AsyncMock()
    client.start_thread.side_effect = [
        CodexJsonRpcError(-32000, "Unknown model: gpt-5.4-2026-03-05"),
        SimpleNamespace(thread=SimpleNamespace(id="thr-1")),
    ]

    thread = await architect._start_thread(client, prepared)

    assert thread.thread.id == "thr-1"
    assert prepared.thread_params["model"] == "gpt-5.4"
    assert prepared.turn_params["model"] == "gpt-5.4"
    assert client.start_thread.await_count == 2


@pytest.mark.asyncio
async def test_codex_analyze_falls_back_when_catalog_lookup_times_out(tmp_path: Path) -> None:
    architect = _build_architect(
        tmp_path,
        model_name="gpt-5.4-2026-03-05",
        reasoning=ReasoningMode.HIGH,
    )

    with patch(
        "agentrules.core.agents.codex.architect.CodexAppServerClient.list_all_models",
        new_callable=AsyncMock,
    ) as mock_list_models:
        mock_list_models.side_effect = TimeoutError("timed out")
        result = await architect.analyze(
            {
                "formatted_prompt": "Inspect the timeout fallback model flow.",
                "_codex_cwd": str(tmp_path),
            }
        )

    assert result["error"] if "error" in result else None is None
    assert "Codex analyzed: Inspect the timeout fallback model flow." in result["findings"]


@pytest.mark.asyncio
async def test_codex_runtime_default_falls_back_to_runtime_default_on_catalog_failure(tmp_path: Path) -> None:
    architect = _build_architect(
        tmp_path,
        model_name=model_presets.CODEX_RUNTIME_DEFAULT_MODEL_NAME,
        reasoning=ReasoningMode.DYNAMIC,
    )

    with patch(
        "agentrules.core.agents.codex.architect.CodexAppServerClient.list_all_models",
        new_callable=AsyncMock,
    ) as mock_list_models:
        mock_list_models.side_effect = CodexError("catalog unavailable")
        result = await architect.analyze(
            {
                "formatted_prompt": "Inspect runtime default fallback behavior.",
                "_codex_cwd": str(tmp_path),
            }
        )

    assert result["error"] if "error" in result else None is None
    assert "Codex analyzed: Inspect runtime default fallback behavior." in result["findings"]


@pytest.mark.asyncio
async def test_codex_runtime_default_catalog_failure_clears_model_override(tmp_path: Path) -> None:
    architect = _build_architect(
        tmp_path,
        model_name=model_presets.CODEX_RUNTIME_DEFAULT_MODEL_NAME,
        reasoning=ReasoningMode.DYNAMIC,
    )
    prepared = architect._prepare_request(
        "Inspect runtime default fallback behavior.",
        system_prompt="Use concise bullets.",
        phase_name=None,
        cwd=str(tmp_path),
    )
    client = AsyncMock()
    client.list_all_models.side_effect = CodexError("catalog unavailable")

    await architect._resolve_runtime_model_selection(client, prepared)

    assert "model" not in prepared.thread_params
    assert "model" not in prepared.turn_params
    assert "effort" not in prepared.turn_params
    assert prepared.turn_params["summary"] == "none"


@pytest.mark.asyncio
async def test_codex_runtime_default_without_default_hint_clears_model_override(tmp_path: Path) -> None:
    architect = _build_architect(
        tmp_path,
        model_name=model_presets.CODEX_RUNTIME_DEFAULT_MODEL_NAME,
        reasoning=ReasoningMode.DYNAMIC,
    )
    prepared = architect._prepare_request(
        "Inspect runtime default behavior without an explicit default hint.",
        system_prompt="Use concise bullets.",
        phase_name=None,
        cwd=str(tmp_path),
    )
    client = AsyncMock()
    client.list_all_models.return_value = (
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
    )

    await architect._resolve_runtime_model_selection(client, prepared)

    assert "model" not in prepared.thread_params
    assert "model" not in prepared.turn_params
    assert "effort" not in prepared.turn_params
    assert prepared.turn_params["summary"] == "none"


@pytest.mark.asyncio
async def test_codex_analyze_accepts_legacy_gpt54_alias(tmp_path: Path) -> None:
    architect = _build_architect(
        tmp_path,
        model_name="gpt-5.4-2026-03-05",
        reasoning=ReasoningMode.HIGH,
    )

    result = await architect.analyze(
        {
            "formatted_prompt": "Inspect the legacy Codex GPT-5.4 preset.",
            "_codex_cwd": str(tmp_path),
        }
    )

    assert result["error"] if "error" in result else None is None
    assert "Codex analyzed: Inspect the legacy Codex GPT-5.4 preset." in result["findings"]


@pytest.mark.asyncio
async def test_codex_analyze_rejects_hidden_legacy_model_with_unsupported_explicit_effort(tmp_path: Path) -> None:
    architect = _build_architect(
        tmp_path,
        model_name="gpt-5.2-codex",
        reasoning=ReasoningMode.HIGH,
    )

    result = await architect.analyze(
        {
            "formatted_prompt": "Inspect the hidden Codex compatibility preset.",
            "_codex_cwd": str(tmp_path),
        }
    )

    assert "does not support reasoning effort 'high'" in result["error"]


@pytest.mark.asyncio
async def test_codex_analyze_accepts_hidden_legacy_model_with_default_explicit_effort(tmp_path: Path) -> None:
    architect = _build_architect(
        tmp_path,
        model_name="gpt-5.2-codex",
        reasoning=ReasoningMode.MEDIUM,
    )

    result = await architect.analyze(
        {
            "formatted_prompt": "Inspect the hidden Codex compatibility preset.",
            "_codex_cwd": str(tmp_path),
        }
    )

    assert result["error"] if "error" in result else None is None
    assert "Codex analyzed: Inspect the hidden Codex compatibility preset." in result["findings"]


@pytest.mark.asyncio
async def test_codex_analyze_reports_unavailable_pinned_model(tmp_path: Path) -> None:
    architect = _build_architect(
        tmp_path,
        model_name="gpt-6-codex-preview",
        reasoning=ReasoningMode.MEDIUM,
    )

    result = await architect.analyze(
        {
            "formatted_prompt": "Inspect an unavailable model.",
            "_codex_cwd": str(tmp_path),
        }
    )

    assert "not available from the current Codex account" in result["error"]


@pytest.mark.asyncio
async def test_codex_phase_request_parses_structured_output(tmp_path: Path) -> None:
    architect = _build_architect(tmp_path)

    result = await architect.create_analysis_plan({}, prompt="Plan the repository analysis.")

    assert result["error"] is None
    assert result["plan"] == "Analyze the repository in focused batches."
    assert result["structured_output"]["reasoning"] == "The fake runtime returned a deterministic phase 2 plan."
    assert result["agents"][0]["id"] == "agent_1"


@pytest.mark.asyncio
async def test_codex_phase_request_reports_invalid_structured_output(tmp_path: Path) -> None:
    architect = _build_architect(tmp_path)

    result = await architect.synthesize_findings({}, prompt="BAD_SCHEMA_JSON")

    assert result["analysis"] == "No synthesis generated"
    assert "invalid structured output" in (result["error"] or "")


@pytest.mark.asyncio
async def test_codex_analyze_maps_failed_turn_to_error(tmp_path: Path) -> None:
    architect = _build_architect(tmp_path)

    result = await architect.analyze(
        {
            "formatted_prompt": "TURN_FAIL",
            "_codex_cwd": str(tmp_path),
        }
    )

    assert "Fake Codex turn failure" in result["error"]
    assert "Simulated failure" in result["error"]
