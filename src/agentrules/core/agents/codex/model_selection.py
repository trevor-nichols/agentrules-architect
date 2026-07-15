"""Resolve configured Codex model selections against the live runtime catalog."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from agentrules.core.agents.base import ReasoningMode
from agentrules.core.configuration import model_presets

from .models import CodexModelInfo


@dataclass(frozen=True)
class ResolvedCodexModelSelection:
    """Concrete model/effort pair safe to send to the Codex runtime."""

    model_name: str | None
    reasoning_effort: str | None
    display_name: str


def resolve_model_selection(
    *,
    available_models: Sequence[CodexModelInfo],
    requested_model_name: str,
    requested_reasoning: ReasoningMode,
) -> ResolvedCodexModelSelection:
    """Resolve a configured Codex selection using the live runtime model catalog."""

    if not available_models:
        raise ValueError("Codex runtime returned no visible models; cannot validate the configured Codex selection.")

    if requested_model_name == model_presets.CODEX_RUNTIME_DEFAULT_MODEL_NAME:
        default_model = next((model for model in available_models if model.is_default), None)
        if default_model is None:
            return ResolvedCodexModelSelection(
                model_name=None,
                reasoning_effort=None,
                display_name="Codex runtime default",
            )
        return ResolvedCodexModelSelection(
            model_name=default_model.model,
            reasoning_effort=default_model.default_reasoning_effort,
            display_name=default_model.display_name or default_model.model,
        )

    selected_model = _find_matching_model(available_models, requested_model_name)
    if selected_model is None:
        available = ", ".join(model.model for model in available_models)
        raise ValueError(
            f"Configured Codex model '{requested_model_name}' is not available from the current Codex account. "
            f"Available models: {available}."
        )

    requested_effort = _requested_reasoning_effort(requested_reasoning)
    if requested_effort is None:
        requested_effort = selected_model.default_reasoning_effort
    supported_efforts = _allowed_reasoning_efforts(selected_model)
    if requested_effort is not None and supported_efforts and requested_effort not in supported_efforts:
        supported = ", ".join(supported_efforts)
        raise ValueError(
            f"Configured Codex model '{selected_model.model}' does not support reasoning effort "
            f"'{requested_effort}'. Supported values: {supported}."
        )

    resolved_model_name = _resolve_request_model_name(
        requested_model_name=requested_model_name,
        matched_model_name=selected_model.model,
    )
    return ResolvedCodexModelSelection(
        model_name=resolved_model_name,
        reasoning_effort=requested_effort,
        display_name=selected_model.display_name or selected_model.model,
    )


def normalize_requested_model_name(requested_model_name: str) -> str:
    return model_presets.normalize_codex_runtime_model_name(requested_model_name)


def _find_matching_model(
    available_models: Sequence[CodexModelInfo],
    requested_model_name: str,
) -> CodexModelInfo | None:
    normalized_model_name = normalize_requested_model_name(requested_model_name)
    exact_match = next((model for model in available_models if model.model == requested_model_name), None)
    if exact_match is not None:
        return exact_match

    canonical_match = next((model for model in available_models if model.model == normalized_model_name), None)
    if canonical_match is not None:
        return canonical_match

    return next(
        (
            model
            for model in available_models
            if normalize_requested_model_name(model.model) == normalized_model_name
        ),
        None,
    )


def _resolve_request_model_name(
    *,
    requested_model_name: str,
    matched_model_name: str,
) -> str:
    normalized_requested_model_name = normalize_requested_model_name(requested_model_name)
    if (
        requested_model_name != normalized_requested_model_name
        and matched_model_name == normalized_requested_model_name
    ):
        return requested_model_name
    return matched_model_name


def _allowed_reasoning_efforts(model: CodexModelInfo) -> tuple[str, ...]:
    efforts: list[str] = []

    def _append(value: str | None) -> None:
        if value is not None and value not in efforts:
            efforts.append(value)

    _append(model.default_reasoning_effort)
    for option in model.supported_reasoning_efforts:
        _append(option.reasoning_effort)
    return tuple(efforts)


def _requested_reasoning_effort(reasoning: ReasoningMode) -> str | None:
    if reasoning == ReasoningMode.DYNAMIC:
        return None
    if reasoning == ReasoningMode.DISABLED:
        return "none"
    if reasoning == ReasoningMode.MINIMAL:
        return "minimal"
    if reasoning in {
        ReasoningMode.LOW,
        ReasoningMode.MEDIUM,
        ReasoningMode.HIGH,
        ReasoningMode.XHIGH,
        ReasoningMode.MAX,
    }:
        return reasoning.value
    if reasoning == ReasoningMode.ENABLED:
        return ReasoningMode.MEDIUM.value
    return "none"
