"""Helpers for mapping user configuration to model presets."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Literal, cast

from agentrules.config import agents as agent_settings
from agentrules.config.agents import PresetDefinition
from agentrules.core.agents.base import ModelProvider, ReasoningMode
from agentrules.core.types.models import ModelConfig

from . import get_config_manager

logger = logging.getLogger(__name__)

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
CODEX_RUNTIME_DEFAULT_KEY = f"{CODEX_RUNTIME_PRESET_PREFIX}__default__"
CODEX_RUNTIME_DEFAULT_MODEL_NAME = "__codex_runtime_default__"
LEGACY_CODEX_RUNTIME_MODEL_ALIASES: dict[str, str] = {
    "gpt-5.4-2026-03-05": "gpt-5.4",
}
_LEGACY_CODEX_RUNTIME_MODEL_NAMES_BY_CANONICAL: dict[str, tuple[str, ...]] = {}
for _legacy_model_name, _canonical_model_name in LEGACY_CODEX_RUNTIME_MODEL_ALIASES.items():
    _LEGACY_CODEX_RUNTIME_MODEL_NAMES_BY_CANONICAL.setdefault(_canonical_model_name, ())
    _LEGACY_CODEX_RUNTIME_MODEL_NAMES_BY_CANONICAL[_canonical_model_name] = (
        *_LEGACY_CODEX_RUNTIME_MODEL_NAMES_BY_CANONICAL[_canonical_model_name],
        _legacy_model_name,
    )

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
class PresetDeprecationInfo:
    replacement_key: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class CodexRuntimeModelCatalogEntry:
    model: str
    display_name: str | None = None
    description: str | None = None
    is_default: bool = False
    default_reasoning_effort: CodexRuntimeReasoningEffort = None
    supported_reasoning_efforts: tuple[CodexRuntimeModelReasoningOption, ...] = ()


@dataclass(frozen=True)
class CodexRuntimeModelReasoningOption:
    reasoning_effort: CodexRuntimeReasoningEffort
    description: str | None = None


@dataclass(frozen=True)
class _ResolvedCodexRuntimeReasoningOption:
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
DEPRECATED_PRESETS: dict[str, PresetDeprecationInfo] = {
    "gemini-3-pro-preview": PresetDeprecationInfo(
        replacement_key="gemini-3.1-pro-preview",
        reason="Google retired this preview model.",
    ),
    "gemini-3.1-flash-lite-preview": PresetDeprecationInfo(
        replacement_key="gemini-3.1-flash-lite",
        reason="Google retired this preview model.",
    ),
}

CONFIG_MANAGER = get_config_manager()
_WARNED_DEPRECATED_RUNTIME_PRESET_KEYS: set[str] = set()


def _resolve_override_mapping(overrides: Mapping[str, str] | None) -> Mapping[str, str]:
    if overrides is None:
        return CONFIG_MANAGER.get_model_overrides()
    return overrides


def get_phase_title(phase: str) -> str:
    return PHASE_TITLES.get(phase, phase.title())


def get_default_preset_key(phase: str) -> str | None:
    return agent_settings.MODEL_PRESET_DEFAULTS.get(phase)


def get_preset_info(key: str) -> PresetInfo | None:
    preset = PRESET_INFOS.get(key)
    if preset is not None:
        return preset

    if is_codex_runtime_default_preset_key(key):
        return _build_runtime_codex_default_preset_info()

    runtime_selection = parse_codex_runtime_preset_selection(key)
    if runtime_selection is None:
        return None

    return _build_runtime_codex_preset_info(
        runtime_selection.model_name,
        reasoning_effort=runtime_selection.reasoning_effort,
    )


def get_preset_deprecation_info(key: str | None) -> PresetDeprecationInfo | None:
    if not isinstance(key, str):
        return None
    return DEPRECATED_PRESETS.get(key)


def resolve_runtime_preset_key(preset_key: str | None, *, warn: bool = False) -> str | None:
    if preset_key is None:
        return None

    deprecation = get_preset_deprecation_info(preset_key)
    replacement_key = deprecation.replacement_key if deprecation is not None else None
    if not replacement_key or replacement_key not in agent_settings.MODEL_PRESETS:
        return preset_key

    if warn and preset_key not in _WARNED_DEPRECATED_RUNTIME_PRESET_KEYS:
        reason_suffix = f" {deprecation.reason}" if deprecation and deprecation.reason else ""
        logger.warning(
            "Preset key '%s' is deprecated and will resolve to '%s' for runtime requests.%s",
            preset_key,
            replacement_key,
            reason_suffix,
        )
        _WARNED_DEPRECATED_RUNTIME_PRESET_KEYS.add(preset_key)

    return replacement_key


def get_configured_preset_key(phase: str, overrides: Mapping[str, str] | None = None) -> str | None:
    overrides = _resolve_override_mapping(overrides)
    override = overrides.get(phase)
    if override is not None:
        return override
    return get_default_preset_key(phase)


def get_active_preset_key(phase: str, overrides: Mapping[str, str] | None = None) -> str | None:
    configured_key = get_configured_preset_key(phase, overrides)
    if configured_key is None:
        return None
    return resolve_runtime_preset_key(configured_key)


def get_model_config_for_phase(
    phase: str,
    overrides: Mapping[str, str] | None = None,
):
    preset_key = get_active_preset_key(phase, overrides)
    if preset_key is None:
        return None

    return get_model_config_for_preset_key(preset_key)


def get_model_config_for_preset_key(preset_key: str | None):
    runtime_preset_key = resolve_runtime_preset_key(preset_key)
    if runtime_preset_key is None:
        return None

    preset = agent_settings.MODEL_PRESETS.get(runtime_preset_key)
    if preset is not None:
        return preset["config"]

    if is_codex_runtime_default_preset_key(runtime_preset_key):
        return _build_runtime_codex_default_model_config()

    runtime_selection = parse_codex_runtime_preset_selection(runtime_preset_key)
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
    overrides = _resolve_override_mapping(overrides)
    active: dict[str, str] = {}
    for phase in PHASE_SEQUENCE:
        override = overrides.get(phase)
        if override is not None:
            resolved_override = resolve_runtime_preset_key(override)
            if resolved_override is not None:
                active[phase] = resolved_override
            continue

        default_key = get_default_preset_key(phase)
        if default_key is not None:
            active[phase] = default_key
    return active


def get_configured_presets(overrides: Mapping[str, str] | None = None) -> dict[str, str]:
    overrides = _resolve_override_mapping(overrides)
    configured: dict[str, str] = {}
    for phase in PHASE_SEQUENCE:
        override = overrides.get(phase)
        if override is not None:
            configured[phase] = override
            continue

        default_key = get_default_preset_key(phase)
        if default_key is not None:
            configured[phase] = default_key
    return configured


def apply_user_overrides(
    overrides: Mapping[str, str] | None = None,
    *,
    warn_deprecated: bool = False,
) -> dict[str, str]:
    """
    Apply user-selected model presets to the global MODEL_CONFIG.
    Returns the applied preset mapping for further inspection.
    """
    overrides = _resolve_override_mapping(overrides)
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

        runtime_preset_key = resolve_runtime_preset_key(preset_key, warn=warn_deprecated)
        if runtime_preset_key is None:
            continue

        override_preset: PresetDefinition | None = agent_settings.MODEL_PRESETS.get(runtime_preset_key)
        if override_preset is not None:
            agent_settings.MODEL_CONFIG[phase] = override_preset["config"]
            applied[phase] = runtime_preset_key
            continue

        if is_codex_runtime_default_preset_key(runtime_preset_key):
            agent_settings.MODEL_CONFIG[phase] = _build_runtime_codex_default_model_config()
            applied[phase] = runtime_preset_key
            continue

        runtime_selection = parse_codex_runtime_preset_selection(runtime_preset_key)
        if runtime_selection is None:
            continue
        agent_settings.MODEL_CONFIG[phase] = _build_runtime_codex_model_config(
            runtime_selection.model_name,
            reasoning_effort=runtime_selection.reasoning_effort,
        )
        applied[phase] = runtime_preset_key

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


def is_codex_runtime_default_preset_key(key: str | None) -> bool:
    return isinstance(key, str) and key == CODEX_RUNTIME_DEFAULT_KEY


def parse_codex_runtime_preset_selection(key: str | None) -> CodexRuntimePresetSelection | None:
    if not isinstance(key, str):
        return None
    if not key.startswith(CODEX_RUNTIME_PRESET_PREFIX):
        return None
    if is_codex_runtime_default_preset_key(key):
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


def resolve_raw_codex_model_name_for_preset_key(key: str | None) -> str | None:
    if is_codex_runtime_default_preset_key(key):
        return None
    runtime_selection = parse_codex_runtime_preset_selection(key)
    if runtime_selection is not None:
        normalized_model_name = runtime_selection.model_name.strip()
        return normalized_model_name or None
    if not isinstance(key, str):
        return None
    preset = agent_settings.MODEL_PRESETS.get(key)
    if preset is None or preset["provider"] != ModelProvider.CODEX:
        return None
    model_name = preset["config"].model_name.strip()
    return model_name or None


def resolve_codex_model_name_for_preset_key(key: str | None) -> str | None:
    model_name = resolve_raw_codex_model_name_for_preset_key(key)
    if model_name is None:
        return None
    return normalize_codex_runtime_model_name(model_name)


def resolve_codex_reasoning_effort_for_preset_key(key: str | None) -> CodexRuntimeReasoningEffort:
    if is_codex_runtime_default_preset_key(key):
        return None
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
    entries = tuple(catalog_entries)
    runtime_infos: list[PresetInfo] = []
    seen_identities: dict[tuple[str, CodexRuntimeReasoningEffort], int] = {}

    default_entry = _resolve_runtime_default_catalog_entry(entries)
    if default_entry is not None:
        runtime_infos.append(
            _build_runtime_codex_default_preset_info(
                display_name=default_entry.display_name,
                model_name=default_entry.model,
                default_reasoning_effort=default_entry.default_reasoning_effort,
                description=default_entry.description,
            )
        )

    for entry in entries:
        model_name = entry.model.strip()
        if not model_name:
            continue
        normalized_model_name = normalize_codex_runtime_model_name(model_name)
        for reasoning_option in _resolve_runtime_reasoning_options(entry):
            identity = (
                normalized_model_name,
                reasoning_option.reasoning_effort,
            )
            preset = _build_runtime_codex_preset_info(
                model_name,
                display_name=entry.display_name,
                description=entry.description,
                reasoning_effort=reasoning_option.reasoning_effort,
                reasoning_description=reasoning_option.description,
            )
            existing_index = seen_identities.get(identity)
            if existing_index is None:
                seen_identities[identity] = len(runtime_infos)
                runtime_infos.append(preset)
                continue

            existing_preset = runtime_infos[existing_index]
            existing_model_name = parse_codex_runtime_preset_key(existing_preset.key)
            if _prefer_runtime_catalog_model_name(
                existing_model_name,
                candidate_model_name=model_name,
                normalized_model_name=normalized_model_name,
            ):
                runtime_infos[existing_index] = preset

    return runtime_infos


def build_codex_runtime_executable_identities(
    catalog_entries: Iterable[CodexRuntimeModelCatalogEntry],
) -> frozenset[tuple[str, CodexRuntimeReasoningEffort]]:
    identities: set[tuple[str, CodexRuntimeReasoningEffort]] = set()
    for entry in catalog_entries:
        model_name = entry.model.strip()
        if not model_name:
            continue
        normalized_model_name = normalize_codex_runtime_model_name(model_name)
        identities.add((normalized_model_name, None))
        normalized_default_effort = _normalize_codex_reasoning_effort(entry.default_reasoning_effort)
        if normalized_default_effort is not None:
            identities.add((normalized_model_name, normalized_default_effort))
        for option in entry.supported_reasoning_efforts:
            normalized_effort = _normalize_codex_reasoning_effort(option.reasoning_effort)
            if normalized_effort is not None:
                identities.add((normalized_model_name, normalized_effort))
    return frozenset(identities)


def _build_runtime_codex_default_preset_info(
    *,
    display_name: str | None = None,
    model_name: str | None = None,
    default_reasoning_effort: CodexRuntimeReasoningEffort = None,
    description: str | None = None,
) -> PresetInfo:
    details = "Follow the current default model from the live Codex app-server catalog."
    current_model = (display_name or "").strip() or model_name
    if current_model:
        details = f"{details} Current default: {current_model}."
    normalized_effort = _normalize_codex_reasoning_effort(default_reasoning_effort)
    if normalized_effort is not None:
        details = f"{details} Default reasoning effort: {_format_reasoning_description(normalized_effort)}."
    if description:
        details = f"{details} {description.strip()}".strip()
    return PresetInfo(
        key=CODEX_RUNTIME_DEFAULT_KEY,
        label="Codex runtime default",
        description=details,
        provider=ModelProvider.CODEX,
    )


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


def _build_runtime_codex_default_model_config() -> ModelConfig:
    template = _resolve_codex_runtime_template()
    return template._replace(
        model_name=CODEX_RUNTIME_DEFAULT_MODEL_NAME,
        reasoning=ReasoningMode.DYNAMIC,
    )


def _build_runtime_codex_model_config(
    model_name: str,
    *,
    reasoning_effort: CodexRuntimeReasoningEffort = None,
) -> ModelConfig:
    template = _resolve_codex_runtime_template()
    reasoning_mode = ReasoningMode.DYNAMIC
    if reasoning_effort is not None:
        reasoning_mode = _reasoning_mode_from_effort(reasoning_effort, fallback=template.reasoning)
    return template._replace(model_name=model_name, reasoning=reasoning_mode)


def _resolve_codex_runtime_template() -> ModelConfig:
    for preset in agent_settings.MODEL_PRESETS.values():
        if preset["provider"] == ModelProvider.CODEX:
            return preset["config"]
    raise ValueError("No Codex model preset is defined in agentrules.config.agents.MODEL_PRESETS.")


def _resolve_runtime_reasoning_options(
    entry: CodexRuntimeModelCatalogEntry,
) -> tuple[_ResolvedCodexRuntimeReasoningOption, ...]:
    descriptions: dict[str, str | None] = {}
    for option in entry.supported_reasoning_efforts:
        normalized_effort = _normalize_codex_reasoning_effort(option.reasoning_effort)
        if normalized_effort is None:
            continue
        if normalized_effort not in descriptions:
            descriptions[normalized_effort] = option.description

    options: list[_ResolvedCodexRuntimeReasoningOption] = []
    normalized_default_effort = _normalize_codex_reasoning_effort(entry.default_reasoning_effort)
    if normalized_default_effort is None:
        options.append(_ResolvedCodexRuntimeReasoningOption(reasoning_effort=None))
    else:
        options.append(
            _ResolvedCodexRuntimeReasoningOption(
                reasoning_effort=normalized_default_effort,
                description=descriptions.get(normalized_default_effort),
            )
        )

    ordered_efforts = [
        effort
        for effort in _CODEX_RUNTIME_REASONING_EFFORT_ORDER
        if effort in descriptions and effort != normalized_default_effort
    ]
    options.extend(
        _ResolvedCodexRuntimeReasoningOption(
            reasoning_effort=cast(CodexRuntimeReasoningEffort, effort),
            description=descriptions.get(effort),
        )
        for effort in ordered_efforts
    )
    return tuple(options)


def _resolve_runtime_default_catalog_entry(
    entries: Iterable[CodexRuntimeModelCatalogEntry],
) -> CodexRuntimeModelCatalogEntry | None:
    for entry in entries:
        if entry.is_default and entry.model.strip():
            return entry
    return None


def _normalize_codex_reasoning_effort(value: object) -> CodexRuntimeReasoningEffort:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if normalized in _CODEX_RUNTIME_REASONING_EFFORT_SET:
        return normalized
    return None


def normalize_codex_runtime_model_name(model_name: str) -> str:
    normalized = model_name.strip()
    return LEGACY_CODEX_RUNTIME_MODEL_ALIASES.get(normalized, normalized)


def codex_runtime_model_alias_candidates(model_name: str) -> tuple[str, ...]:
    normalized = model_name.strip()
    if not normalized:
        return ()

    candidates: list[str] = []

    def _append(value: str | None) -> None:
        if value and value not in candidates:
            candidates.append(value)

    canonical_model_name = normalize_codex_runtime_model_name(normalized)
    _append(normalized)
    _append(canonical_model_name)
    for legacy_model_name in _LEGACY_CODEX_RUNTIME_MODEL_NAMES_BY_CANONICAL.get(canonical_model_name, ()):
        _append(legacy_model_name)
    return tuple(candidates)


def _prefer_runtime_catalog_model_name(
    existing_model_name: str | None,
    *,
    candidate_model_name: str,
    normalized_model_name: str,
) -> bool:
    if existing_model_name == normalized_model_name:
        return False
    return candidate_model_name == normalized_model_name


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
        ModelProvider.CLAUDE_CODE: "Claude Code",
        ModelProvider.ANTHROPIC: "Anthropic",
        ModelProvider.GEMINI: "Google Gemini",
        ModelProvider.DEEPSEEK: "DeepSeek",
        ModelProvider.XAI: "xAI Grok",
    }
    return mapping.get(provider, provider.value.title())
