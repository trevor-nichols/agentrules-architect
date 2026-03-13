"""Pipeline orchestration utilities for the CursorRules Architect."""

from .config import (
    EffectiveExclusions,
    GitignoreSnapshot,
    PipelineMetrics,
    PipelineResult,
    PipelineSettings,
    ProjectSnapshot,
)
from .factory import create_default_pipeline
from .orchestrator import AnalysisPipeline
from .output import PipelineOutputOptions, PipelineOutputSummary, PipelineOutputWriter
from .project_profile import build_project_profile
from .snapshot import build_project_snapshot

__all__ = [
    "AnalysisPipeline",
    "EffectiveExclusions",
    "GitignoreSnapshot",
    "PipelineMetrics",
    "PipelineOutputOptions",
    "PipelineOutputSummary",
    "PipelineOutputWriter",
    "PipelineResult",
    "PipelineSettings",
    "ProjectSnapshot",
    "build_project_profile",
    "create_default_pipeline",
    "build_project_snapshot",
]
