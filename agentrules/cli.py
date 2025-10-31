"""
Typer-based command-line interface for the CursorRules Architect pipeline.
"""

from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from textwrap import dedent
from typing import List, Optional

import questionary
import typer
from dotenv import load_dotenv
from rich.console import Console

from agentrules.analyzer import ProjectAnalyzer
from agentrules.config_service import (
    PROVIDER_ENV_MAP,
    apply_config_to_environment,
    get_current_provider_keys,
    set_phase_model,
    set_provider_key,
)
from agentrules.logging_setup import configure_logging
from agentrules import model_config

app = typer.Typer(
    name="agentrules",
    help="Analyze a project and generate Cursor rules using multi-provider AI agents.",
    invoke_without_command=True,
    add_completion=False,
)


def _load_env_files() -> None:
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)


def _activate_offline_mode(console: Console) -> None:
    if os.getenv("OFFLINE", "0") != "1":
        return
    try:
        from core.utils.offline import patch_factory_offline

        patch_factory_offline()
        console.print("[yellow]OFFLINE=1 detected: using DummyArchitects (no network calls).[/]")
    except Exception as error:
        console.print(f"[red]Failed to enable OFFLINE mode: {error}[/]")


def _run_pipeline(directory: Path, offline: bool, console: Console) -> None:
    if offline:
        os.environ["OFFLINE"] = "1"
    _activate_offline_mode(console)

    analyzer = ProjectAnalyzer(directory, console)
    start_time = time.time()
    try:
        asyncio.run(analyzer.analyze())
    except RuntimeError:
        # Fallback for already-running loops (e.g., inside notebooks)
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(analyzer.analyze())
        finally:
            loop.close()
    analyzer.persist_outputs(start_time)
    console.print(f"\n[green]Analysis finished for:[/] {directory}")


def _masked(key: Optional[str]) -> str:
    if not key:
        return "[not set]"
    if len(key) <= 6:
        return "*" * len(key)
    return f"{key[:3]}…{key[-3:]}"


def _configure_keys(console: Console) -> None:
    console.print("\n[bold]Configure Provider API Keys[/bold]")
    console.print("Leave blank to keep the current value.\n")

    for provider, env_var in PROVIDER_ENV_MAP.items():
        current_display = _masked(get_current_provider_keys().get(provider))
        answer = questionary.password(
            f"{provider.title()} API key ({env_var}) [{current_display}]:",
            qmark="🔐",
            default="",
        ).ask()
        if answer is None:
            console.print("[yellow]Configuration cancelled.[/]")
            return
        if answer.strip():
            set_provider_key(provider, answer.strip())

    console.print("[green]Provider keys updated.[/]")
    model_config.apply_user_overrides()


def _configure_models(console: Console) -> None:
    console.print("\n[bold]Configure model presets per phase[/bold]")
    console.print("Select the model to use for each phase. Choose 'Reset to default' to revert.\n")

    provider_keys = get_current_provider_keys()
    active = model_config.get_active_presets()

    for phase in model_config.PHASE_SEQUENCE:
        title = model_config.get_phase_title(phase)
        presets = model_config.get_available_presets_for_phase(phase, provider_keys)
        if not presets:
            console.print(f"[yellow]No presets available for {title}; configure provider keys first.[/]")
            continue

        default_key = model_config.get_default_preset_key(phase)
        current_key = active.get(phase, default_key)
        default_info = model_config.get_preset_info(default_key) if default_key else None

        choices: List[questionary.Choice] = []
        if default_info:
            choices.append(
                questionary.Choice(
                    title=f"Reset to default ({default_info.label} – {default_info.provider_display})",
                    value="__RESET__",
                )
            )
        else:
            choices.append(questionary.Choice(title="Reset to default", value="__RESET__"))

        for preset in presets:
            label = f"{preset.label} [{preset.provider_display}]"
            if preset.key == default_key:
                label += " (default)"
            if preset.key == current_key:
                label += " [current]"
            choices.append(questionary.Choice(title=label, value=preset.key))

        default_choice = next((choice.title for choice in choices if choice.value == current_key), choices[0].title)

        selection = questionary.select(
            f"{title}:",
            choices=choices,
            default=default_choice,
            qmark="🧠",
        ).ask()

        if selection is None:
            console.print("[yellow]Model configuration cancelled.[/]")
            return

        if selection == "__RESET__":
            set_phase_model(phase, None)
            active.pop(phase, None)
        else:
            set_phase_model(phase, selection)
            active[phase] = selection

    model_config.apply_user_overrides({phase: key for phase, key in active.items() if phase in model_config.PHASE_SEQUENCE})
    console.print("[green]Model selections saved.[/]")
    model_config.apply_user_overrides()


def _show_keys(console: Console) -> None:
    console.print("\n[bold]Current Provider Configuration[/bold]")
    for provider, key in get_current_provider_keys().items():
        console.print(f"- {provider.title():<10}: {_masked(key)}")
    console.print("")


def _interactive_menu(console: Console) -> None:
    banner = dedent(
        """
        [bold cyan]
         █████╗  ██████╗ ███████╗███╗   ██╗████████╗██████╗ ██╗   ██╗██╗     ███████╗███████╗
        ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝██╔══██╗██║   ██║██║     ██╔════╝██╔════╝
        ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   ██████╔╝██║   ██║██║     ███████╗█████╗
        ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ██╔══██╗██║   ██║██║     ╚════██║██╔══╝
        ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ██║  ██║╚██████╔╝███████╗███████║███████╗
        ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝╚══════╝
        [/bold cyan]
        """
    )
    console.print(banner)

    menu_choices = {
        "Analyze current directory": "analyze_current",
        "Analyze another path": "analyze_other",
        "Configure provider API keys": "configure_keys",
        "Configure models per phase": "configure_models",
        "Show configured providers": "show_keys",
        "Exit": "exit",
    }

    while True:
        choice = questionary.select(
            "What would you like to do?",
            choices=list(menu_choices.keys()),
            qmark="🤖",
        ).ask()

        if choice is None or menu_choices[choice] == "exit":
            console.print("Goodbye!")
            return

        action = menu_choices[choice]
        if action == "analyze_current":
            _run_pipeline(Path.cwd(), offline=False, console=console)
        elif action == "analyze_other":
            path_answer = questionary.path("Target project directory:", only_directories=True).ask()
            if not path_answer:
                continue
            target = Path(path_answer).expanduser().resolve()
            if not target.exists() or not target.is_dir():
                console.print(f"[red]Invalid directory: {target}[/]")
                continue
            _run_pipeline(target, offline=False, console=console)
        elif action == "configure_keys":
            _configure_keys(console)
        elif action == "configure_models":
            _configure_models(console)
        elif action == "show_keys":
            _show_keys(console)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        help="Show the agentrules version and exit.",
    ),
) -> None:
    console = Console()
    configure_logging()
    apply_config_to_environment()
    _load_env_files()
    model_config.apply_user_overrides()

    if version:
        import importlib.metadata

        version_str = importlib.metadata.version("agentrules")
        console.print(f"agentrules {version_str}")
        raise typer.Exit()

    if ctx.invoked_subcommand is not None:
        return

    _interactive_menu(console)


@app.command()
def analyze(
    path: Path = typer.Argument(Path.cwd(), exists=True, dir_okay=True, file_okay=False, resolve_path=True),
    offline: bool = typer.Option(False, "--offline", help="Run using offline dummy architects (no API calls)."),
) -> None:
    console = Console()
    configure_logging()
    apply_config_to_environment()
    _load_env_files()
    model_config.apply_user_overrides()
    _run_pipeline(path, offline, console)


@app.command()
def configure(
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help="Limit configuration to a single provider.",
    ),
    models_only: bool = typer.Option(
        False,
        "--models",
        help="Configure model presets instead of API keys.",
    ),
) -> None:
    console = Console()
    configure_logging()

    if models_only and provider:
        raise typer.BadParameter("Cannot combine --models with --provider.")

    if models_only:
        _configure_models(console)
        return

    if provider:
        if provider not in PROVIDER_ENV_MAP:
            raise typer.BadParameter(f"Unknown provider '{provider}'. Options: {', '.join(PROVIDER_ENV_MAP.keys())}")
        answer = questionary.password(f"{provider.title()} API key:", qmark="🔐").ask()
        if answer is None:
            console.print("[yellow]No changes made.[/]")
            return
        set_provider_key(provider, answer.strip() or None)
        console.print(f"[green]{provider.title()} key updated.[/]")
        model_config.apply_user_overrides()
        return

    _configure_keys(console)


@app.command("keys")
def show_keys() -> None:
    console = Console()
    configure_logging()
    _show_keys(console)
