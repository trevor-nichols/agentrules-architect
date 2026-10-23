"""Current Gemini picker choices resolve to their documented request budgets."""

from __future__ import annotations

import pytest

from agentrules.config.agents import MODEL_PRESETS
from agentrules.core.agents.base import ReasoningMode
from agentrules.core.utils.token_estimator import compute_effective_limits


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
