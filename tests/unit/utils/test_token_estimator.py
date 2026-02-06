import sys

import pytest

from agentrules.config import agents as agents_config
from agentrules.core.agents.base import ModelProvider
from agentrules.core.types.models import ModelConfig
from agentrules.core.utils.token_estimator import (
    compute_effective_limits,
    estimate_tokens,
)


def test_heuristic_estimator_counts_chars_div4():
    payload = {"input": "abcd"}  # 4 chars -> ceil(4/4)=1
    result = estimate_tokens(
        provider=ModelProvider.OPENAI,
        model_name="gpt-unknown",
        payload=payload,
        estimator_family="heuristic",
    )
    assert result.estimated == 1
    assert result.source == "heuristic"


@pytest.mark.parametrize("model_name", ["gpt-4.1", "o3"])
def test_tiktoken_estimator_returns_positive(model_name):
    payload = {"input": "hello world"}
    result = estimate_tokens(
        provider=ModelProvider.OPENAI,
        model_name=model_name,
        payload=payload,
        api="responses",
        estimator_family="tiktoken",
    )
    assert result.source.startswith("tiktoken")
    assert result.estimated is None or result.estimated > 0


def test_tiktoken_unavailable(monkeypatch):
    import builtins

    original_import = builtins.__import__

    def _raise(name, *args, **kwargs):
        if name == "tiktoken":
            raise ImportError("missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _raise)
    result = estimate_tokens(
        provider=ModelProvider.OPENAI,
        model_name="gpt-4.1",
        payload={"input": "hello"},
        estimator_family="tiktoken",
    )
    assert result.source == "tiktoken_unavailable"
    assert result.estimated is None
    assert "Install tiktoken" in (result.error or "")


def test_tiktoken_encode_error(monkeypatch):
    class DummyEncoding:
        def encode(self, _text):
            raise RuntimeError("boom")

    class DummyTiktoken:
        @staticmethod
        def encoding_for_model(_name):
            return DummyEncoding()

        @staticmethod
        def get_encoding(_name):
            return DummyEncoding()

    monkeypatch.setitem(sys.modules, "tiktoken", DummyTiktoken())
    result = estimate_tokens(
        provider=ModelProvider.OPENAI,
        model_name="gpt-5",
        payload={"messages": [{"role": "user", "content": "hi"}]},
        estimator_family="tiktoken",
    )
    assert result.source == "tiktoken_error"
    assert result.estimated is None
    assert "boom" in (result.error or "")


def test_anthropic_estimator_strips_output_config() -> None:
    recorded: dict[str, object] = {}

    class FakeMessages:
        def count_tokens(self, **kwargs):  # type: ignore[no-untyped-def]
            recorded["kwargs"] = kwargs
            return {"input_tokens": 42}

    class FakeClient:
        messages = FakeMessages()

    payload = {
        "model": "claude-opus-4-6",
        "messages": [{"role": "user", "content": "hi"}],
        "output_config": {"effort": "low"},
    }
    result = estimate_tokens(
        provider=ModelProvider.ANTHROPIC,
        model_name="claude-opus-4-6",
        payload=payload,
        estimator_family="anthropic_api",
        client=FakeClient(),
    )

    assert result.estimated == 42
    kwargs = recorded.get("kwargs")
    assert isinstance(kwargs, dict)
    assert "output_config" not in kwargs


def test_compute_effective_limits_defaults():
    limit, margin, effective = compute_effective_limits(20_000, None)
    assert limit == 20_000
    assert margin == 4_000  # min(10%, 4000) chooses 4000 here
    assert effective == 16_000


def test_compute_effective_limits_custom_margin():
    limit, margin, effective = compute_effective_limits(50_000, 1_000)
    assert limit == 50_000
    assert margin == 1_000
    assert effective == 49_000


def test_compute_effective_limits_none_limit():
    limit, margin, effective = compute_effective_limits(None, None)
    assert limit is None
    assert margin is None
    assert effective is None


def test_compute_effective_limits_small_limit_is_clamped():
    limit, margin, effective = compute_effective_limits(3_000, None)
    assert limit == 3_000
    # margin clamped below limit to avoid negative
    assert margin is not None and margin < limit
    assert effective is not None and effective == limit - margin
    assert effective >= 0


def test_compute_effective_limits_margin_exceeds_limit():
    limit, margin, effective = compute_effective_limits(5_000, 10_000)
    assert limit == 5_000
    assert margin == 4_999  # clamped to limit - 1
    assert effective == 1


def test_apply_model_limits_openai_defaults():
    cfg = agents_config._apply_model_limits(agents_config.GPT5_1_DEFAULT)
    assert cfg.max_input_tokens == 400_000
    assert cfg.estimator_family == "tiktoken"


def test_apply_model_limits_preserves_existing():
    cfg = ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="custom",
        max_input_tokens=123,
        safety_margin_tokens=7,
        estimator_family="custom",
    )
    result = agents_config._apply_model_limits(cfg)
    assert result.max_input_tokens == 123
    assert result.safety_margin_tokens == 7
    assert result.estimator_family == "custom"
