from datetime import date, timedelta

import pytest

from agentrules.config.agents import MODEL_PRESETS
from agentrules.core.configuration.model_presets import (
    get_preset_deprecation_info,
    resolve_runtime_preset_key,
)


@pytest.mark.parametrize(
    ("retirement_date", "mappings"),
    [
        (
            date(2026, 12, 11),
            {
                "o3-low": "gpt56-sol-low",
                "o3-medium": "gpt56-sol-default",
                "o3-high": "gpt56-sol-high",
                "gpt5-default": "gpt56-sol-default",
                "gpt5-minimal": "gpt56-sol-none",
                "gpt5-high": "gpt56-sol-high",
            },
        ),
        (
            date(2027, 1, 14),
            {
                "gpt4.1-default": "gpt6-luna-default",
                "gpt4.1-creative": "gpt6-luna-default",
                "gpt4.1-precise": "gpt6-luna-default",
            },
        ),
        (
            date(2027, 4, 1),
            {
                "gpt51-default": "gpt6-sol-default",
                "gpt51-minimal": "gpt6-sol-none",
                "gpt51-high": "gpt6-sol-high",
                "gpt-5.3-codex": "gpt6-sol-default",
                "gpt54-nano-none": "gpt6-luna-none",
                "gpt54-nano-low": "gpt6-luna-low",
                "gpt54-nano-medium": "gpt6-luna-default",
                "gpt54-nano-high": "gpt6-luna-high",
                "gpt54-nano-xhigh": "gpt6-luna-xhigh",
            },
        ),
    ],
)
def test_live_openai_presets_keep_wire_model_until_retirement_then_redirect_once(
    retirement_date: date, mappings: dict[str, str]
) -> None:
    for saved_key, replacement in mappings.items():
        deprecation = get_preset_deprecation_info(saved_key)
        assert deprecation is not None
        assert deprecation.retirement_date == retirement_date
        assert deprecation.retirement_replacement_key == replacement
        assert resolve_runtime_preset_key(saved_key, as_of=retirement_date - timedelta(days=1)) == saved_key
        assert resolve_runtime_preset_key(saved_key, as_of=retirement_date) == replacement
        assert replacement in MODEL_PRESETS
        assert resolve_runtime_preset_key(replacement, as_of=retirement_date) == replacement
