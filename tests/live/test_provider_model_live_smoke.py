"""Minimal, independently gated live smokes for direct model providers."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pytest
from anthropic import Anthropic
from google import genai
from google.genai import types as genai_types
from openai import OpenAI

from agentrules.core.agents.deepseek.config import DEFAULT_BASE_URL as DEEPSEEK_BASE_URL
from agentrules.core.agents.xai.config import DEFAULT_BASE_URL as XAI_BASE_URL

MAX_LIVE_OUTPUT_TOKENS = 32
LIVE_PROMPT = "Reply with exactly: OK"


@dataclass(frozen=True)
class LiveProviderCase:
    provider: str
    enable_flag: str
    key_env_vars: tuple[str, ...]
    model_env_var: str
    default_model: str
    runner: Callable[[str, str], object]


LIVE_PROVIDER_CASES = (
    LiveProviderCase(
        provider="openai",
        enable_flag="AGENTRULES_RUN_OPENAI_LIVE",
        key_env_vars=("OPENAI_API_KEY",),
        model_env_var="AGENTRULES_OPENAI_LIVE_MODEL",
        default_model="gpt-5.6-sol",
        runner=lambda api_key, model: _run_openai(api_key, model),
    ),
    LiveProviderCase(
        provider="anthropic",
        enable_flag="AGENTRULES_RUN_ANTHROPIC_LIVE",
        key_env_vars=("ANTHROPIC_API_KEY",),
        model_env_var="AGENTRULES_ANTHROPIC_LIVE_MODEL",
        default_model="claude-sonnet-5",
        runner=lambda api_key, model: _run_anthropic(api_key, model),
    ),
    LiveProviderCase(
        provider="gemini",
        enable_flag="AGENTRULES_RUN_GEMINI_LIVE",
        key_env_vars=("GOOGLE_API_KEY", "GEMINI_API_KEY"),
        model_env_var="AGENTRULES_GEMINI_LIVE_MODEL",
        default_model="gemini-3.5-flash",
        runner=lambda api_key, model: _run_gemini(api_key, model),
    ),
    LiveProviderCase(
        provider="deepseek",
        enable_flag="AGENTRULES_RUN_DEEPSEEK_LIVE",
        key_env_vars=("DEEPSEEK_API_KEY",),
        model_env_var="AGENTRULES_DEEPSEEK_LIVE_MODEL",
        default_model="deepseek-v4-flash",
        runner=lambda api_key, model: _run_deepseek(api_key, model),
    ),
    LiveProviderCase(
        provider="xai",
        enable_flag="AGENTRULES_RUN_XAI_LIVE",
        key_env_vars=("XAI_API_KEY",),
        model_env_var="AGENTRULES_XAI_LIVE_MODEL",
        default_model="grok-4.5",
        runner=lambda api_key, model: _run_xai(api_key, model),
    ),
)


@pytest.mark.live
@pytest.mark.parametrize("case", LIVE_PROVIDER_CASES, ids=lambda case: case.provider)
def test_direct_provider_model_live_smoke(case: LiveProviderCase) -> None:
    if os.getenv(case.enable_flag) != "1":
        pytest.skip(f"Set {case.enable_flag}=1 to enable the {case.provider} live smoke.")

    api_key = next((os.getenv(name) for name in case.key_env_vars if os.getenv(name)), None)
    if api_key is None:
        pytest.skip(f"Missing {' or '.join(case.key_env_vars)} for the {case.provider} live smoke.")

    model = os.getenv(case.model_env_var, case.default_model)
    try:
        evidence = case.runner(api_key, model)
    except Exception as exc:
        status_code = _status_code(exc)
        if status_code in {403, 404, 429}:
            pytest.skip(f"{case.provider} model is unavailable to this account, region, or quota (HTTP {status_code}).")
        raise

    assert evidence


def _run_openai(api_key: str, model: str) -> object:
    with OpenAI(api_key=api_key) as client:
        response = client.responses.create(
            model=model,
            input=LIVE_PROMPT,
            max_output_tokens=MAX_LIVE_OUTPUT_TOKENS,
        )
    return response.id


def _run_anthropic(api_key: str, model: str) -> object:
    with Anthropic(api_key=api_key) as client:
        response = client.messages.create(
            model=model,
            max_tokens=MAX_LIVE_OUTPUT_TOKENS,
            messages=[{"role": "user", "content": LIVE_PROMPT}],
        )
    return response.id


def _run_gemini(api_key: str, model: str) -> object:
    client: Any = genai.Client(api_key=api_key)
    with client:
        response = client.models.generate_content(
            model=model,
            contents=LIVE_PROMPT,
            config=genai_types.GenerateContentConfig(
                max_output_tokens=MAX_LIVE_OUTPUT_TOKENS,
            ),
        )
    return bool(response.candidates)


def _run_deepseek(api_key: str, model: str) -> object:
    with OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL) as client:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": LIVE_PROMPT}],
            max_tokens=MAX_LIVE_OUTPUT_TOKENS,
            extra_body={"thinking": {"type": "disabled"}},
        )
    return response.id


def _run_xai(api_key: str, model: str) -> object:
    with OpenAI(api_key=api_key, base_url=XAI_BASE_URL) as client:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": LIVE_PROMPT}],
            max_tokens=MAX_LIVE_OUTPUT_TOKENS,
            reasoning_effort="low",
        )
    return response.id


def _status_code(exc: Exception) -> int | None:
    for attribute in ("status_code", "code"):
        value: Any = getattr(exc, attribute, None)
        if isinstance(value, int):
            return value
    return None
