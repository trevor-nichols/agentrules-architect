"""Implementation of the `keys` subcommand."""

from __future__ import annotations

import typer

from ..bootstrap import bootstrap_runtime
from ..ui.settings import show_provider_summary


def register(app: typer.Typer) -> None:
    """Register the `keys` subcommand with the provided Typer app."""

    @app.command("keys")
    def show_keys() -> None:  # type: ignore[func-returns-value]
        """Show configured provider key status without printing secret values."""

        context = bootstrap_runtime()
        show_provider_summary(context)
