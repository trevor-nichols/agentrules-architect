"""Top-level settings menu wiring."""

from __future__ import annotations

import questionary

from agentrules.cli.context import CliContext
from agentrules.cli.ui.styles import CLI_STYLE, navigation_choice

from .codex import configure_codex_runtime
from .exclusions import configure_exclusions
from .logging import configure_logging
from .models import configure_models
from .outputs import configure_output_preferences
from .providers import configure_provider_keys

SETTINGS_CATEGORY_ENTRIES: tuple[tuple[str, str], ...] = (
    ("Provider API keys", "providers"),
    ("Codex runtime", "codex"),
    ("Model presets per phase", "models"),
    ("Logging verbosity", "logging"),
    ("Output preferences", "outputs"),
    ("Exclusion rules", "exclusions"),
)


def build_settings_category_choices() -> list[questionary.Choice]:
    """Build the top-level settings category list."""

    return [questionary.Choice(title=title, value=value) for title, value in SETTINGS_CATEGORY_ENTRIES]


def configure_settings(context: CliContext) -> None:
    """Run the interactive settings menu."""

    console = context.console
    console.print("\n[bold]Settings[/bold]")
    console.print("[dim]Provider API keys and the local Codex runtime are configured separately.[/]")

    while True:
        selection = questionary.select(
            "Select a settings category:",
            choices=[
                *build_settings_category_choices(),
                navigation_choice("Back", value="__BACK__"),
            ],
            qmark="⚙️",
            style=CLI_STYLE,
        ).ask()

        if selection in (None, "__BACK__"):
            console.print("[dim]Leaving settings.[/]")
            return
        if selection == "providers":
            configure_provider_keys(context)
        elif selection == "codex":
            configure_codex_runtime(context)
        elif selection == "models":
            configure_models(context)
        elif selection == "logging":
            configure_logging(context)
        elif selection == "outputs":
            configure_output_preferences(context)
        elif selection == "exclusions":
            configure_exclusions(context)
