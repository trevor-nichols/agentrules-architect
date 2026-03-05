from __future__ import annotations

from agentrules.core.agents.factory.factory import ArchitectFactory
from agentrules.core.types.models import GPT4_1_DEFAULT


def test_factory_attaches_system_prompt_when_missing() -> None:
    architect = ArchitectFactory.create_architect(
        model_config=GPT4_1_DEFAULT,
        name="Policy Agent",
        role="risk analysis",
        responsibilities=["Find reliability risks"],
        prompt_template="{context}",
    )

    prepared = architect._prepare_request("hello", tools=None)  # type: ignore[attr-defined]
    if prepared.api == "responses":
        assert "instructions" in prepared.payload
        assert "Policy Agent" in prepared.payload["instructions"]
    else:
        assert prepared.payload["messages"][0]["role"] == "developer"
        assert "Policy Agent" in prepared.payload["messages"][0]["content"]


def test_factory_explicit_system_prompt_overrides_default() -> None:
    architect = ArchitectFactory.create_architect(
        model_config=GPT4_1_DEFAULT,
        name="Explicit Agent",
        role="risk analysis",
        responsibilities=["Find reliability risks"],
        prompt_template="{context}",
        system_prompt="Use concise risk bullets only.",
    )

    prepared = architect._prepare_request("hello", tools=None)  # type: ignore[attr-defined]
    if prepared.api == "responses":
        assert prepared.payload.get("instructions") == "Use concise risk bullets only."
    else:
        assert prepared.payload["messages"][0]["role"] == "developer"
        assert prepared.payload["messages"][0]["content"] == "Use concise risk bullets only."
