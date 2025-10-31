"""
core.agents package

Defines public shortcuts for constructing architect instances without triggering
eager import cycles during module initialization.
"""

from .base import ModelProvider


def get_architect_for_phase(*args, **kwargs):
    from .factory.factory import get_architect_for_phase as _impl

    return _impl(*args, **kwargs)


__all__ = ["get_architect_for_phase", "ModelProvider"]
