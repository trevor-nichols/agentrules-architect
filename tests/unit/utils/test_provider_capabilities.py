from types import SimpleNamespace

from agentrules.core.agents.base import ModelProvider, ReasoningMode
from agentrules.core.types.models import ModelConfig
from agentrules.core.utils.provider_capabilities import (
    requires_external_research_tool_loop,
    resolve_provider,
    should_embed_phase3_file_contents,
    uses_repo_runtime,
    uses_runtime_native_web_search,
)


def test_codex_runtime_capabilities_are_centralized() -> None:
    codex_config = ModelConfig(
        provider=ModelProvider.CODEX,
        model_name="gpt-5.3-codex",
        reasoning=ReasoningMode.MEDIUM,
    )
    codex_architect = SimpleNamespace(provider=ModelProvider.CODEX, _model_config=codex_config)
    openai_config = ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="gpt-5-mini",
        reasoning=ReasoningMode.MEDIUM,
    )

    assert resolve_provider(codex_architect) == ModelProvider.CODEX
    assert uses_repo_runtime(codex_architect) is True
    assert uses_runtime_native_web_search(codex_architect) is True
    assert requires_external_research_tool_loop(codex_architect) is False
    assert should_embed_phase3_file_contents(codex_architect) is False

    assert resolve_provider(openai_config) == ModelProvider.OPENAI
    assert uses_repo_runtime(openai_config) is False
    assert uses_runtime_native_web_search(openai_config) is False
    assert requires_external_research_tool_loop(openai_config) is True
    assert should_embed_phase3_file_contents(openai_config) is True
