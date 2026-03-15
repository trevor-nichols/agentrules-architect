"""Data structures used by the analysis pipeline orchestration layer."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from pathspec import PathSpec

from agentrules.core.configuration.models import ExclusionOverrides


@dataclass(frozen=True)
class EffectiveExclusions:
    """Normalized exclusion sets applied during project discovery."""

    directories: frozenset[str]
    files: frozenset[str]
    extensions: frozenset[str]


@dataclass(frozen=True)
class PipelineSettings:
    """Configuration prepared for a single pipeline execution."""

    target_directory: Path
    tree_max_depth: int
    respect_gitignore: bool
    effective_exclusions: EffectiveExclusions
    exclude_relative_paths: frozenset[str] = frozenset()
    exclusion_overrides: ExclusionOverrides | None = None


@dataclass(frozen=True)
class GitignoreSnapshot:
    """Stored information about the .gitignore state for the target project."""

    spec: PathSpec | None
    path: Path | None


@dataclass(frozen=True)
class ProjectSnapshot:
    """Pre-computed project metadata shared across analysis phases."""

    tree_with_delimiters: tuple[str, ...]
    tree: tuple[str, ...]
    dependency_info: Mapping[str, object]
    gitignore: GitignoreSnapshot
    project_profile: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class PipelineMetrics:
    """Measured execution metrics for a pipeline run."""

    elapsed_seconds: float


@dataclass(frozen=True)
class PipelineResult:
    """Aggregated outputs produced by the multi-phase pipeline."""

    snapshot: ProjectSnapshot
    phase1: Mapping[str, object]
    phase2: Mapping[str, object]
    phase3: Mapping[str, object]
    phase4: Mapping[str, object]
    consolidated_report: Mapping[str, object]
    final_analysis: Mapping[str, object]
    metrics: PipelineMetrics
