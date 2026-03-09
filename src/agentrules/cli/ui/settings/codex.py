"""Codex runtime configuration flow."""

from __future__ import annotations

import questionary
from rich.table import Table

from agentrules.cli.context import CliContext
from agentrules.cli.services import codex_runtime, configuration
from agentrules.cli.ui.styles import CLI_STYLE, navigation_choice, value_choice


def _format_home_strategy(strategy: str) -> str:
    return "Managed by AgentRules" if strategy == "managed" else "Inherit existing"


def _format_runtime_status(diagnostics: codex_runtime.CodexRuntimeDiagnostics) -> str:
    if diagnostics.runtime_error:
        return "[red]Unavailable[/]"
    if diagnostics.can_connect:
        return "[green]Connected[/]"
    return "[yellow]Unknown[/]"


def _format_account_status(diagnostics: codex_runtime.CodexRuntimeDiagnostics) -> str:
    if diagnostics.account_error:
        return f"[red]Unavailable[/] ({diagnostics.account_error})"
    account = diagnostics.account
    if account is None or not account.is_authenticated:
        return "[yellow]Signed out[/]"

    identity = account.email or account.account_type or "authenticated"
    plan = account.plan_type or "unknown plan"
    return f"[green]Signed in[/] ({identity}, {plan})"


def _format_model_catalog_status(diagnostics: codex_runtime.CodexRuntimeDiagnostics) -> str:
    if diagnostics.models_error:
        return f"[red]Unavailable[/] ({diagnostics.models_error})"
    count = len(diagnostics.models)
    if count == 0:
        return "[yellow]No models returned[/]"
    return f"[green]{count} available[/]"


def _render_runtime_summary(
    context: CliContext,
    state: configuration.CodexRuntimeState,
    diagnostics: codex_runtime.CodexRuntimeDiagnostics,
) -> None:
    config_table = Table(title="[bold]Codex Runtime Configuration[/bold]", show_lines=False, pad_edge=False)
    config_table.add_column("Setting", style="bold")
    config_table.add_column("Value")
    config_table.add_row("Configured executable", state.cli_path)
    config_table.add_row("Resolved executable", state.executable_path or "[red]Not found[/]")
    config_table.add_row("CODEX_HOME strategy", _format_home_strategy(state.home_strategy))
    config_table.add_row(
        "Managed CODEX_HOME override",
        state.managed_home or "[dim](default AgentRules location)[/]",
    )
    config_table.add_row(
        "Effective CODEX_HOME",
        state.effective_home or "[dim]Inherited runtime value is currently unset[/]",
    )

    live_table = Table(title="[bold]Live App-Server Status[/bold]", show_lines=False, pad_edge=False)
    live_table.add_column("Signal", style="bold")
    live_table.add_column("Value")
    live_table.add_row("Status", _format_runtime_status(diagnostics))
    live_table.add_row("User agent", diagnostics.user_agent or "[dim]-[/]")
    live_table.add_row("Account", _format_account_status(diagnostics))
    live_table.add_row(
        "Requires OpenAI auth",
        (
            "[yellow]-[/]"
            if diagnostics.account is None
            else ("[green]Yes[/]" if diagnostics.account.requires_openai_auth else "[green]No[/]")
        ),
    )
    live_table.add_row("Model catalog", _format_model_catalog_status(diagnostics))

    context.console.print("")
    context.console.print(config_table)
    context.console.print("")
    context.console.print(live_table)
    if diagnostics.runtime_error:
        context.console.print(f"\n[red]Runtime error:[/] {diagnostics.runtime_error}")
    if diagnostics.recent_stderr:
        context.console.print(f"[dim]Recent stderr:[/] {diagnostics.recent_stderr[-1]}")
    for note in build_runtime_guidance(state, diagnostics):
        context.console.print(note)
    context.console.print("")


def build_runtime_guidance(
    state: configuration.CodexRuntimeState,
    diagnostics: codex_runtime.CodexRuntimeDiagnostics,
) -> list[str]:
    """Render operator notes for the current Codex runtime state."""

    notes: list[str] = []
    if state.home_strategy == "managed":
        notes.append(
            "[dim]Managed mode keeps a separate AgentRules-owned CODEX_HOME. "
            "Use this when you want an isolated login/config state for AgentRules.[/]"
        )
    else:
        notes.append(
            "[dim]Inherit mode reuses your existing Codex CLI state from CODEX_HOME. "
            "Use this to share your current ChatGPT login, config, and skills.[/]"
        )

    if diagnostics.account is None or not diagnostics.account.is_authenticated:
        if diagnostics.account_error is None:
            notes.append(
                "[dim]Sign in with ChatGPT here to enable Codex-backed presets without storing "
                "OpenAI API keys in AgentRules.[/]"
            )
    elif diagnostics.models:
        notes.append(
            "[dim]Next step: choose a Codex preset under Settings -> Model presets per phase "
            "to route analysis phases through this runtime.[/]"
        )

    return notes


def _render_models_table(context: CliContext, diagnostics: codex_runtime.CodexRuntimeDiagnostics) -> None:
    if diagnostics.models_error:
        context.console.print(f"[red]Could not load Codex models:[/] {diagnostics.models_error}")
        return
    if not diagnostics.models:
        context.console.print("[yellow]Codex did not return any visible models.[/]")
        return

    table = Table(title="[bold]Codex Models[/bold]", show_lines=False, pad_edge=False)
    table.add_column("Model", style="bold")
    table.add_column("Default", no_wrap=True)
    table.add_column("Reasoning", no_wrap=True)
    table.add_column("Modalities", no_wrap=True)
    table.add_column("Description")

    for model in diagnostics.models:
        table.add_row(
            model.model,
            "Yes" if model.is_default else "",
            model.default_reasoning_effort or "-",
            ", ".join(model.input_modalities),
            model.description or model.availability_message or "-",
        )

    context.console.print("")
    context.console.print(table)
    context.console.print("")


def _await_models_acknowledgement() -> None:
    """Keep the model table visible until the operator confirms."""
    questionary.text(
        "Press Enter to return to Codex runtime actions:",
        default="",
        qmark="🧰",
        style=CLI_STYLE,
    ).ask()


def configure_codex_runtime(context: CliContext) -> None:
    """Interactive prompts for configuring the local Codex runtime."""

    console = context.console
    console.print("\n[bold]Configure Codex Runtime[/bold]")
    console.print(
        "Codex uses the local CLI/app-server runtime. Configure the executable path, "
        "choose how AgentRules resolves [cyan]CODEX_HOME[/cyan], and inspect the live "
        "runtime/account/model state.\n"
    )

    while True:
        state = configuration.get_codex_runtime_state()
        diagnostics = codex_runtime.get_codex_runtime_diagnostics(include_models=True)
        _render_runtime_summary(context, state, diagnostics)

        selection = questionary.select(
            "Select Codex runtime action:",
            choices=[
                value_choice("Codex executable path", state.cli_path, value="__CLI_PATH__"),
                value_choice(
                    "CODEX_HOME strategy",
                    _format_home_strategy(state.home_strategy),
                    value="__HOME_STRATEGY__",
                ),
                value_choice(
                    "Managed CODEX_HOME override",
                    state.managed_home or "(default managed location)",
                    value="__MANAGED_HOME__",
                ),
                value_choice(
                    "Refresh live runtime status",
                    "Connected" if diagnostics.can_connect else "Retry",
                    value="__REFRESH__",
                ),
                questionary.Choice(title="Sign in with ChatGPT", value="__LOGIN__"),
                questionary.Choice(title="Sign out of Codex", value="__LOGOUT__"),
                questionary.Choice(title="Show available models", value="__MODELS__"),
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

        if selection == "__REFRESH__":
            console.print("[green]Live Codex runtime status refreshed.[/]")
            continue

        if selection == "__LOGIN__":
            try:
                result = codex_runtime.start_codex_chatgpt_login()
            except Exception as error:
                console.print(f"[red]Codex login failed:[/] {error}")
                continue

            if result.browser_error:
                console.print(f"[yellow]Browser open failed:[/] {result.browser_error}")
            if result.login.auth_url and (result.browser_error or not result.opened_browser):
                console.print(f"[cyan]Open this ChatGPT login URL manually:[/] {result.login.auth_url}")
            if result.waiting_timed_out:
                console.print(
                    "[yellow]ChatGPT login was started, but AgentRules timed out waiting for completion. "
                    "Finish the browser flow, then use refresh to verify the account state.[/]"
                )
                continue
            if result.completion is None:
                console.print(
                    "[yellow]ChatGPT login was started. Complete the browser flow, then refresh the status.[/]"
                )
                continue
            if result.completion.success:
                console.print("[green]ChatGPT login completed successfully.[/]")
            else:
                console.print(f"[red]ChatGPT login failed:[/] {result.completion.error or 'Unknown error'}")
            continue

        if selection == "__LOGOUT__":
            try:
                account = codex_runtime.logout_codex_runtime()
            except Exception as error:
                console.print(f"[red]Codex logout failed:[/] {error}")
                continue
            if account.is_authenticated:
                console.print("[yellow]Codex still reports an authenticated account after logout.[/]")
            else:
                console.print("[green]Codex runtime signed out successfully.[/]")
            continue

        if selection == "__MODELS__":
            _render_models_table(context, diagnostics)
            _await_models_acknowledgement()
            continue
