"""Current Gemini picker choices resolve to their documented request budgets."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pytest
from google.genai.types import ThinkingLevel

from agentrules.config.agents import MODEL_PRESETS
from agentrules.core.agents.base import ReasoningMode
from agentrules.core.agents.gemini import GeminiArchitect
from agentrules.core.utils.token_estimator import compute_effective_limits
from tests.fakes.vendor_responses import GeminiGenerateContentResponseFake


@pytest.mark.parametrize(
    ("key", "wire_model", "reasoning", "input_limit"),
    [
        ("gemini-3.8-flash", "gemini-3.8-flash", ReasoningMode.MEDIUM, 1_048_576),
        ("gemini-3.8-flash-reasoning-low", "gemini-3.8-flash", ReasoningMode.LOW, 1_048_576),
        ("gemini-3.8-flash-reasoning-high", "gemini-3.8-flash", ReasoningMode.HIGH, 1_048_576),
        ("gemini-4-argon", "gemini-4-argon", ReasoningMode.MEDIUM, 983_040),
        ("gemini-4-argon-reasoning-low", "gemini-4-argon", ReasoningMode.LOW, 983_040),
        ("gemini-4-argon-reasoning-high", "gemini-4-argon", ReasoningMode.HIGH, 983_040),
    ],
)
def test_current_gemini_picker_choice_has_valid_request_and_packing_limit(
    key: str,
    wire_model: str,
    reasoning: ReasoningMode,
    input_limit: int,
) -> None:
    preset = MODEL_PRESETS[key]
    config = preset["config"]

    assert config.model_name == wire_model
    assert config.reasoning == reasoning
    assert config.max_input_tokens == input_limit
    _, _, effective_limit = compute_effective_limits(config.max_input_tokens, config.safety_margin_tokens)
    assert effective_limit is not None and effective_limit < input_limit


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("model_name", "expected_level"),
    [
        ("gemini-4-argon", ThinkingLevel.MEDIUM),
        ("gemini-4-carbon", ThinkingLevel.MEDIUM),
        ("gemini-4-hydrogen", ThinkingLevel.HIGH),
        ("gemini-4-neon", ThinkingLevel.HIGH),
    ],
)
async def test_gemini4_direct_request_uses_model_default_and_shared_window(
    model_name: str, expected_level: str
) -> None:
    calls: list[dict[str, Any]] = []

    def generate_content(**request: Any) -> GeminiGenerateContentResponseFake:
        calls.append(request)
        return GeminiGenerateContentResponseFake(text="hello")

    architect = GeminiArchitect(model_name=model_name)
    architect.client = cast(Any, SimpleNamespace(models=SimpleNamespace(generate_content=generate_content)))

    result = await architect.analyze({"formatted_prompt": "Analyze the project"})

    assert result["findings"] == "hello"
    request, = calls
    assert request["model"] == model_name
    config = request["config"]
    assert config.thinking_config.thinking_level == expected_level
    assert config.thinking_config.thinking_budget is None
    assert config.max_output_tokens == 65_536
    assert config.automatic_continuation
    assert config.http_options.timeout == 1_200_000
