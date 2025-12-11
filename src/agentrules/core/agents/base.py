"""
core/agents/base.py

This module provides the base Architect class for interacting with AI models.
It defines the abstract base class that all specific model implementations will inherit from.

This module serves as the foundation for all model interactions in the CursorRules Architect system.
"""

# ====================================================
# Importing Required Libraries
# This section imports all the necessary libraries needed for the script.
# ====================================================

import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from enum import Enum
from typing import TYPE_CHECKING, Any

from agentrules.core.streaming import StreamChunk

if TYPE_CHECKING:
    from agentrules.core.types.models import ModelConfig

# ====================================================
# Type Definitions
# This section defines types used throughout the module.
# ====================================================

class ReasoningMode(Enum):
    """Enum for specifying the reasoning mode for a model."""
    # General modes (primarily for Anthropic)
    ENABLED = "enabled"
    DISABLED = "disabled"
    DYNAMIC = "dynamic"

    # OpenAI-specific reasoning effort levels (for o3, o4-mini, gpt-5.1)
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    # For temperature-based models like gpt-4.1, use TEMPERATURE mode
    # and specify the actual temperature value separately
    TEMPERATURE = "temperature"

class ModelProvider(Enum):
    """Enum for specifying the model provider."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    GEMINI = "gemini"
    XAI = "xai"

# ====================================================
# Get Logger
# Set up logger to track events and issues.
# ====================================================

logger = logging.getLogger("project_extractor")

# ====================================================
# BaseArchitect Class Definition
# This class defines the BaseArchitect, which serves as the abstract base class
# for all AI model implementations.
# ====================================================

class BaseArchitect(ABC):
    """
    Abstract base class for all Architect implementations.

    This class defines the common interface that all model-specific Architect
    classes must implement, providing a uniform way to interact with different
    AI models.
    """

    def __init__(
        self,
        provider: ModelProvider,
        model_name: str,
        reasoning: ReasoningMode = ReasoningMode.DISABLED,
        temperature: float | None = None,
        name: str | None = None,
        role: str | None = None,
        responsibilities: list[str] | None = None,
        tools_config: dict | None = None,
        model_config: "ModelConfig | None" = None,
    ):
        """
        Initialize a BaseArchitect instance.

        Args:
            provider: The model provider (Anthropic or OpenAI)
            model_name: Name of the model to use
            reasoning: Reasoning mode to use (if supported by the model)
            temperature: Temperature value for temperature-based models
            name: Optional name for the architect (for specialized roles)
            role: Optional role description
            responsibilities: Optional list of responsibilities
            tools_config: Optional configuration for tools the model can use
        """
        self.provider = provider
        self.model_name = model_name
        self.reasoning = reasoning
        self.temperature = temperature
        self.name = name
        self.role = role
        self.responsibilities = responsibilities or []
        self.tools_config = tools_config or {"enabled": False, "tools": None}
        self._model_config = model_config

    @property
    def supports_streaming(self) -> bool:
        """Indicate whether this architect implementation provides streaming."""
        return False

    @abstractmethod
    async def analyze(self, context: dict[str, Any], tools: list[Any] | None = None) -> dict[str, Any]:
        """
        Run analysis using the AI model.

        Args:
            context: Dictionary containing the context for analysis
            tools: Optional list of tools the model can use

        Returns:
            Dictionary containing the analysis results or error information
        """
        pass

    @abstractmethod
    async def create_analysis_plan(self, phase1_results: dict, prompt: str | None = None) -> dict:
        """
        Create an analysis plan based on Phase 1 results.

        Args:
            phase1_results: Dictionary containing the results from Phase 1
            prompt: Optional custom prompt to use

        Returns:
            Dictionary containing the analysis plan
        """
        pass

    @abstractmethod
    async def synthesize_findings(self, phase3_results: dict, prompt: str | None = None) -> dict:
        """
        Synthesize findings from Phase 3.

        Args:
            phase3_results: Dictionary containing the results from Phase 3
            prompt: Optional custom prompt to use

        Returns:
            Dictionary containing the synthesis
        """
        pass

    @abstractmethod
    async def final_analysis(self, consolidated_report: dict, prompt: str | None = None) -> dict:
        """
        Perform final analysis on the consolidated report.

        Args:
            consolidated_report: Dictionary containing the consolidated report
            prompt: Optional custom prompt to use

        Returns:
            Dictionary containing the final analysis
        """
        pass

    @abstractmethod
    async def consolidate_results(self, all_results: dict, prompt: str | None = None) -> dict:
        """
        Consolidate results from all previous phases.

        Args:
            all_results: Dictionary containing all phase results
            prompt: Optional custom prompt to use

        Returns:
            Dictionary containing the consolidated report
        """
        pass

    def stream_analyze(
        self,
        context: dict[str, Any],
        tools: list[Any] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream analysis results as they are generated by the model.

        Implementations should override this method when streaming is supported.

        Args:
            context: Dictionary containing the context for analysis
            tools: Optional list of tools the model can use

        Yields:
            StreamChunk instances representing incremental output
        """
        async def _not_implemented() -> AsyncIterator[StreamChunk]:
            raise NotImplementedError(f"{self.__class__.__name__} does not implement streaming.")
            yield  # pragma: no cover

        return _not_implemented()
