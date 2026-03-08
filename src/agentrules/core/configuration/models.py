"""Dataclasses describing persisted CLI configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from agentrules.core.utils.constants import (
    DEFAULT_RULES_FILENAME,
    DEFAULT_RULES_TREE_MAX_DEPTH,
    DEFAULT_SNAPSHOT_FILENAME,
)

ResearcherMode = Literal["on", "off"]
CodexHomeStrategy = Literal["managed", "inherit"]


@dataclass
class ProviderConfig:
    api_key: str | None = None


@dataclass
class CodexConfig:
    cli_path: str = "codex"
    home_strategy: CodexHomeStrategy = "managed"
    managed_home: str | None = None

    def is_default(self) -> bool:
        return self.cli_path == "codex" and self.home_strategy == "managed" and self.managed_home is None


@dataclass
class OutputPreferences:
    generate_cursorignore: bool = False
    generate_agent_scaffold: bool = False
    generate_phase_outputs: bool = True
    generate_snapshot: bool = True
    rules_filename: str = DEFAULT_RULES_FILENAME
    snapshot_filename: str = DEFAULT_SNAPSHOT_FILENAME
    rules_tree_max_depth: int = DEFAULT_RULES_TREE_MAX_DEPTH


@dataclass
class ExclusionOverrides:
    respect_gitignore: bool = True
    add_directories: list[str] = field(default_factory=list)
    remove_directories: list[str] = field(default_factory=list)
    add_files: list[str] = field(default_factory=list)
    remove_files: list[str] = field(default_factory=list)
    add_extensions: list[str] = field(default_factory=list)
    remove_extensions: list[str] = field(default_factory=list)
    tree_max_depth: int | None = None

    def is_empty(self) -> bool:
        override_lists = (
            self.add_directories,
            self.remove_directories,
            self.add_files,
            self.remove_files,
            self.add_extensions,
            self.remove_extensions,
        )
        depth_overridden = self.tree_max_depth is not None
        return self.respect_gitignore and not any(override_lists) and not depth_overridden


@dataclass
class FeatureToggles:
    researcher_mode: ResearcherMode = "off"

    def is_default(self) -> bool:
        return self.researcher_mode == "off"


@dataclass
class CLIConfig:
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    codex: CodexConfig = field(default_factory=CodexConfig)
    models: dict[str, str] = field(default_factory=dict)
    verbosity: str | None = None
    outputs: OutputPreferences = field(default_factory=OutputPreferences)
    exclusions: ExclusionOverrides = field(default_factory=ExclusionOverrides)
    features: FeatureToggles = field(default_factory=FeatureToggles)
