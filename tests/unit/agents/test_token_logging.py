import logging

import pytest

from agentrules.config import agents as agents_config
from agentrules.core.agents.anthropic import architect as anthro_mod
from agentrules.core.agents.anthropic.request_builder import PreparedRequest as AnthropicPrepared
from agentrules.core.agents.deepseek import architect as deepseek_mod
from agentrules.core.agents.deepseek.request_builder import PreparedRequest as DeepSeekPrepared
from agentrules.core.agents.gemini import architect as gemini_mod
from agentrules.core.agents.openai import architect as openai_mod
from agentrules.core.agents.openai.request_builder import PreparedRequest as OpenAIPrepared
from agentrules.core.agents.xai import architect as xai_mod
from agentrules.core.agents.xai.request_builder import PreparedRequest as XaiPrepared
from agentrules.core.types import models as model_types
from agentrules.core.utils.token_estimator import TokenEstimateResult
from agentrules.core.utils.token_packer import pack_files_for_phase3


@pytest.fixture(autouse=True)
def _set_log_level(caplog):
    caplog.set_level(logging.INFO, logger="project_extractor")


@pytest.fixture
def fake_estimate(monkeypatch):
    def _fake(*args, **kwargs):
        return TokenEstimateResult(123, "fake")

    monkeypatch.setattr(openai_mod, "estimate_tokens", _fake)
    monkeypatch.setattr(anthro_mod, "estimate_tokens", _fake)
    monkeypatch.setattr(deepseek_mod, "estimate_tokens", _fake)
    monkeypatch.setattr(xai_mod, "estimate_tokens", _fake)
    monkeypatch.setattr(gemini_mod, "estimate_tokens", _fake)
    return _fake


def _dummy_model_config():
    # Use an existing config as a template and attach limits.
    cfg = model_types.GPT4_1_DEFAULT
    return cfg._replace(max_input_tokens=200_000, estimator_family="tiktoken")


def test_openai_token_log(caplog, fake_estimate):
    arch = openai_mod.OpenAIArchitect(model_name="o3", model_config=_dummy_model_config())
    prepared = OpenAIPrepared(api="chat", payload={"messages": [{"role": "user", "content": "hi"}]})
    arch._log_token_estimate(prepared)
    assert "Token preflight" in caplog.text
    assert "estimate=123" in caplog.text


def test_anthropic_token_log(caplog, fake_estimate):
    arch = anthro_mod.AnthropicArchitect(model_name="claude-sonnet-4.5", model_config=_dummy_model_config())
    prepared = AnthropicPrepared(payload={"messages": [{"role": "user", "content": "hi"}]})
    arch._log_token_estimate(prepared)
    assert "Token preflight" in caplog.text
    assert "estimate=123" in caplog.text


def test_deepseek_token_log(caplog, fake_estimate):
    arch = deepseek_mod.DeepSeekArchitect(model_name="deepseek-chat", model_config=_dummy_model_config())
    prepared = DeepSeekPrepared(payload={"messages": [{"role": "user", "content": "hi"}]})
    arch._log_token_estimate(prepared)
    assert "Token preflight" in caplog.text
    assert "estimate=123" in caplog.text


def test_xai_token_log(caplog, fake_estimate):
    arch = xai_mod.XaiArchitect(model_name="grok-4-0709", model_config=_dummy_model_config())
    prepared = XaiPrepared(payload={"messages": [{"role": "user", "content": "hi"}]})
    arch._log_token_estimate(prepared)
    assert "Token preflight" in caplog.text
    assert "estimate=123" in caplog.text


def test_gemini_token_log(caplog, fake_estimate, monkeypatch):
    monkeypatch.setattr(gemini_mod, "build_gemini_client", lambda _key=None: (None, None))
    arch = gemini_mod.GeminiArchitect(model_name="gemini-2.5-flash", model_config=_dummy_model_config())
    arch._log_token_estimate("hi", config=None)
    assert "Token preflight" in caplog.text
    assert "estimate=123" in caplog.text


def test_gpt5_mini_logs_limits(caplog, monkeypatch):
    def _fake_estimator(*args, **kwargs):
        return TokenEstimateResult(321, "fake")

    monkeypatch.setattr(openai_mod, "estimate_tokens", _fake_estimator)
    cfg = agents_config._apply_model_limits(model_types.GPT5_MINI)
    arch = openai_mod.OpenAIArchitect(model_name="gpt-5-mini", model_config=cfg)
    prepared = OpenAIPrepared(api="chat", payload={"messages": [{"role": "user", "content": "hi"}]})
    arch._log_token_estimate(prepared)

    assert "Token preflight" in caplog.text
    assert "estimate=321" in caplog.text
    assert "limit=400000" in caplog.text
    assert "effective_limit=360000" in caplog.text


def test_openai_prepare_and_log_responses_path(caplog, monkeypatch):
    recorded: dict[str, object] = {}

    def _fake_estimator(provider, model_name, payload, api=None, estimator_family=None, **kwargs):
        recorded["provider"] = provider
        recorded["model_name"] = model_name
        recorded["payload"] = payload
        recorded["api"] = api
        recorded["estimator_family"] = estimator_family
        return TokenEstimateResult(111, "fake")

    monkeypatch.setattr(openai_mod, "estimate_tokens", _fake_estimator)
    cfg = agents_config._apply_model_limits(model_types.GPT5_MINI)
    arch = openai_mod.OpenAIArchitect(model_name="gpt-5-mini", model_config=cfg)

    prepared = arch._prepare_request("hello world", tools=None)
    assert prepared.api == "responses"
    assert prepared.payload["input"] == "hello world"

    arch._log_token_estimate(prepared)

    assert recorded["payload"] == prepared.payload
    assert recorded["api"] == "responses"
    assert "Token preflight" in caplog.text
    assert "estimate=111" in caplog.text
    assert "limit=400000" in caplog.text
    assert "effective_limit=360000" in caplog.text


def test_anthropic_log_nonzero_with_packer_payload(caplog, monkeypatch):
    calls: dict[str, object] = {}

    def _fake_estimator(provider, model_name, payload, estimator_family=None, api=None, client=None):
        calls["payload"] = payload
        return TokenEstimateResult(77, "fake")

    monkeypatch.setattr(anthro_mod, "estimate_tokens", _fake_estimator)
    cfg = model_types.ModelConfig(
        provider=model_types.ModelProvider.ANTHROPIC,
        model_name="claude-3-5",
        reasoning=model_types.ReasoningMode.MEDIUM,
        max_input_tokens=200_000,
        estimator_family="anthropic_api",
    )

    batches = pack_files_for_phase3(
        files_with_content={"a.py": "hello world"},
        tree=[],
        model_config=cfg,
    )
    batch = batches[0]
    arch = anthro_mod.AnthropicArchitect(model_name="claude-3-5", model_config=cfg)
    context = {
        "agent_name": "Anthro",
        "agent_role": "Analyze files",
        "assigned_files": batch.assigned_files,
        "file_contents": batch.file_contents,
        "tree_structure": [],
        "previous_summary": None,
    }
    prompt = arch.format_prompt(context)
    prepared = AnthropicPrepared(payload={"messages": [{"role": "user", "content": prompt}]})
    arch._log_token_estimate(prepared)

    assert "Token preflight" in caplog.text
    assert "estimate=77" in caplog.text
    payload = calls.get("payload")
    assert isinstance(payload, dict)
    messages = payload.get("messages")
    assert isinstance(messages, list)
