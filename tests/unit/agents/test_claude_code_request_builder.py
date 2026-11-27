from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from claude_agent_sdk import ClaudeAgentOptions

from agentrules.config.agents import MODEL_PRESETS
from agentrules.core.agents.base import ReasoningMode
from agentrules.core.agents.claude_code.request_builder import prepare_request
from agentrules.core.configuration.manager import ConfigManager
from agentrules.core.configuration.models import ClaudeCodeConfig
from agentrules.core.configuration.repository import TomlConfigRepository
from agentrules.core.configuration.services import claude_code as claude_code_service
from agentrules.core.configuration.services.claude_code import ClaudeCodeVersion
from agentrules.core.types.models import (
    CLAUDE_CODE_RUNTIME_DEFAULT_MODEL,
    CLAUDE_OPUS,
    create_claude_code_config,
)


def _build_config_manager(tmp_path: Path) -> ConfigManager:
    env = {
        "ANTHROPIC_API_KEY": "api-key",
        "ANTHROPIC_AUTH_TOKEN": "auth-token",
        "CLAUDE_CODE_OAUTH_TOKEN": "oauth-token",
        "PATH": "/usr/bin",
    }
    manager = ConfigManager(repository=TomlConfigRepository(tmp_path / "config.toml"), environ=env)
    manager.set_claude_code_cli_path(sys.executable)
    return manager


def _build_sdk_default_config_manager(tmp_path: Path) -> ConfigManager:
    env = {
        "ANTHROPIC_API_KEY": "api-key",
        "ANTHROPIC_AUTH_TOKEN": "auth-token",
        "CLAUDE_CODE_OAUTH_TOKEN": "oauth-token",
        "PATH": "/usr/bin",
    }
    return ConfigManager(repository=TomlConfigRepository(tmp_path / "config.toml"), environ=env)


def _stub_runtime_version(
    monkeypatch: pytest.MonkeyPatch,
    version: ClaudeCodeVersion | None,
) -> None:
    monkeypatch.setattr(claude_code_service, "_probe_claude_code_executable_version", lambda *_args, **_kwargs: version)


def test_prepare_request_sets_oauth_runtime_options_and_sanitized_env(tmp_path: Path) -> None:
    prepared = prepare_request(
        config_manager=_build_config_manager(tmp_path),
        model_name="claude-sonnet-4-6",
        content="Inspect repository architecture.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.DISABLED,
        phase_name=None,
        cwd=str(tmp_path),
    )

    assert prepared.options["model"] == "claude-sonnet-4-6"
    assert prepared.options["cli_path"] == str(Path(sys.executable).resolve())
    assert prepared.options["cwd"] == str(tmp_path.resolve())
    assert prepared.options["permission_mode"] == "dontAsk"
    assert prepared.options["allowed_tools"] == ["Read", "Glob", "Grep"]
    assert "Bash" in prepared.options["disallowed_tools"]
    assert prepared.options["max_turns"] == 12
    assert "max_budget_usd" not in prepared.options
    assert "request_timeout_seconds" not in prepared.options
    assert prepared.execution_timeout_seconds == 300.0
    assert prepared.options["system_prompt"] == {
        "type": "preset",
        "preset": "claude_code",
        "append": "Keep responses concise.",
        "exclude_dynamic_sections": True,
    }
    assert prepared.options["env"]["CLAUDE_CODE_OAUTH_TOKEN"] == "oauth-token"
    assert "ANTHROPIC_API_KEY" not in prepared.options["env"]
    assert "ANTHROPIC_AUTH_TOKEN" not in prepared.options["env"]
    assert prepared.sanitized_env_vars == ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")


def test_prepare_request_omits_cli_path_for_sdk_default_runtime(tmp_path: Path) -> None:
    prepared = prepare_request(
        config_manager=_build_sdk_default_config_manager(tmp_path),
        model_name="claude-sonnet-4-6",
        content="Inspect repository architecture.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.DISABLED,
        phase_name=None,
        cwd=str(tmp_path),
    )

    sdk_options = ClaudeAgentOptions(**prepared.options)

    assert "cli_path" not in prepared.options
    assert sdk_options.cli_path is None


def test_prepare_request_resolves_configured_cli_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    executable = bin_dir / "claude"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))
    manager = _build_sdk_default_config_manager(tmp_path)
    manager.set_claude_code_cli_path("claude")

    prepared = prepare_request(
        config_manager=manager,
        model_name="claude-sonnet-4-6",
        content="Inspect repository architecture.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.DISABLED,
        phase_name=None,
        cwd=str(tmp_path),
    )

    assert prepared.options["cli_path"] == str(executable.resolve())


def test_prepare_request_fails_fast_when_configured_cli_path_is_missing(tmp_path: Path) -> None:
    manager = _build_sdk_default_config_manager(tmp_path)
    manager.set_claude_code_cli_path(str(tmp_path / "missing-claude"))

    with pytest.raises(ValueError, match="Configured Claude Code executable could not be resolved"):
        prepare_request(
            config_manager=manager,
            model_name="claude-sonnet-4-6",
            content="Inspect repository architecture.",
            system_prompt="Keep responses concise.",
            reasoning=ReasoningMode.DISABLED,
            phase_name=None,
            cwd=str(tmp_path),
        )


def test_prepare_request_enables_research_tools_when_tools_config_enabled(tmp_path: Path) -> None:
    prepared = prepare_request(
        config_manager=_build_config_manager(tmp_path),
        model_name="claude-sonnet-4-6",
        content="Research package docs.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.DISABLED,
        phase_name=None,
        cwd=str(tmp_path),
        tools_config={"enabled": True, "tools": None},
    )

    assert prepared.options["allowed_tools"] == ["Read", "Glob", "Grep", "WebSearch", "WebFetch"]


def test_prepare_request_maps_reasoning_and_structured_output(tmp_path: Path) -> None:
    prepared = prepare_request(
        config_manager=_build_config_manager(tmp_path),
        model_name="claude-sonnet-4-6",
        content="Plan the analysis.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.DYNAMIC,
        phase_name="phase2",
        cwd=str(tmp_path),
        effort="medium",
    )

    assert prepared.options["thinking"] == {"type": "adaptive"}
    assert prepared.options["effort"] == "medium"
    assert prepared.options["output_format"]["type"] == "json_schema"
    assert prepared.options["output_format"]["schema"]["properties"]["plan"]["type"] == "string"


def test_prepare_request_rejects_unsupported_xhigh_reasoning(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Effort 'xhigh' is not supported"):
        prepare_request(
            config_manager=_build_config_manager(tmp_path),
            model_name="claude-opus-4-6",
            content="Deeply inspect repository architecture.",
            system_prompt="Keep responses concise.",
            reasoning=ReasoningMode.XHIGH,
            phase_name=None,
            cwd=str(tmp_path),
        )


def test_prepare_request_maps_xhigh_reasoning_to_xhigh_for_opus47(tmp_path: Path) -> None:
    prepared = prepare_request(
        config_manager=_build_config_manager(tmp_path),
        model_name="claude-opus-4-7",
        content="Deeply inspect repository architecture.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.XHIGH,
        phase_name=None,
        cwd=str(tmp_path),
    )

    assert prepared.options["effort"] == "xhigh"


def test_prepare_request_enabled_reasoning_uses_adaptive_for_opus48(tmp_path: Path) -> None:
    prepared = prepare_request(
        config_manager=_build_config_manager(tmp_path),
        model_name="claude-opus-4-8",
        content="Deeply inspect repository architecture.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.ENABLED,
        phase_name=None,
        cwd=str(tmp_path),
    )

    assert prepared.options["thinking"] == {"type": "adaptive"}


def test_prepare_request_rejects_models_unsupported_by_resolved_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = _build_config_manager(tmp_path)
    _stub_runtime_version(monkeypatch, ClaudeCodeVersion(2, 1, 150))

    with pytest.raises(ValueError, match="requires Claude Code 2.1.154 or later"):
        prepare_request(
            config_manager=manager,
            model_name="claude-opus-4-8",
            content="Inspect repository architecture.",
            system_prompt="Keep responses concise.",
            reasoning=ReasoningMode.DISABLED,
            phase_name=None,
            cwd=str(tmp_path),
        )


def test_prepare_request_allows_opus5_on_supported_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = _build_config_manager(tmp_path)
    _stub_runtime_version(monkeypatch, ClaudeCodeVersion(2, 1, 219))
    config = create_claude_code_config(CLAUDE_OPUS)

    prepared = prepare_request(
        config_manager=manager,
        model_name=config.model_name,
        content="Inspect repository architecture.",
        system_prompt="Keep responses concise.",
        reasoning=config.reasoning,
        effort=config.anthropic_effort,
        phase_name=None,
        cwd=str(tmp_path),
    )

    ClaudeAgentOptions(**prepared.options)
    assert prepared.options["model"] == "claude-opus-5"


def test_prepare_request_rejects_opus5_on_older_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = _build_config_manager(tmp_path)
    _stub_runtime_version(monkeypatch, ClaudeCodeVersion(2, 1, 218))

    with pytest.raises(ValueError, match="requires Claude Code 2.1.219 or later"):
        prepare_request(
            config_manager=manager,
            model_name="claude-opus-5",
            content="Inspect repository architecture.",
            system_prompt="Keep responses concise.",
            reasoning=ReasoningMode.DYNAMIC,
            phase_name=None,
            cwd=str(tmp_path),
        )


def test_prepare_request_fails_closed_when_opus5_runtime_version_is_unknown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = _build_config_manager(tmp_path)
    _stub_runtime_version(monkeypatch, None)

    with pytest.raises(ValueError, match="runtime version could not be verified"):
        prepare_request(
            config_manager=manager,
            model_name="claude-opus-5",
            content="Inspect repository architecture.",
            system_prompt="Keep responses concise.",
            reasoning=ReasoningMode.DYNAMIC,
            phase_name=None,
            cwd=str(tmp_path),
        )


@pytest.mark.parametrize(
    ("preset_key", "minimum_version", "effort"),
    [
        ("claude-code-fable-5.2", ClaudeCodeVersion(2, 1, 321), "medium"),
        ("claude-code-fable-5.1", ClaudeCodeVersion(2, 1, 257), "high"),
        ("claude-code-opus-5.5", ClaudeCodeVersion(2, 1, 280), "medium"),
        ("claude-code-sonnet-5.5", ClaudeCodeVersion(2, 1, 284), "high"),
        ("claude-code-haiku-5.5", ClaudeCodeVersion(2, 1, 293), "medium"),
    ],
)
def test_pinned_claude_code_model_requires_its_exact_runtime_minimum(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    preset_key: str,
    minimum_version: ClaudeCodeVersion,
    effort: str,
) -> None:
    manager = _build_config_manager(tmp_path)
    config = MODEL_PRESETS[preset_key]["config"]
    too_old = ClaudeCodeVersion(minimum_version.major, minimum_version.minor, minimum_version.patch - 1)
    _stub_runtime_version(monkeypatch, too_old)

    with pytest.raises(ValueError, match=f"requires Claude Code {minimum_version} or later"):
        prepare_request(
            config_manager=manager,
            model_name=config.model_name,
            content="Plan the analysis.",
            system_prompt="Keep responses concise.",
            reasoning=config.reasoning,
            effort=config.anthropic_effort,
            phase_name="phase2",
            cwd=str(tmp_path),
        )

    _stub_runtime_version(monkeypatch, minimum_version)
    prepared = prepare_request(
        config_manager=manager,
        model_name=config.model_name,
        content="Plan the analysis.",
        system_prompt="Keep responses concise.",
        reasoning=config.reasoning,
        effort=config.anthropic_effort,
        phase_name="phase2",
        cwd=str(tmp_path),
    )

    ClaudeAgentOptions(**prepared.options)
    assert prepared.options["model"] == config.model_name
    assert prepared.options["effort"] == effort
    assert prepared.options["output_format"]["type"] == "json_schema"


@pytest.mark.parametrize("model_name", ["claude-fable-5-1", "claude-opus-5-5"])
def test_pinned_claude_code_model_fails_closed_for_unversionable_executable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    model_name: str,
) -> None:
    manager = _build_config_manager(tmp_path)
    _stub_runtime_version(monkeypatch, None)

    with pytest.raises(ValueError, match="resolved runtime version could not be verified"):
        prepare_request(
            config_manager=manager,
            model_name=model_name,
            content="Plan the analysis.",
            system_prompt="Keep responses concise.",
            reasoning=ReasoningMode.DYNAMIC,
            phase_name="phase2",
            cwd=str(tmp_path),
        )


def test_pinned_model_versions_the_executable_passed_to_sdk(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = tmp_path / "sdk-bundled-claude"
    configured = tmp_path / "configured-claude"
    global_cli = tmp_path / "global-claude"
    for executable in (bundle, configured, global_cli):
        executable.write_text("fake", encoding="utf-8")
        executable.chmod(0o755)

    versions: dict[str, ClaudeCodeVersion | None] = {
        str(bundle): ClaudeCodeVersion(2, 1, 279),
        str(configured): ClaudeCodeVersion(2, 1, 280),
        str(global_cli): ClaudeCodeVersion(2, 1, 309),
    }
    probed_paths: list[str] = []

    def fake_probe(path: str, *, env_vars_to_remove: tuple[str, ...] = ()) -> ClaudeCodeVersion | None:
        del env_vars_to_remove
        probed_paths.append(path)
        return versions[path]

    monkeypatch.setattr(claude_code_service, "_resolve_sdk_bundled_executable", lambda: str(bundle))
    monkeypatch.setattr(claude_code_service.shutil, "which", lambda _name: str(global_cli))
    monkeypatch.setattr(claude_code_service, "_probe_claude_code_executable_version", fake_probe)
    manager = _build_sdk_default_config_manager(tmp_path)

    with pytest.raises(ValueError, match="requires Claude Code 2.1.280 or later"):
        prepare_request(
            config_manager=manager,
            model_name="claude-opus-5-5",
            content="Plan the analysis.",
            system_prompt="Keep responses concise.",
            reasoning=ReasoningMode.DYNAMIC,
            phase_name=None,
            cwd=str(tmp_path),
        )
    assert probed_paths == [str(bundle)]

    versions[str(bundle)] = None
    with pytest.raises(ValueError, match="resolved runtime version could not be verified"):
        prepare_request(
            config_manager=manager,
            model_name="claude-opus-5-5",
            content="Plan the analysis.",
            system_prompt="Keep responses concise.",
            reasoning=ReasoningMode.DYNAMIC,
            phase_name=None,
            cwd=str(tmp_path),
        )
    assert probed_paths == [str(bundle), str(bundle)]

    manager.set_claude_code_cli_path(str(configured))
    prepared = prepare_request(
        config_manager=manager,
        model_name="claude-opus-5-5",
        content="Plan the analysis.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.DYNAMIC,
        phase_name=None,
        cwd=str(tmp_path),
    )
    assert prepared.options["cli_path"] == str(configured)
    assert probed_paths == [str(bundle), str(bundle), str(configured)]

    with pytest.raises(ValueError, match="requires Claude Code 2.1.293 or later"):
        prepare_request(
            config_manager=manager,
            model_name="claude-haiku-5-5",
            content="Plan the analysis.",
            system_prompt="Keep responses concise.",
            reasoning=ReasoningMode.DYNAMIC,
            phase_name=None,
            cwd=str(tmp_path),
        )
    assert str(global_cli) not in probed_paths


@pytest.mark.parametrize(
    ("first_version", "error"),
    [
        ("2.1.320", "requires Claude Code 2.1.321 or later"),
        ("unknown", "runtime version could not be verified"),
        ("2.1.321", None),
    ],
)
def test_fable_52_probes_and_launches_the_same_executable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    first_version: str,
    error: str | None,
) -> None:
    launched_path = str(tmp_path / "selected-claude")
    other_path = str(tmp_path / "different-claude")
    resolved_paths = iter((launched_path, other_path))
    versions = {launched_path: first_version, other_path: "2.1.332"}
    probes: list[tuple[str, ...]] = []

    def run_probe(args: list[str], *, env: dict[str, str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        probes.append(tuple(args))
        assert "ANTHROPIC_API_KEY" not in env
        return subprocess.CompletedProcess(args, 0, stdout=versions[args[0]], stderr="")

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-env-key")
    monkeypatch.setattr(claude_code_service, "_resolve_sdk_bundled_executable", lambda: next(resolved_paths))
    monkeypatch.setattr(claude_code_service.subprocess, "run", run_probe)
    manager = _build_sdk_default_config_manager(tmp_path)

    def build_options() -> ClaudeAgentOptions:
        prepared = prepare_request(
            config_manager=manager,
            model_name="claude-fable-5-2",
            content="Plan the analysis.",
            system_prompt="Keep responses concise.",
            reasoning=ReasoningMode.DYNAMIC,
            effort="medium",
            phase_name="phase2",
            cwd=str(tmp_path),
        )
        return ClaudeAgentOptions(**prepared.options)

    if error is not None:
        with pytest.raises(ValueError, match=error):
            build_options()
    else:
        sdk_options = build_options()
        assert sdk_options.cli_path == launched_path
        assert sdk_options.model == "claude-fable-5-2"
        assert sdk_options.effort == "medium"

    assert probes == [(launched_path, "--version")]


def test_prepare_request_omits_model_for_runtime_default(tmp_path: Path) -> None:
    prepared = prepare_request(
        config_manager=_build_config_manager(tmp_path),
        model_name=CLAUDE_CODE_RUNTIME_DEFAULT_MODEL,
        content="Inspect repository architecture.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.DISABLED,
        phase_name=None,
        cwd=str(tmp_path),
    )

    sdk_options = ClaudeAgentOptions(**prepared.options)
    assert "model" not in prepared.options
    assert sdk_options.model is None
    assert "thinking" not in prepared.options
    assert "effort" not in prepared.options


@pytest.mark.parametrize("alias", ["best", "sonnet", "opus", "fable", "haiku"])
def test_prepare_request_preserves_runtime_managed_aliases(tmp_path: Path, alias: str) -> None:
    prepared = prepare_request(
        config_manager=_build_config_manager(tmp_path),
        model_name=alias,
        content="Inspect repository architecture.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.DYNAMIC if alias == "fable" else ReasoningMode.DISABLED,
        phase_name=None,
        cwd=str(tmp_path),
    )

    sdk_options = ClaudeAgentOptions(**prepared.options)
    assert prepared.options["model"] == alias
    assert sdk_options.model == alias
    assert "thinking" not in prepared.options
    assert "effort" not in prepared.options


def test_prepare_request_sonnet5_disabled_is_explicit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manager = _build_config_manager(tmp_path)
    _stub_runtime_version(monkeypatch, ClaudeCodeVersion(2, 1, 210))

    prepared = prepare_request(
        config_manager=manager,
        model_name="claude-sonnet-5",
        content="Inspect repository architecture.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.DISABLED,
        phase_name=None,
        cwd=str(tmp_path),
    )

    ClaudeAgentOptions(**prepared.options)
    assert prepared.options["thinking"] == {"type": "disabled"}


def test_prepare_request_sonnet5_adaptive_max_effort(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = _build_config_manager(tmp_path)
    _stub_runtime_version(monkeypatch, ClaudeCodeVersion(2, 1, 210))

    prepared = prepare_request(
        config_manager=manager,
        model_name="claude-sonnet-5",
        content="Inspect repository architecture.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.DYNAMIC,
        effort="max",
        phase_name=None,
        cwd=str(tmp_path),
    )

    ClaudeAgentOptions(**prepared.options)
    assert prepared.options["thinking"] == {"type": "adaptive"}
    assert prepared.options["effort"] == "max"


@pytest.mark.parametrize("effort", ["low", "medium", "high"])
def test_prepare_request_opus5_accepts_supported_effort_with_thinking_disabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    effort: str,
) -> None:
    manager = _build_config_manager(tmp_path)
    _stub_runtime_version(monkeypatch, ClaudeCodeVersion(2, 1, 219))

    prepared = prepare_request(
        config_manager=manager,
        model_name="claude-opus-5",
        content="Inspect repository architecture.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.DISABLED,
        effort=effort,
        phase_name=None,
        cwd=str(tmp_path),
    )

    ClaudeAgentOptions(**prepared.options)
    assert prepared.options["thinking"] == {"type": "disabled"}
    assert prepared.options["effort"] == effort


@pytest.mark.parametrize("effort", ["xhigh", "max"])
def test_prepare_request_opus5_rejects_extended_effort_with_thinking_disabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    effort: str,
) -> None:
    manager = _build_config_manager(tmp_path)
    _stub_runtime_version(monkeypatch, ClaudeCodeVersion(2, 1, 219))

    with pytest.raises(ValueError, match="when thinking is disabled"):
        prepare_request(
            config_manager=manager,
            model_name="claude-opus-5",
            content="Inspect repository architecture.",
            system_prompt="Keep responses concise.",
            reasoning=ReasoningMode.DISABLED,
            effort=effort,
            phase_name=None,
            cwd=str(tmp_path),
        )


def test_prepare_request_fable5_omits_thinking_and_preserves_effort(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = _build_config_manager(tmp_path)
    _stub_runtime_version(monkeypatch, ClaudeCodeVersion(2, 1, 210))

    prepared = prepare_request(
        config_manager=manager,
        model_name="claude-fable-5",
        content="Inspect repository architecture.",
        system_prompt="Keep responses concise.",
        reasoning=ReasoningMode.DYNAMIC,
        effort="max",
        phase_name=None,
        cwd=str(tmp_path),
    )

    ClaudeAgentOptions(**prepared.options)
    assert "thinking" not in prepared.options
    assert prepared.options["effort"] == "max"


def test_prepare_request_rejects_fable5_disabled_before_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = _build_config_manager(tmp_path)
    _stub_runtime_version(monkeypatch, ClaudeCodeVersion(2, 1, 210))

    with pytest.raises(ValueError, match="always uses adaptive thinking"):
        prepare_request(
            config_manager=manager,
            model_name="claude-fable-5",
            content="Inspect repository architecture.",
            system_prompt="Keep responses concise.",
            reasoning=ReasoningMode.DISABLED,
            phase_name=None,
            cwd=str(tmp_path),
        )


def test_prepare_request_fails_closed_when_pinned_model_version_is_unknown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = _build_config_manager(tmp_path)
    _stub_runtime_version(monkeypatch, None)

    with pytest.raises(ValueError, match="runtime version could not be verified"):
        prepare_request(
            config_manager=manager,
            model_name="claude-sonnet-5",
            content="Inspect repository architecture.",
            system_prompt="Keep responses concise.",
            reasoning=ReasoningMode.DYNAMIC,
            phase_name=None,
            cwd=str(tmp_path),
        )


def test_prepare_request_builds_sdk_accepted_system_prompt_preset(tmp_path: Path) -> None:
    prepared = prepare_request(
        config_manager=_build_config_manager(tmp_path),
        model_name="claude-sonnet-4-6",
        content="Inspect repository architecture.",
        system_prompt="Use AgentRules phase guidance.",
        reasoning=ReasoningMode.DISABLED,
        phase_name=None,
        cwd=str(tmp_path),
    )

    sdk_options = ClaudeAgentOptions(**prepared.options)

    assert sdk_options.system_prompt == {
        "type": "preset",
        "preset": "claude_code",
        "append": "Use AgentRules phase guidance.",
        "exclude_dynamic_sections": True,
    }


def test_prepare_request_uses_configured_execution_guardrails(tmp_path: Path) -> None:
    manager = _build_config_manager(tmp_path)
    config = manager.load()
    config.claude_code = ClaudeCodeConfig(
        cli_path=sys.executable,
        max_turns=3,
        request_timeout_seconds=1.5,
        max_budget_usd=0.25,
    )
    manager.save(config)

    prepared = prepare_request(
        config_manager=manager,
        model_name="claude-sonnet-4-6",
        content="Inspect repository architecture.",
        system_prompt="Use AgentRules phase guidance.",
        reasoning=ReasoningMode.DISABLED,
        phase_name=None,
        cwd=str(tmp_path),
    )

    sdk_options = ClaudeAgentOptions(**prepared.options)

    assert sdk_options.max_turns == 3
    assert sdk_options.max_budget_usd == 0.25
    assert prepared.execution_timeout_seconds == 1.5
    assert "request_timeout_seconds" not in prepared.options


def test_prepare_request_keeps_api_key_env_when_sanitization_is_disabled(tmp_path: Path) -> None:
    manager = _build_config_manager(tmp_path)
    manager.set_claude_code_sanitize_api_key_env(False)

    prepared = prepare_request(
        config_manager=manager,
        model_name="claude-sonnet-4-6",
        content="Inspect repository architecture.",
        system_prompt="Use AgentRules phase guidance.",
        reasoning=ReasoningMode.DISABLED,
        phase_name=None,
        cwd=str(tmp_path),
    )

    assert prepared.options["env"]["ANTHROPIC_API_KEY"] == "api-key"
    assert prepared.options["env"]["ANTHROPIC_AUTH_TOKEN"] == "auth-token"
    assert prepared.sanitized_env_vars == ()
