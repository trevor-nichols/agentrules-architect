"""Serialization helpers for persisting CLI configuration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from agentrules.core.utils.constants import DEFAULT_RULES_FILENAME

from .models import CLIConfig, ExclusionOverrides, FeatureToggles, OutputPreferences, ProviderConfig
from .utils import (
    coerce_bool,
    coerce_positive_int,
    coerce_string_list,
    normalize_researcher_mode,
    normalize_rules_filename,
    normalize_verbosity_label,
)


def config_from_dict(payload: Mapping[str, Any]) -> CLIConfig:
    providers: dict[str, ProviderConfig] = {}
    for name, values in payload.get("providers", {}).items():
        if not isinstance(name, str):
            continue
        if isinstance(values, Mapping):
            providers[name] = ProviderConfig(**values)
        else:
            providers[name] = ProviderConfig(api_key=cast(str | None, values))

    models = {
        phase: preset
        for phase, preset in payload.get("models", {}).items()
        if isinstance(phase, str) and isinstance(preset, str)
    }

    raw_verbosity = payload.get("verbosity")
    verbosity = cast(str | None, raw_verbosity if isinstance(raw_verbosity, str) else None)

    outputs_payload = payload.get("outputs")
    outputs = OutputPreferences(
        generate_cursorignore=coerce_bool(
            outputs_payload.get("generate_cursorignore") if isinstance(outputs_payload, Mapping) else None,
            default=False,
        ),
        generate_agent_scaffold=coerce_bool(
            outputs_payload.get("generate_agent_scaffold") if isinstance(outputs_payload, Mapping) else None,
            default=False,
        ),
        generate_phase_outputs=coerce_bool(
            outputs_payload.get("generate_phase_outputs") if isinstance(outputs_payload, Mapping) else None,
            default=True,
        ),
        rules_filename=normalize_rules_filename(
            outputs_payload.get("rules_filename") if isinstance(outputs_payload, Mapping) else None,
            default=DEFAULT_RULES_FILENAME,
        ),
    )

    exclusions_payload = payload.get("exclusions")
    exclusions = ExclusionOverrides(
        respect_gitignore=coerce_bool(
            exclusions_payload.get("respect_gitignore") if isinstance(exclusions_payload, Mapping) else None,
            default=True,
        ),
        add_directories=coerce_string_list(exclusions_payload, "directories"),
        remove_directories=coerce_string_list(exclusions_payload, "remove_directories"),
        add_files=coerce_string_list(exclusions_payload, "files"),
        remove_files=coerce_string_list(exclusions_payload, "remove_files"),
        add_extensions=coerce_string_list(exclusions_payload, "extensions"),
        remove_extensions=coerce_string_list(exclusions_payload, "remove_extensions"),
        tree_max_depth=coerce_positive_int(
            exclusions_payload.get("tree_max_depth") if isinstance(exclusions_payload, Mapping) else None,
            minimum=1,
            default=None,
        ),
    )

    features_payload = payload.get("features")
    features = FeatureToggles(
        researcher_mode=normalize_researcher_mode(
            features_payload.get("researcher_mode") if isinstance(features_payload, Mapping) else None,
            default="off",
        )
    )

    return CLIConfig(
        providers=providers,
        models=models,
        verbosity=verbosity,
        outputs=outputs,
        exclusions=exclusions,
        features=features,
    )


def config_to_dict(config: CLIConfig) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "providers": {
            name: {"api_key": cfg.api_key}
            for name, cfg in config.providers.items()
            if cfg.api_key
        }
    }

    if config.models:
        payload["models"] = dict(config.models)

    if config.verbosity:
        normalized = normalize_verbosity_label(config.verbosity)
        if normalized:
            payload["verbosity"] = normalized

    outputs_payload: dict[str, Any] = {}
    if config.outputs.generate_cursorignore:
        outputs_payload["generate_cursorignore"] = True
    if config.outputs.generate_agent_scaffold:
        outputs_payload["generate_agent_scaffold"] = True
    if not config.outputs.generate_phase_outputs:
        outputs_payload["generate_phase_outputs"] = False
    if config.outputs.rules_filename != DEFAULT_RULES_FILENAME:
        outputs_payload["rules_filename"] = config.outputs.rules_filename
    if outputs_payload:
        payload["outputs"] = outputs_payload

    if not config.exclusions.is_empty():
        exclusions_payload: dict[str, Any] = {
            "directories": list(config.exclusions.add_directories),
            "remove_directories": list(config.exclusions.remove_directories),
            "files": list(config.exclusions.add_files),
            "remove_files": list(config.exclusions.remove_files),
            "extensions": list(config.exclusions.add_extensions),
            "remove_extensions": list(config.exclusions.remove_extensions),
        }
        if not config.exclusions.respect_gitignore:
            exclusions_payload["respect_gitignore"] = False
        if config.exclusions.tree_max_depth is not None:
            exclusions_payload["tree_max_depth"] = config.exclusions.tree_max_depth
        payload["exclusions"] = exclusions_payload

    if not config.features.is_default():
        payload["features"] = {
            "researcher_mode": config.features.researcher_mode,
        }

    return payload
