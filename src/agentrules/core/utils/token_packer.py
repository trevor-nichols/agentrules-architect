"""
Token-aware packing helpers for Phase 3 file batches.

Goals:
- Respect provider/model input limits using local estimates.
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


def pack_files_for_phase3(
    *,
    files_with_content: dict[str, str],
    tree: list[str] | str | None,
    model_config: ModelConfig | None,
    summarizer: SummaryFn | None = None,
) -> list[PackedBatch]:
    """
    Greedily pack file contents into batches that respect the model's effective limit.

    - Uses a local tokenizer to approximate the final prompt size.
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
    use_byte_counts = model_config.estimator_family == "heuristic"

    def count_text(text: str) -> int:
        nonlocal use_byte_counts
        if not use_byte_counts:
            result = estimate_tokens(
                provider=provider,
                model_name=model_name,
                payload={"input": text},
                estimator_family="tiktoken",
            )
            if result.estimated is not None:
                return result.estimated

            use_byte_counts = True
            logger.warning(
                "Local tokenizer unavailable for Phase 3 packing; using UTF-8 byte counts",
                extra={"provider": provider, "model": model_name},
            )
        return max(1, len(text.encode("utf-8")))

    tree_text = "\n".join(tree) if isinstance(tree, list) else (tree or "")
    skeleton = format_phase3_prompt(
        {"tree_structure": tree_text, "assigned_files": [], "file_contents": {}}
    )
    skeleton_tokens = count_text(skeleton)
    if skeleton_tokens >= effective_limit:
        raise ValueError(f"Phase 3 prompt skeleton exceeds the input budget for {model_name}")

    content_token_cache: dict[tuple[str, str], int] = {}
    summary_cache: dict[tuple[str, str], str] = {}

    def estimate_content(content: str) -> tuple[tuple[str, str], int]:
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        key = (model_name, content_hash)
        if key not in content_token_cache:
            escaped_content = json.dumps(content, ensure_ascii=False)
            content_token_cache[key] = count_text(escaped_content)
        return key, content_token_cache[key]

    batches: list[PackedBatch] = []
    current_files: list[str] = []
    current_contents: dict[str, str] = {}
    running_tokens = skeleton_tokens

    for path, original_content in files_with_content.items():
        envelope = json.dumps({"path": path, "content": ""}, ensure_ascii=False)
        envelope += f"\n\n- {path}\n"
        overhead = count_text(envelope) + 16
        file_budget = effective_limit - skeleton_tokens - overhead
        content = original_content
        original_key, tokens = estimate_content(original_content)
        if tokens > file_budget:
            if original_key not in summary_cache:
                summary_cache[original_key] = summarizer(original_content)
            content = summary_cache[original_key]
            _, tokens = estimate_content(content)
            while tokens > file_budget and len(content) > 1:
                content = content[: max(1, len(content) // 2)]
                _, tokens = estimate_content(content)
            if tokens > file_budget:
                raise ValueError(f"File {path} cannot fit the input budget for {model_name}")

        estimated_tokens = overhead + tokens
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
