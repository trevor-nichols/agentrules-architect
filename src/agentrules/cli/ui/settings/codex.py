"""Codex runtime configuration flow."""

from __future__ import annotations

import questionary

from agentrules.cli.context import CliContext
from agentrules.cli.services import configuration
from agentrules.cli.ui.styles import CLI_STYLE, navigation_choice, value_choice


def configure_codex_runtime(context: CliContext) -> None:
    """Interactive prompts for configuring the local Codex runtime."""

    console = context.console
    console.print("\n[bold]Configure Codex Runtime[/bold]")
    console.print(
        "Codex uses the local CLI/app-server runtime. Configure the executable path and how "
        "AgentRules should resolve [cyan]CODEX_HOME[/cyan].\n"
    )

    while True:
        state = configuration.get_codex_runtime_state()
        effective_home = state.effective_home or "Inherited from environment/CLI"
        executable_status = state.executable_path or "Not found"

        selection = questionary.select(
            "Select Codex runtime setting:",
            choices=[
                value_choice("Codex executable path", state.cli_path, value="__CLI_PATH__"),
                value_choice(
                    "CODEX_HOME strategy",
                    "Managed by AgentRules" if state.home_strategy == "managed" else "Inherit existing",
                    value="__HOME_STRATEGY__",
                ),
                value_choice(
                    "Managed CODEX_HOME override",
                    state.managed_home or "(default managed location)",
                    value="__MANAGED_HOME__",
                ),
                value_choice("Effective CODEX_HOME", effective_home, value="__EFFECTIVE_HOME__"),
                value_choice("Resolved executable", executable_status, value="__RESOLVED_EXECUTABLE__"),
                navigation_choice("Back", value="__BACK__"),
            ],
            qmark="🧰",
            style=CLI_STYLE,
        ).ask()

        if selection in (None, "__BACK__"):
            console.print("[dim]Leaving Codex runtime settings.[/]")
            return

        if selection == "__CLI_PATH__":
            answer = questionary.text(
                "Enter the Codex executable path or command name:",
                default=state.cli_path,
                qmark="🧰",
                style=CLI_STYLE,
            ).ask()
            if answer is None:
                console.print("[yellow]No changes made to Codex executable path.[/]")
                continue
            configuration.save_codex_cli_path(answer)
            console.print("[green]Codex executable path updated.[/]")
            continue

        if selection == "__HOME_STRATEGY__":
            strategy = questionary.select(
                "How should AgentRules resolve CODEX_HOME?",
                choices=[
                    questionary.Choice(
                        title="Managed by AgentRules" + (" [current]" if state.home_strategy == "managed" else ""),
                        value="managed",
                    ),
                    questionary.Choice(
                        title="Inherit existing environment/CLI value"
                        + (" [current]" if state.home_strategy == "inherit" else ""),
                        value="inherit",
                    ),
                    navigation_choice("Cancel", value="__CANCEL__"),
                ],
                default=state.home_strategy,
                qmark="🧰",
                style=CLI_STYLE,
            ).ask()
            if strategy in (None, "__CANCEL__"):
                console.print("[yellow]No changes made to CODEX_HOME strategy.[/]")
                continue
            configuration.save_codex_home_strategy(strategy)
            if strategy == "managed":
                console.print("[green]AgentRules will manage CODEX_HOME for Codex runs.[/]")
            else:
                console.print("[green]AgentRules will inherit CODEX_HOME from the environment when present.[/]")
            continue

        if selection == "__MANAGED_HOME__":
            answer = questionary.text(
                "Enter a managed CODEX_HOME override. Leave blank to use the default AgentRules location:",
                default=state.managed_home or "",
                qmark="🧰",
                style=CLI_STYLE,
            ).ask()
            if answer is None:
                console.print("[yellow]No changes made to managed CODEX_HOME.[/]")
                continue
            configuration.save_codex_managed_home(answer or None)
            if answer.strip():
                console.print("[green]Managed CODEX_HOME override updated.[/]")
            else:
                console.print("[green]Managed CODEX_HOME reset to the default AgentRules location.[/]")
            continue

        if selection == "__EFFECTIVE_HOME__":
            console.print(f"[cyan]Effective CODEX_HOME:[/] {effective_home}")
            continue

        if selection == "__RESOLVED_EXECUTABLE__":
            if state.executable_path:
                console.print(f"[cyan]Resolved executable:[/] {state.executable_path}")
            else:
                console.print(
                    "[yellow]The configured Codex executable could not be resolved. "
                    "Install Codex or update the executable path before enabling Codex presets.[/]"
                )
