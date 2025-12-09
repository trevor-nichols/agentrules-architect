"""
Token-aware packing helpers for Phase 3 file batches.

Goals:
- Respect provider/model input limits using existing estimators.
- Greedily pack file blocks until the next block would exceed the effective limit.
- Summarize single-file oversize cases so nothing is skipped.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from agentrules.config import agents as agent_config
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


def _estimate_prompt_tokens(
    *,
    provider: ModelProvider,
    model_name: str,
    estimator_family: str | None,
    assigned_files: list[str],
    file_blocks: Iterable[tuple[str, str]],
    tree: str | list[str] | None,
) -> int:
    """Build a lightweight Phase3-shaped prompt and estimate its tokens."""
    tree_text = "\n".join(tree) if isinstance(tree, list) else (tree or "")
    files_list = "\n".join(f"- {f}" for f in assigned_files)
    blocks = [
        f'<file path="{path}">\n{content}\n</file>'
        for path, content in file_blocks
    ]
    body = "\n\n".join(blocks)
    prompt = (
        f"TREE:\n{tree_text}\n\n"
        f"ASSIGNED:\n{files_list}\n\n"
        f"FILES:\n{body}"
    )

    payload: dict[str, object]
    api: str | None = None

    if provider == ModelProvider.ANTHROPIC:
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
        }
    elif provider == ModelProvider.GEMINI:
        payload = {"contents": prompt}
    elif provider == ModelProvider.OPENAI:
        payload = {"input": prompt}
        api = "responses"
    else:
        payload = {"input": prompt}

    result = estimate_tokens(
        provider=provider,
        model_name=model_name,
        payload=payload,
        estimator_family=estimator_family,
        api=api,
    )
    if result.estimated is not None:
        return result.estimated

    # Defensive fallback to avoid under-counting
    fallback = estimate_tokens(
        provider=provider,
        model_name=model_name,
        payload={"input": prompt},
        estimator_family="heuristic",
    )
    if fallback.estimated is not None and fallback.estimated > 0:
        return fallback.estimated

    conservative = max(len(prompt) // 3, 1)
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
    effective_limit = effective_limit or limit

    # If we have no limit, return a single batch as-is.
    if not effective_limit:
        return [
            PackedBatch(
                assigned_files=list(files_with_content.keys()),
                file_contents=dict(files_with_content),
            )
        ]

    provider = model_config.provider
    model_name = model_config.model_name
    estimator_family = getattr(model_config, "estimator_family", None)

    items: list[tuple[str, str]] = list(files_with_content.items())
    batches: list[PackedBatch] = []
    current_files: list[str] = []
    current_contents: dict[str, str] = {}

    for path, content in items:
        tentative_files = current_files + [path]
        tentative_blocks: list[tuple[str, str]] = list(current_contents.items()) + [(path, content)]

        tokens = _estimate_prompt_tokens(
            provider=provider,
            model_name=model_name,
            estimator_family=estimator_family,
            assigned_files=tentative_files,
            file_blocks=tentative_blocks,
            tree=tree,
        )

        if tokens <= effective_limit:
            current_files.append(path)
            current_contents[path] = content
            continue

        # If nothing is in the current batch, the single file is too large—summarize it.
        if not current_files:
            summarized = summarizer(content)
            current_files.append(path)
            current_contents[path] = summarized
            batches.append(
                PackedBatch(
                    assigned_files=list(current_files),
                    file_contents=dict(current_contents),
                )
            )
            current_files = []
            current_contents = {}
            continue

        # Flush current batch and start a new one with the pending file.
        batches.append(
            PackedBatch(
                assigned_files=list(current_files),
                file_contents=dict(current_contents),
            )
        )
        current_files = [path]
        current_contents = {path: content}

    if current_files:
        batches.append(
            PackedBatch(
                assigned_files=list(current_files),
                file_contents=dict(current_contents),
            )
        )

    return batches


def resolve_model_config(model_name: str) -> ModelConfig:
    """Resolve a ModelConfig from configured presets."""
    presets = getattr(agent_config, "MODEL_PRESETS", {})
    for _, preset in presets.items():
        cfg = preset.get("config")
        if cfg and getattr(cfg, "model_name", "").lower() == model_name.lower():
            return cfg
    raise ValueError(f"No model config found for {model_name}")
