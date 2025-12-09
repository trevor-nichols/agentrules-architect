from agentrules.core.agents.base import ModelProvider, ReasoningMode
from agentrules.core.types.models import ModelConfig
from agentrules.core.utils.token_estimator import TokenEstimateResult
from agentrules.core.utils.token_packer import pack_files_for_phase3


def _cfg(limit: int) -> ModelConfig:
    return ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="gpt-5-mini",
        reasoning=ReasoningMode.MEDIUM,
        max_input_tokens=limit,
        estimator_family="heuristic",
    )


def test_pack_splits_on_limit():
    files = {
        "a.py": "a" * 2000,
        "b.py": "b" * 2000,
        "c.py": "c" * 2000,
    }
    batches = pack_files_for_phase3(
        files_with_content=files,
        tree=[],
        model_config=_cfg(limit=1500),
    )
    assert len(batches) >= 2
    combined_files = [f for batch in batches for f in batch.assigned_files]
    assert combined_files == ["a.py", "b.py", "c.py"]


def test_pack_summarizes_oversize_single():
    files = {"big.py": "x" * 10_000}
    batches = pack_files_for_phase3(
        files_with_content=files,
        tree=[],
        model_config=_cfg(limit=500),
    )
    assert len(batches) == 1
    batch = batches[0]
    assert list(batch.file_contents.keys()) == ["big.py"]
    assert len(batch.file_contents["big.py"]) < 10_000  # summarized/truncated


def test_pack_estimation_uses_anthropic_messages(monkeypatch):
    files = {"a.py": "hello"}
    calls = {}

    def _fake_estimate(provider, model_name, payload, estimator_family=None, api=None):
        calls["provider"] = provider
        calls["payload"] = payload
        calls["api"] = api
        calls["family"] = estimator_family
        return TokenEstimateResult(50, "fake")

    monkeypatch.setattr("agentrules.core.utils.token_packer.estimate_tokens", _fake_estimate)
    cfg = ModelConfig(
        provider=ModelProvider.ANTHROPIC,
        model_name="claude-3-5",
        reasoning=ReasoningMode.MEDIUM,
        max_input_tokens=1000,
        estimator_family="anthropic_api",
    )
    pack_files_for_phase3(files_with_content=files, tree=[], model_config=cfg)

    assert isinstance(calls["payload"], dict)
    assert "messages" in calls["payload"]
    msg = calls["payload"]["messages"][0]
    assert msg["role"] == "user"
    assert isinstance(msg["content"], str)
    assert calls["api"] is None
    assert calls["family"] == "anthropic_api"


def test_pack_no_model_config_returns_single_batch():
    files = {"a.py": "hello", "b.py": "world"}
    batches = pack_files_for_phase3(files_with_content=files, tree=[], model_config=None)
    assert len(batches) >= 1
    combined = {f for batch in batches for f in batch.assigned_files}
    assert combined == {"a.py", "b.py"}
