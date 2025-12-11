"""
Provider-aware token estimation utilities.

This module keeps estimation logic isolated so we can:
- swap estimators per provider/model,
- degrade gracefully when SDK count endpoints are unavailable,
- keep architect code lean (log-only in first iteration).
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from math import ceil
from typing import Any, NamedTuple

from agentrules.core.agents.base import ModelProvider

logger = logging.getLogger("project_extractor")


class TokenEstimateResult(NamedTuple):
    estimated: int | None
    source: str
    error: str | None = None


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def estimate_tokens(
    provider: ModelProvider,
    model_name: str,
    payload: dict[str, Any],
    *,
    api: str | None = None,
    estimator_family: str | None = None,
    client: Any | None = None,
) -> TokenEstimateResult:
    """
    Estimate input tokens for a prepared provider payload.

    Args:
        provider: Provider identifier.
        model_name: Model name used to select encoding/count endpoint.
        payload: The request payload that will be sent.
        api: Optional API variant (e.g., "responses" vs "chat" for OpenAI).
        estimator_family: Optional override for which estimator to use.
        client: Optional pre-initialized provider SDK client.
    """
    family = estimator_family or _default_family(provider)

    if family == "anthropic_api":
        return _estimate_anthropic(payload, client)

    if family == "gemini_api":
        return _estimate_gemini(model_name, payload, client)

    if family == "tiktoken":
        return _estimate_tiktoken(model_name, payload, api)

    return _estimate_heuristic(payload)


def compute_effective_limits(
    max_input_tokens: int | None,
    safety_margin_tokens: int | None,
) -> tuple[int | None, int | None, int | None]:
    """Return (limit, margin, effective_limit) with defaults applied."""
    if max_input_tokens is None:
        return None, None, None

    limit = max_input_tokens
    margin = safety_margin_tokens

    if margin is None:
        margin = max(4_000, int(0.10 * limit))
    # Never allow margin to exceed the limit; clamp to avoid negatives.
    margin = min(margin, max(limit - 1, 0))

    effective = limit - margin
    if effective < 0:
        effective = 0

    return limit, margin, effective


# --------------------------------------------------------------------------- #
# Estimators
# --------------------------------------------------------------------------- #

def _estimate_anthropic(payload: dict[str, Any], client: Any | None) -> TokenEstimateResult:
    try:
        if client is None:
            from agentrules.core.agents.anthropic.client import get_client  # lazy import

            client = get_client()

        response = client.messages.count_tokens(**payload)  # type: ignore[arg-type]
        tokens = getattr(response, "input_tokens", None)
        if tokens is None and isinstance(response, dict):
            tokens = response.get("input_tokens")
        return TokenEstimateResult(tokens, "anthropic_api")
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.debug("Anthropic count_tokens failed: %s", exc, exc_info=True)
        return TokenEstimateResult(None, "anthropic_api_error", str(exc))


def _estimate_gemini(model_name: str, payload: dict[str, Any], client: Any | None) -> TokenEstimateResult:
    try:
        contents = payload.get("contents") or payload.get("input") or payload.get("messages")
        config = payload.get("config")
        count_config = None
        if config is not None:
            try:
                from google.genai import types as genai_types  # type: ignore
                count_tokens_cls = getattr(genai_types, "CountTokensConfig", None)
                if count_tokens_cls and isinstance(config, count_tokens_cls):
                    count_config = config
            except Exception:
                # If we cannot import or match, fall back to no config to avoid warnings.
                count_config = None
        if client is None:
            from agentrules.core.agents.gemini.client import build_gemini_client  # lazy import

            client, _ = build_gemini_client(None)

        response = client.models.count_tokens(model=model_name, contents=contents, config=count_config)  # type: ignore[arg-type]
        tokens = (
            getattr(response, "total_tokens", None)
            or getattr(response, "input_tokens", None)
            or getattr(response, "prompt_token_count", None)
        )
        return TokenEstimateResult(tokens, "gemini_api")
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.debug("Gemini count_tokens failed: %s", exc, exc_info=True)
        return TokenEstimateResult(None, "gemini_api_error", str(exc))


def _estimate_tiktoken(model_name: str, payload: dict[str, Any], api: str | None) -> TokenEstimateResult:
    try:
        import tiktoken  # type: ignore
    except ImportError:
        return TokenEstimateResult(None, "tiktoken_unavailable", "Install tiktoken to enable local estimates.")

    try:
        try:
            encoding = tiktoken.encoding_for_model(model_name)
        except Exception:
            encoding = tiktoken.get_encoding("cl100k_base")

        text = _extract_text(payload, api)
        tokens = len(encoding.encode(text))
        return TokenEstimateResult(tokens, "tiktoken")
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.debug("tiktoken estimate failed: %s", exc, exc_info=True)
        return TokenEstimateResult(None, "tiktoken_error", str(exc))


def _estimate_heuristic(payload: dict[str, Any]) -> TokenEstimateResult:
    text = _extract_text(payload, None)
    estimate = ceil(len(text) / 4) if text else 0
    return TokenEstimateResult(estimate, "heuristic")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _default_family(provider: ModelProvider) -> str:
    if provider == ModelProvider.ANTHROPIC:
        return "anthropic_api"
    if provider == ModelProvider.GEMINI:
        return "gemini_api"
    return "tiktoken"


def _extract_text(payload: dict[str, Any], api: str | None) -> str:
    """Flatten common payload shapes into a single string for counting."""
    if "messages" in payload:
        return _flatten_messages(payload["messages"])
    if api == "responses" and "input" in payload:
        return str(payload.get("input", ""))
    if "input" in payload:
        return str(payload.get("input", ""))
    return str(payload)


def _flatten_messages(messages: Iterable[Any]) -> str:
    parts: list[str] = []
    for msg in messages or []:
        role = getattr(msg, "get", None) and msg.get("role")
        content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", "")
        if isinstance(content, list):
            content = " ".join(str(c) for c in content)
        parts.append(f"{role}: {content}")
    return "\n".join(parts)

