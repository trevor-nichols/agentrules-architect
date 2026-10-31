"""Reviewed capabilities for direct OpenAI API models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from agentrules.core.agents.base import ReasoningMode

OpenAITransport = Literal["responses", "chat"]


@dataclass(frozen=True)
class OpenAIModelCapabilities:
    total_context_tokens: int
    max_input_tokens: int
    max_output_tokens: int
    accepted_efforts: frozenset[str]
    default_reasoning: ReasoningMode
    transport: OpenAITransport = "responses"
    supports_tools: bool = True
    supports_structured_output: bool = True
    default_temperature: float | None = None

    def __post_init__(self) -> None:
        if self.max_input_tokens + self.max_output_tokens > self.total_context_tokens:
            raise ValueError("OpenAI input and output limits exceed total context")


_STANDARD_EFFORTS = frozenset({"none", "low", "medium", "high", "xhigh"})
_GPT6_ALL_EFFORTS = _STANDARD_EFFORTS | {"max"}
_GPT6_REASONING_EFFORTS = _GPT6_ALL_EFFORTS - {"none"}


def _reasoning_model(
    *,
    total: int,
    output: int,
    efforts: frozenset[str],
    default: ReasoningMode = ReasoningMode.MEDIUM,
) -> OpenAIModelCapabilities:
    return OpenAIModelCapabilities(
        total_context_tokens=total,
        max_input_tokens=total - output,
        max_output_tokens=output,
        accepted_efforts=efforts,
        default_reasoning=default,
    )


# Wire IDs are exact. Direct API presets are reviewed here; moving Codex model
# names remain owned by the local app-server catalog.
OPENAI_MODEL_CAPABILITIES: Mapping[str, OpenAIModelCapabilities] = MappingProxyType({
    "gpt-6-astra": _reasoning_model(
        total=1_050_000, output=128_000, efforts=_GPT6_REASONING_EFFORTS
    ),
    "gpt-6.1-sol": _reasoning_model(
        total=1_050_000, output=128_000, efforts=_GPT6_REASONING_EFFORTS
    ),
    "gpt-6-sol": _reasoning_model(total=1_050_000, output=128_000, efforts=_GPT6_ALL_EFFORTS),
    "gpt-6-luna": _reasoning_model(total=1_050_000, output=128_000, efforts=_GPT6_ALL_EFFORTS),
    "gpt-5.6": _reasoning_model(total=1_050_000, output=128_000, efforts=_GPT6_ALL_EFFORTS),
    "gpt-5.6-sol": _reasoning_model(total=1_050_000, output=128_000, efforts=_GPT6_ALL_EFFORTS),
    "gpt-5.6-terra": _reasoning_model(total=1_050_000, output=128_000, efforts=_GPT6_ALL_EFFORTS),
    "gpt-5.6-luna": _reasoning_model(total=1_050_000, output=128_000, efforts=_GPT6_ALL_EFFORTS),
    "gpt-5.5": _reasoning_model(total=1_050_000, output=128_000, efforts=_STANDARD_EFFORTS),
    "gpt-5.4-2026-03-05": _reasoning_model(
        total=1_050_000, output=128_000, efforts=_STANDARD_EFFORTS,
        default=ReasoningMode.DISABLED,
    ),
    "gpt-5.4-mini": _reasoning_model(
        total=400_000, output=128_000, efforts=_STANDARD_EFFORTS,
        default=ReasoningMode.DISABLED,
    ),
    "gpt-5.4-nano": _reasoning_model(
        total=400_000, output=128_000, efforts=_STANDARD_EFFORTS,
        default=ReasoningMode.DISABLED,
    ),
    "gpt-5.3-codex": _reasoning_model(
        total=400_000, output=128_000,
        efforts=frozenset({"low", "medium", "high", "xhigh"}),
    ),
    "gpt-5.2": _reasoning_model(
        total=400_000, output=128_000, efforts=_STANDARD_EFFORTS,
        default=ReasoningMode.DISABLED,
    ),
    "gpt-5.2-codex": _reasoning_model(
        total=400_000, output=128_000,
        efforts=frozenset({"low", "medium", "high", "xhigh"}),
    ),
    "gpt-5.1": _reasoning_model(
        total=400_000, output=128_000,
        efforts=frozenset({"none", "low", "medium", "high"}),
        default=ReasoningMode.DISABLED,
    ),
    "gpt-5.1-codex": _reasoning_model(
        total=400_000, output=128_000,
        efforts=frozenset({"low", "medium", "high"}),
    ),
    "gpt-5": _reasoning_model(
        total=400_000, output=128_000,
        efforts=frozenset({"minimal", "low", "medium", "high"}),
    ),
    "gpt-5-mini": _reasoning_model(
        total=400_000, output=128_000,
        efforts=frozenset({"minimal", "low", "medium", "high"}),
    ),
    "o3": _reasoning_model(
        total=200_000, output=100_000,
        efforts=frozenset({"low", "medium", "high"}),
        default=ReasoningMode.HIGH,
    ),
    "o4-mini": _reasoning_model(
        total=200_000, output=100_000,
        efforts=frozenset({"low", "medium", "high"}),
        default=ReasoningMode.HIGH,
    ),
    "gpt-4.1": OpenAIModelCapabilities(
        total_context_tokens=1_047_576,
        max_input_tokens=1_014_808,
        max_output_tokens=32_768,
        accepted_efforts=frozenset(),
        default_reasoning=ReasoningMode.TEMPERATURE,
        default_temperature=0.7,
    ),
})


def get_openai_model_capabilities(model_name: str) -> OpenAIModelCapabilities | None:
    return OPENAI_MODEL_CAPABILITIES.get(model_name.lower())
