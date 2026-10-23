"""
Token-aware packing helpers for Phase 3 file batches.

Goals:
- Respect provider/model input limits using existing estimators.
- Greedily pack file blocks until the next block would exceed the effective limit.
- Summarize single-file oversize cases so nothing is skipped.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass

from agentrules.config import agents as agent_config
from agentrules.config.prompts.phase_3_prompts import format_phase3_prompt
from agentrules.core.agents.base import ModelProvider, ReasoningMode
from agentrules.core.types.models import ModelConfig
from agentrules.core.utils.token_estimator import compute_effective_limits, estimate_tokens

SummaryFn = Callable[[str], str]
logger = logging.getLogger("project_extractor")

DEFAULT_UNKNOWN_MAX_INPUT = 128_000


@dataclass
class PackedBatch:
    assigned_files: list[str]
    file_contents: dict[str, str]


def _default_summary(text: str, max_chars: int = 2000) -> str:
    """Cheap local summary that truncates while preserving intent."""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return f"{text[: max_chars]}...\n[truncated summary]"


def _estimate_text_tokens(
    *,
    provider: ModelProvider,
    model_name: str,
    estimator_family: str | None,
    text: str,
) -> int:
    payload: dict[str, object]
    api: str | None = None

    if provider == ModelProvider.ANTHROPIC:
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": text}],
        }
    elif provider == ModelProvider.GEMINI:
        payload = {"contents": text}
    elif provider == ModelProvider.OPENAI:
        payload = {"input": text}
        api = "responses"
    else:
        payload = {"input": text}

    result = estimate_tokens(
        provider=provider,
        model_name=model_name,
        payload=payload,
        estimator_family=estimator_family,
        api=api,
    )
    if result.estimated is not None:
        if result.source == "heuristic":
            return max(result.estimated, len(text.encode("utf-8")))
        return result.estimated

    conservative = max(len(text.encode("utf-8")), 1)
    logger.warning(
        "Token estimate unavailable; using conservative fallback",
        extra={"provider": provider, "model": model_name, "estimate": conservative},
    )
    return conservative


def pack_files_for_phase3(
    *,
    files_with_content: dict[str, str],
    tree: list[str] | str | None,
    model_config: ModelConfig | None,
    summarizer: SummaryFn | None = None,
) -> list[PackedBatch]:
    """
    Greedily pack file contents into batches that respect the model's effective limit.

    - Uses estimate_tokens to approximate the final prompt size.
    - Starts a new batch when the next file would exceed the effective limit.
    - If a single file is bigger than the effective limit, it is summarized locally first.
    """
    if model_config is None:
        model_config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="unknown",
            max_input_tokens=DEFAULT_UNKNOWN_MAX_INPUT,
            estimator_family="heuristic",
            reasoning=ReasoningMode.MEDIUM,
        )
    summarizer = summarizer or _default_summary
    limit, _margin, effective_limit = compute_effective_limits(
        getattr(model_config, "max_input_tokens", None),
        getattr(model_config, "safety_margin_tokens", None),
    )

    # If we have no limit, return a single batch as-is.
    if limit is None:
        return [
            PackedBatch(
                assigned_files=list(files_with_content.keys()),
                file_contents=dict(files_with_content),
            )
        ]
    assert effective_limit is not None

    provider = model_config.provider
    model_name = model_config.model_name
    estimator_family = getattr(model_config, "estimator_family", None)

    tree_text = "\n".join(tree) if isinstance(tree, list) else (tree or "")
    skeleton = format_phase3_prompt(
        {"tree_structure": tree_text, "assigned_files": [], "file_contents": {}}
    )
    skeleton_tokens = _estimate_text_tokens(
        provider=provider,
        model_name=model_name,
        estimator_family=estimator_family,
        text=skeleton,
    )
    if skeleton_tokens >= effective_limit:
        raise ValueError(f"Phase 3 prompt skeleton exceeds the input budget for {model_name}")

    content_token_cache: dict[tuple[str, str], int] = {}

    def content_tokens(content: str) -> int:
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        key = (model_name, content_hash)
        if key not in content_token_cache:
            escaped_content = json.dumps(content, ensure_ascii=False)
            content_token_cache[key] = _estimate_text_tokens(
                provider=provider,
                model_name=model_name,
                estimator_family=estimator_family,
                text=escaped_content,
            )
        return content_token_cache[key]

    def file_tokens(path: str, content: str) -> int:
        envelope = json.dumps({"path": path, "content": ""}, ensure_ascii=False)
        envelope += f"\n\n- {path}\n"
        overhead = _estimate_text_tokens(
            provider=provider,
            model_name=model_name,
            estimator_family=estimator_family,
            text=envelope,
        )
        return content_tokens(content) + overhead + 16

    batches: list[PackedBatch] = []
    current_files: list[str] = []
    current_contents: dict[str, str] = {}
    running_tokens = skeleton_tokens

    for path, original_content in files_with_content.items():
        content = original_content
        estimated_tokens = file_tokens(path, content)
        if skeleton_tokens + estimated_tokens > effective_limit:
            content = summarizer(content)
            estimated_tokens = file_tokens(path, content)
            while skeleton_tokens + estimated_tokens > effective_limit and len(content) > 1:
                content = content[: max(1, len(content) // 2)]
                estimated_tokens = file_tokens(path, content)
            if skeleton_tokens + estimated_tokens > effective_limit:
                raise ValueError(f"File {path} cannot fit the input budget for {model_name}")

        if running_tokens + estimated_tokens > effective_limit:
            batches.append(PackedBatch(assigned_files=current_files, file_contents=current_contents))
            current_files = []
            current_contents = {}
            running_tokens = skeleton_tokens

        current_files.append(path)
        current_contents[path] = content
        running_tokens += estimated_tokens

    if current_files:
        batches.append(PackedBatch(assigned_files=current_files, file_contents=current_contents))

    return batches


def resolve_model_config(model_name: str) -> ModelConfig:
    """Resolve a ModelConfig from configured presets."""
    presets = getattr(agent_config, "MODEL_PRESETS", {})
    for _, preset in presets.items():
        cfg = preset.get("config")
        if cfg and getattr(cfg, "model_name", "").lower() == model_name.lower():
            return cfg
    raise ValueError(f"No model config found for {model_name}")
