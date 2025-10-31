"""Context primitives shared across CLI modules."""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Console


@dataclass
class CliContext:
    """Lightweight container for objects shared by CLI handlers."""

    console: Console

    def print(self, *args, **kwargs) -> None:
        """Convenience wrapper around the Rich console print method."""

        self.console.print(*args, **kwargs)


def mask_secret(value: str | None) -> str:
    """Return a masked representation of a secret for safe display."""

    if not value:
        return "Not set"
    if len(value) <= 6:
        return "*" * len(value)
    return f"{value[:3]}…{value[-3:]}"


def format_secret_status(value: str | None) -> str:
    """Return a Rich-colored status indicator for a provider secret."""

    if value:
        return "[green]Configured[/]"
    return "[red]Not set[/]"
