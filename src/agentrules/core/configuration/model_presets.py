"""Helpers for mapping user configuration to model presets."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Literal, cast

from agentrules.config import agents as agent_settings
from agentrules.config.agents import PresetDefinition
from agentrules.core.agents.base import ModelProvider, ReasoningMode
from agentrules.core.types.models import ModelConfig

from . import get_config_manager

PHASE_TITLES: dict[str, str] = {
    "phase1": "Phase 1 – Initial Discovery",
    "phase2": "Phase 2 – Methodical Planning",
    "phase3": "Phase 3 – Deep Analysis",
    "phase4": "Phase 4 – Synthesis",
    "phase5": "Phase 5 – Consolidation",
    "final": "Final Analysis",
    "researcher": "Researcher Agent",
}

PHASE_SEQUENCE: list[str] = list(agent_settings.MODEL_PRESET_DEFAULTS.keys())
CODEX_RUNTIME_PRESET_PREFIX = "codex-runtime:"
CODEX_RUNTIME_PRESET_EFFORT_SEPARATOR = "|effort="

CodexRuntimeReasoningEffort = Literal["none", "minimal", "low", "medium", "high", "xhigh"] | None
_CODEX_RUNTIME_REASONING_EFFORT_ORDER: tuple[str, ...] = (
    "none",
    "minimal",
    "low",
    "medium",
    "high",
    "xhigh",
)
_CODEX_RUNTIME_REASONING_EFFORT_SET = set(_CODEX_RUNTIME_REASONING_EFFORT_ORDER)


@dataclass(frozen=True)
class PresetInfo:
    key: str
    label: str
    description: str
    provider: ModelProvider

    @property
    def provider_slug(self) -> str:
        return self.provider.value

    @property
    def provider_display(self) -> str:
        return _provider_display_name(self.provider)


@dataclass(frozen=True)
class CodexRuntimeModelCatalogEntry:
    model: str
    display_name: str | None = None
    description: str | None = None
    default_reasoning_effort: CodexRuntimeReasoningEffort = None
    supported_reasoning_efforts: tuple[CodexRuntimeModelReasoningOption, ...] = ()


@dataclass(frozen=True)
class CodexRuntimeModelReasoningOption:
    reasoning_effort: CodexRuntimeReasoningEffort
    description: str | None = None


@dataclass(frozen=True)
class CodexRuntimePresetSelection:
    model_name: str
    reasoning_effort: CodexRuntimeReasoningEffort = None


def _build_preset_infos(
    presets: Iterable[tuple[str, PresetDefinition]],
) -> dict[str, PresetInfo]:
    info_map: dict[str, PresetInfo] = {}
    for key, meta in presets:
        info_map[key] = PresetInfo(
            key=key,
            label=meta["label"],
            description=meta["description"],
            provider=meta["provider"],
        )
    return info_map


PRESET_INFOS: dict[str, PresetInfo] = _build_preset_infos(agent_settings.MODEL_PRESETS.items())

CONFIG_MANAGER = get_config_manager()


def get_phase_title(phase: str) -> str:
    return PHASE_TITLES.get(phase, phase.title())


def get_default_preset_key(phase: str) -> str | None:
    return agent_settings.MODEL_PRESET_DEFAULTS.get(phase)


def get_preset_info(key: str) -> PresetInfo | None:
    preset = PRESET_INFOS.get(key)
    if preset is not None:
        return preset

    runtime_selection = parse_codex_runtime_preset_selection(key)
    if runtime_selection is None:
        return None

    return _build_runtime_codex_preset_info(
        runtime_selection.model_name,
        reasoning_effort=runtime_selection.reasoning_effort,
    )


def get_active_preset_key(phase: str, overrides: Mapping[str, str] | None = None) -> str | None:
    overrides = overrides or CONFIG_MANAGER.get_model_overrides()
    override = overrides.get(phase)
    if override is not None:
        return override
    return get_default_preset_key(phase)


def get_model_config_for_phase(
    phase: str,
    overrides: Mapping[str, str] | None = None,
):
    preset_key = get_active_preset_key(phase, overrides)
    if preset_key is None:
        return None

    preset = agent_settings.MODEL_PRESETS.get(preset_key)
    if preset is not None:
        return preset["config"]

    runtime_selection = parse_codex_runtime_preset_selection(preset_key)
    if runtime_selection is not None:
        return _build_runtime_codex_model_config(
            runtime_selection.model_name,
            reasoning_effort=runtime_selection.reasoning_effort,
        )

    return None


def get_available_presets_for_phase(
    phase: str,
    provider_availability: Mapping[str, bool] | None = None,
) -> list[PresetInfo]:
    if provider_availability is None:
        provider_availability = CONFIG_MANAGER.get_provider_availability()
    default_key = get_default_preset_key(phase)
    available: list[PresetInfo] = []

    for key, info in PRESET_INFOS.items():
        if key != default_key and not provider_availability.get(info.provider_slug, False):
            continue
        available.append(info)

    # Ensure default preset is present even if no keys are configured yet
    if default_key and not any(p.key == default_key for p in available):
        info = get_preset_info(default_key)
        if info:
            available.insert(0, info)

    return available


def get_active_presets(overrides: Mapping[str, str] | None = None) -> dict[str, str]:
    overrides = overrides or CONFIG_MANAGER.get_model_overrides()
    active: dict[str, str] = {}
    for phase in PHASE_SEQUENCE:
        override = overrides.get(phase)
        if override is not None:
            active[phase] = override
            continue

        default_key = get_default_preset_key(phase)
        if default_key is not None:
            active[phase] = default_key
    return active


def apply_user_overrides(overrides: Mapping[str, str] | None = None) -> dict[str, str]:
    """
    Apply user-selected model presets to the global MODEL_CONFIG.
    Returns the applied preset mapping for further inspection.
    """
    overrides = overrides or CONFIG_MANAGER.get_model_overrides()
    applied: dict[str, str] = {}

    # reset to defaults first
    for phase, preset_key in agent_settings.MODEL_PRESET_DEFAULTS.items():
        default_preset: PresetDefinition = agent_settings.MODEL_PRESETS[preset_key]
        agent_settings.MODEL_CONFIG[phase] = default_preset["config"]
        applied[phase] = preset_key

    # apply overrides when valid
    for phase, preset_key in overrides.items():
        if phase not in agent_settings.MODEL_PRESET_DEFAULTS:
            continue
        override_preset: PresetDefinition | None = agent_settings.MODEL_PRESETS.get(preset_key)
        if override_preset is not None:
            agent_settings.MODEL_CONFIG[phase] = override_preset["config"]
            applied[phase] = preset_key
            continue

        runtime_selection = parse_codex_runtime_preset_selection(preset_key)
        if runtime_selection is None:
            continue
        agent_settings.MODEL_CONFIG[phase] = _build_runtime_codex_model_config(
            runtime_selection.model_name,
            reasoning_effort=runtime_selection.reasoning_effort,
        )
        applied[phase] = preset_key

    return applied


def make_codex_runtime_preset_key(
    model_name: str,
    reasoning_effort: CodexRuntimeReasoningEffort = None,
) -> str:
    normalized_model_name = model_name.strip()
    base = f"{CODEX_RUNTIME_PRESET_PREFIX}{normalized_model_name}"
    normalized_effort = _normalize_codex_reasoning_effort(reasoning_effort)
    if normalized_effort is None:
        return base
    return f"{base}{CODEX_RUNTIME_PRESET_EFFORT_SEPARATOR}{normalized_effort}"


def parse_codex_runtime_preset_selection(key: str | None) -> CodexRuntimePresetSelection | None:
    if not isinstance(key, str):
        return None
    if not key.startswith(CODEX_RUNTIME_PRESET_PREFIX):
        return None

    raw_value = key.removeprefix(CODEX_RUNTIME_PRESET_PREFIX).strip()
    if not raw_value:
        return None

    raw_model, separator, raw_effort = raw_value.partition(CODEX_RUNTIME_PRESET_EFFORT_SEPARATOR)
    model_name = raw_model.strip()
    if not model_name:
        return None

    effort = _normalize_codex_reasoning_effort(raw_effort if separator else None)
    return CodexRuntimePresetSelection(model_name=model_name, reasoning_effort=effort)


def parse_codex_runtime_preset_key(key: str | None) -> str | None:
    selection = parse_codex_runtime_preset_selection(key)
    if selection is None:
        return None
    return selection.model_name


def parse_codex_runtime_reasoning_for_preset_key(key: str | None) -> CodexRuntimeReasoningEffort:
    selection = parse_codex_runtime_preset_selection(key)
    if selection is None:
        return None
    return selection.reasoning_effort


def resolve_codex_model_name_for_preset_key(key: str | None) -> str | None:
    runtime_selection = parse_codex_runtime_preset_selection(key)
    if runtime_selection is not None:
        return runtime_selection.model_name
    if not isinstance(key, str):
        return None
    preset = agent_settings.MODEL_PRESETS.get(key)
    if preset is None or preset["provider"] != ModelProvider.CODEX:
        return None
    return preset["config"].model_name


def resolve_codex_reasoning_effort_for_preset_key(key: str | None) -> CodexRuntimeReasoningEffort:
    runtime_selection = parse_codex_runtime_preset_selection(key)
    if runtime_selection is not None:
        return runtime_selection.reasoning_effort
    if not isinstance(key, str):
        return None
    preset = agent_settings.MODEL_PRESETS.get(key)
    if preset is None or preset["provider"] != ModelProvider.CODEX:
        return None
    return _reasoning_effort_from_mode(preset["config"].reasoning)


def build_codex_runtime_preset_infos(
    catalog_entries: Iterable[CodexRuntimeModelCatalogEntry],
) -> list[PresetInfo]:
    runtime_infos: list[PresetInfo] = []
    seen_keys: set[str] = set()

    for entry in catalog_entries:
        model_name = entry.model.strip()
        if not model_name:
            continue
        for reasoning_option in _resolve_runtime_reasoning_options(entry):
            key = make_codex_runtime_preset_key(
                model_name,
                reasoning_effort=reasoning_option.reasoning_effort,
            )
            if key in seen_keys:
                continue
            runtime_infos.append(
                _build_runtime_codex_preset_info(
                    model_name,
                    display_name=entry.display_name,
                    description=entry.description,
                    reasoning_effort=reasoning_option.reasoning_effort,
                    reasoning_description=reasoning_option.description,
                )
            )
            seen_keys.add(key)

    return runtime_infos


def _build_runtime_codex_preset_info(
    model_name: str,
    *,
    display_name: str | None = None,
    description: str | None = None,
    reasoning_effort: CodexRuntimeReasoningEffort = None,
    reasoning_description: str | None = None,
) -> PresetInfo:
    display = (display_name or "").strip() or model_name
    details = (description or "").strip() or "Discovered from the live Codex app-server model catalog."
    effort_label = _format_reasoning_variant_label(reasoning_effort)
    if effort_label is not None:
        label = f"Codex: {display} ({effort_label})"
    else:
        label = f"Codex: {display}"

    if reasoning_effort is not None:
        reasoning_details = (reasoning_description or "").strip()
        if not reasoning_details:
            reasoning_details = f"Reasoning effort: {_format_reasoning_description(reasoning_effort)}."
        details = f"{details} {reasoning_details}".strip()

    return PresetInfo(
        key=make_codex_runtime_preset_key(model_name, reasoning_effort=reasoning_effort),
        label=label,
        description=details,
        provider=ModelProvider.CODEX,
    )


def _build_runtime_codex_model_config(
    model_name: str,
    *,
    reasoning_effort: CodexRuntimeReasoningEffort = None,
) -> ModelConfig:
    template = _resolve_codex_runtime_template()
    reasoning_mode = _reasoning_mode_from_effort(reasoning_effort, fallback=template.reasoning)
    return template._replace(model_name=model_name, reasoning=reasoning_mode)


def _resolve_codex_runtime_template() -> ModelConfig:
    for preset in agent_settings.MODEL_PRESETS.values():
        if preset["provider"] == ModelProvider.CODEX:
            return preset["config"]
    raise ValueError("No Codex model preset is defined in agentrules.config.agents.MODEL_PRESETS.")


def _resolve_runtime_reasoning_options(
    entry: CodexRuntimeModelCatalogEntry,
) -> tuple[CodexRuntimeModelReasoningOption, ...]:
    descriptions: dict[str, str | None] = {}
    for option in entry.supported_reasoning_efforts:
        normalized_effort = _normalize_codex_reasoning_effort(option.reasoning_effort)
        if normalized_effort is None:
            continue
        if normalized_effort not in descriptions:
            descriptions[normalized_effort] = option.description

    default_effort = _normalize_codex_reasoning_effort(entry.default_reasoning_effort)
    if default_effort is not None and default_effort not in descriptions:
        descriptions[default_effort] = None

    if not descriptions:
        return (CodexRuntimeModelReasoningOption(reasoning_effort=default_effort),)

    ordered_efforts = [effort for effort in _CODEX_RUNTIME_REASONING_EFFORT_ORDER if effort in descriptions]
    return tuple(
        CodexRuntimeModelReasoningOption(
            reasoning_effort=cast(CodexRuntimeReasoningEffort, effort),
            description=descriptions.get(effort),
        )
        for effort in ordered_efforts
    )


def _normalize_codex_reasoning_effort(value: object) -> CodexRuntimeReasoningEffort:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if normalized in _CODEX_RUNTIME_REASONING_EFFORT_SET:
        return normalized
    return None


def _reasoning_mode_from_effort(
    effort: CodexRuntimeReasoningEffort,
    *,
    fallback: ReasoningMode,
) -> ReasoningMode:
    mapping: dict[str, ReasoningMode] = {
        "none": ReasoningMode.DISABLED,
        "minimal": ReasoningMode.MINIMAL,
        "low": ReasoningMode.LOW,
        "medium": ReasoningMode.MEDIUM,
        "high": ReasoningMode.HIGH,
        "xhigh": ReasoningMode.XHIGH,
    }
    normalized_effort = _normalize_codex_reasoning_effort(effort)
    if normalized_effort is None:
        return fallback
    return mapping.get(normalized_effort, fallback)


def _reasoning_effort_from_mode(reasoning: ReasoningMode) -> CodexRuntimeReasoningEffort:
    if reasoning == ReasoningMode.DISABLED:
        return "none"
    if reasoning == ReasoningMode.MINIMAL:
        return "minimal"
    if reasoning == ReasoningMode.LOW:
        return "low"
    if reasoning == ReasoningMode.MEDIUM:
        return "medium"
    if reasoning == ReasoningMode.HIGH:
        return "high"
    if reasoning == ReasoningMode.XHIGH:
        return "xhigh"
    if reasoning in {ReasoningMode.ENABLED, ReasoningMode.DYNAMIC}:
        return "medium"
    return None


def _format_reasoning_variant_label(effort: CodexRuntimeReasoningEffort) -> str | None:
    if effort is None:
        return None
    if effort == "none":
        return "no reasoning"
    if effort == "xhigh":
        return "very high"
    return effort


def _format_reasoning_description(effort: CodexRuntimeReasoningEffort) -> str:
    if effort == "none":
        return "none"
    if effort == "xhigh":
        return "very high"
    if effort is None:
        return "default"
    return effort


def _provider_display_name(provider: ModelProvider) -> str:
    mapping = {
        ModelProvider.OPENAI: "OpenAI",
        ModelProvider.CODEX: "Codex App Server",
        ModelProvider.ANTHROPIC: "Anthropic",
        ModelProvider.GEMINI: "Google Gemini",
        ModelProvider.DEEPSEEK: "DeepSeek",
        ModelProvider.XAI: "xAI Grok",
    }
    return mapping.get(provider, provider.value.title())
