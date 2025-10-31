"""Context primitives shared across CLI modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from rich.console import Console


@dataclass
class CliContext:
    """Lightweight container for objects shared by CLI handlers."""

    console: Console

    def print(self, *args, **kwargs) -> None:
        """Convenience wrapper around the Rich console print method."""

        self.console.print(*args, **kwargs)


def mask_secret(value: Optional[str]) -> str:
    """Return a masked representation of a secret for safe display."""

    if not value:
        return "[not set]"
    if len(value) <= 6:
        return "*" * len(value)
    return f"{value[:3]}…{value[-3:]}"
