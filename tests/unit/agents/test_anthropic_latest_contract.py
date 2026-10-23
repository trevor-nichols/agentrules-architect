from __future__ import annotations

import threading
from datetime import date, timedelta
from types import SimpleNamespace
from typing import Any

import pytest

from agentrules.cli.ui.settings.models.utils import build_model_choice_state
from agentrules.config.agents import MODEL_PRESETS
from agentrules.core.agents.anthropic import AnthropicArchitect
from agentrules.core.agents.anthropic.client import set_client
from agentrules.core.agents.anthropic.request_builder import prepare_request
from agentrules.core.agents.base import ReasoningMode
from agentrules.core.configuration.model_presets import (
    get_preset_info,
    resolve_runtime_preset_key,
)


@pytest.mark.parametrize(
    ("preset_key", "wire_model", "effort"),
    [
        ("claude-opus-5.5", "claude-opus-5-5", "medium"),
        ("claude-sonnet-5.5", "claude-sonnet-5-5", "high"),
        ("claude-haiku-5.5", "claude-haiku-5-5", "medium"),
        ("claude-fable-5.1", "claude-fable-5-1", "high"),
    ],
)
def test_latest_anthropic_presets_build_supported_structured_requests(
    preset_key: str, wire_model: str, effort: str
) -> None:
    config = MODEL_PRESETS[preset_key]["config"]
    output_format = {"type": "json_schema", "schema": {"type": "object"}}

    prepared = prepare_request(
        model_name=config.model_name,
        prompt="Inspect the repository",
        reasoning=config.reasoning,
        tools=[{"name": "inspect", "input_schema": {"type": "object"}}],
        effort=config.anthropic_effort,
        output_format=output_format,
    )

    assert prepared.payload["model"] == wire_model
    assert prepared.payload["output_config"] == {"effort": effort, "format": output_format}
    assert prepared.payload["tools"][0]["name"] == "inspect"
    assert prepared.payload.get("thinking") != {"type": "enabled"}
    assert config.max_input_tokens == 872_000


@pytest.mark.parametrize(
    ("model_name", "reasoning", "effort", "expected_thinking"),
    [
        ("claude-sonnet-5-5", ReasoningMode.DISABLED, "high", "between_tools"),
        ("claude-haiku-5-5", ReasoningMode.DISABLED, "low", "disabled"),
        ("claude-haiku-5-5", ReasoningMode.DYNAMIC, "max", "adaptive"),
    ],
)
def test_latest_anthropic_thinking_modes(
    model_name: str, reasoning: ReasoningMode, effort: str, expected_thinking: str | None
) -> None:
    prepared = prepare_request(
        model_name=model_name,
        prompt="Inspect the repository",
        reasoning=reasoning,
        tools=None,
        effort=effort,
    )

    assert prepared.payload.get("thinking", {}).get("type") == expected_thinking


@pytest.mark.parametrize(
    ("model_name", "reasoning", "effort"),
    [
        ("claude-opus-5-5", ReasoningMode.DISABLED, "medium"),
        ("claude-fable-5-1", ReasoningMode.DISABLED, "high"),
        ("claude-sonnet-5-5", ReasoningMode.DISABLED, "xhigh"),
        ("claude-haiku-5-5", ReasoningMode.DISABLED, "max"),
    ],
)
def test_latest_anthropic_rejects_unsupported_thinking_before_dispatch(
    model_name: str, reasoning: ReasoningMode, effort: str
) -> None:
    with pytest.raises(ValueError):
        prepare_request(
            model_name=model_name,
            prompt="Inspect the repository",
            reasoning=reasoning,
            tools=None,
            effort=effort,
        )


def test_latest_anthropic_rejects_output_over_model_limit() -> None:
    with pytest.raises(ValueError, match="exceeds model"):
        prepare_request(
            model_name="claude-opus-5-5",
            prompt="Inspect the repository",
            reasoning=ReasoningMode.DYNAMIC,
            tools=None,
            max_tokens=128_001,
        )


def test_direct_anthropic_default_uses_current_sonnet() -> None:
    architect = AnthropicArchitect()
    prepared = architect._prepare_request("Inspect the repository", None)

    assert prepared.payload["model"] == "claude-sonnet-5-5"
    assert prepared.payload["thinking"] == {"type": "between_tools"}


def test_fable_retention_is_visible_in_picker_group() -> None:
    info = get_preset_info("claude-fable-5.1")
    assert info is not None
    low_info = get_preset_info("claude-fable-5.1-reasoning-low")
    assert low_info is not None
    state = build_model_choice_state(
        [info, low_info],
        current_key=None,
        default_key=None,
        include_reset=False,
        reset_title="Reset",
    )
    labels = [part[1] for choice in state.choices for part in getattr(choice, "title", []) if isinstance(part, tuple)]
    assert any("30-day retention" in label for label in labels)


@pytest.mark.parametrize(
    ("saved_key", "replacement"),
    [
        ("claude-sonnet", "claude-sonnet-5.5-between-tools"),
        ("claude-sonnet-reasoning", "claude-sonnet-5.5"),
    ],
)
def test_sonnet_45_saved_key_preserves_wire_until_retirement(
    saved_key: str, replacement: str
) -> None:
    retirement = date(2026, 11, 30)
    assert resolve_runtime_preset_key(saved_key, as_of=retirement - timedelta(days=1)) == saved_key
    assert MODEL_PRESETS[saved_key]["config"].model_name == "claude-sonnet-4-5"
    assert resolve_runtime_preset_key(saved_key, as_of=retirement) == replacement
    assert MODEL_PRESETS[replacement]["config"].model_name == "claude-sonnet-5-5"
    assert resolve_runtime_preset_key(replacement, as_of=retirement) == replacement


def test_sonnet_45_picker_discloses_scheduled_replacement() -> None:
    infos = [get_preset_info(key) for key in ("claude-sonnet", "claude-sonnet-reasoning")]
    assert all(info is not None for info in infos)
    assert infos[1] is not None and "Extended Thinking → Adaptive" in infos[1].label
    state = build_model_choice_state(
        [info for info in infos if info is not None],
        current_key="claude-sonnet",
        default_key=None,
        include_reset=False,
        reset_title="Reset",
    )

    group = next(choice for choice in state.choices if str(getattr(choice, "value", "")).startswith("__GROUP__"))
    assert "2026-11-30" in str(group.title)
    assert "Sonnet 5.5" in str(group.title)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "model_name",
    ["claude-fable-5-1", "claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"],
)
async def test_latest_anthropic_refusal_never_returns_partial_findings(model_name: str) -> None:
    class Messages:
        def create(self, **_kwargs: Any) -> Any:
            return SimpleNamespace(
                content=[SimpleNamespace(type="text", text="partial analysis")],
                stop_reason="refusal",
                stop_details=SimpleNamespace(category="policy", explanation=None),
            )

    set_client(SimpleNamespace(messages=Messages()))
    try:
        architect = AnthropicArchitect(model_name=model_name, reasoning=ReasoningMode.DYNAMIC)
        result = await architect.analyze({"formatted_prompt": "Inspect the repository"})
        assert "Anthropic refused the request" in result["error"]
        assert "findings" not in result
    finally:
        set_client(None)


@pytest.mark.asyncio
async def test_anthropic_sync_sdk_error_returns_existing_error_result_without_blocking_loop() -> None:
    event_loop_thread = threading.get_ident()
    sdk_threads: list[int] = []

    class Messages:
        def count_tokens(self, **_kwargs: Any) -> Any:
            sdk_threads.append(threading.get_ident())
            return SimpleNamespace(input_tokens=1)

        def create(self, **_kwargs: Any) -> Any:
            sdk_threads.append(threading.get_ident())
            raise RuntimeError("provider unavailable")

    set_client(SimpleNamespace(messages=Messages()))
    try:
        architect = AnthropicArchitect(model_name="claude-sonnet-5-5", reasoning=ReasoningMode.DYNAMIC)
        result = await architect.analyze({"formatted_prompt": "Inspect the repository"})
        assert len(sdk_threads) == 2
        assert all(thread_id != event_loop_thread for thread_id in sdk_threads)
        assert result["error"] == "provider unavailable"
    finally:
        set_client(None)
