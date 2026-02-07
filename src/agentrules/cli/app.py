"""Typer application wiring for the agentrules CLI."""

from __future__ import annotations

import typer

from .bootstrap import bootstrap_runtime
from .commands.analyze import register as register_analyze
from .commands.configure import register as register_configure
from .commands.execplan import register as register_execplan
from .commands.execplan_registry import register as register_execplan_registry
from .commands.keys import register as register_keys
from .commands.tree import register as register_tree
from .ui.main_menu import run_main_menu


def build_app() -> typer.Typer:
    """Construct the Typer application and register subcommands."""

    app = typer.Typer(
        name="agentrules",
        help="Analyze a project and generate Agent rules using multi-provider AI agents.",
        invoke_without_command=True,
        add_completion=False,
    )

    register_analyze(app)
    register_configure(app)
    register_execplan(app)
    register_execplan_registry(app)
    register_keys(app)
    register_tree(app)

    @app.callback(invoke_without_command=True)
    def main(
        ctx: typer.Context,
        version: bool | None = typer.Option(
            None,
            "--version",
            help="Show the agentrules version and exit.",
        ),
    ) -> None:
        context = bootstrap_runtime()

        if version:
            import importlib.metadata

            version_str = importlib.metadata.version("agentrules")
            context.console.print(f"agentrules {version_str}")
            raise typer.Exit()

        if ctx.invoked_subcommand is not None:
            return

        run_main_menu(context)

    return app


app = build_app()
