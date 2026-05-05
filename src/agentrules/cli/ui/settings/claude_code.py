"""Claude Code runtime configuration flow."""

from __future__ import annotations

import questionary
from rich.table import Table

from agentrules.cli.context import CliContext
from agentrules.cli.services import claude_code_runtime, configuration
from agentrules.cli.ui.styles import CLI_STYLE, navigation_choice, value_choice


def _format_status(diagnostics: claude_code_runtime.ClaudeCodeRuntimeDiagnostics) -> str:
    if diagnostics.runtime_error:
        return "[red]Unavailable[/]"
    if diagnostics.version_error:
        return "[yellow]Executable found[/]"
    return "[green]Available[/]"


def _format_bool(value: bool) -> str:
    return "[green]Yes[/]" if value else "[yellow]No[/]"


def _format_cli_path(cli_path: str | None) -> str:
    return cli_path or "[dim]SDK default[/]"


def _format_cli_path_plain(cli_path: str | None) -> str:
    return cli_path or "SDK default"


def _format_resolved_executable(state: configuration.ClaudeCodeRuntimeState) -> str:
    if state.executable_path:
        return state.executable_path
    if state.cli_path is None:
        return "[dim]SDK default[/]"
    return "[red]Not found[/]"


def _render_runtime_summary(
    context: CliContext,
    state: configuration.ClaudeCodeRuntimeState,
    diagnostics: claude_code_runtime.ClaudeCodeRuntimeDiagnostics,
) -> None:
    config_table = Table(title="[bold]Claude Code Runtime Configuration[/bold]", show_lines=False, pad_edge=False)
    config_table.add_column("Setting", style="bold")
    config_table.add_column("Value")
    config_table.add_row("Configured executable", _format_cli_path(state.cli_path))
    config_table.add_row("Resolved executable", _format_resolved_executable(state))
    config_table.add_row("Claude Agent SDK", _format_bool(diagnostics.sdk_available))
    config_table.add_row("Auth strategy", state.auth_strategy)
    config_table.add_row("OAuth token env var", state.oauth_token_env_var)
    config_table.add_row("Strip Anthropic API-key env", _format_bool(state.sanitize_api_key_env))

    live_table = Table(title="[bold]Runtime Diagnostics[/bold]", show_lines=False, pad_edge=False)
    live_table.add_column("Signal", style="bold")
    live_table.add_column("Value")
    live_table.add_row("Status", _format_status(diagnostics))
    live_table.add_row("Version", diagnostics.version or "[dim]-[/]")
    live_table.add_row("OAuth token present", _format_bool(diagnostics.oauth_token_present))
    live_table.add_row(
        "API-key env visible to child",
        _format_bool(diagnostics.api_key_env_present_after_sanitization),
    )

    context.console.print("")
    context.console.print(config_table)
    context.console.print("")
    context.console.print(live_table)
    if diagnostics.runtime_error:
        context.console.print(f"\n[red]Runtime error:[/] {diagnostics.runtime_error}")
    if diagnostics.version_error:
        context.console.print(f"\n[yellow]Version check:[/] {diagnostics.version_error}")
    for note in build_runtime_guidance(state, diagnostics):
        context.console.print(note)
    context.console.print("")


def build_runtime_guidance(
    state: configuration.ClaudeCodeRuntimeState,
    diagnostics: claude_code_runtime.ClaudeCodeRuntimeDiagnostics,
) -> list[str]:
    """Render operator notes for the current Claude Code runtime state."""

    notes: list[str] = [
        "[dim]Claude Code uses the Claude Agent SDK and Claude.ai OAuth subscription auth. "
        "AgentRules uses the SDK default runtime unless you configure an explicit executable path.[/]"
    ]

    if diagnostics.runtime_error:
        if not diagnostics.sdk_available:
            notes.append("[dim]Install AgentRules dependencies so `claude-agent-sdk` is importable.[/]")
        elif state.cli_path:
            notes.append(
                "[dim]Set a valid Claude executable path, or clear the path to let the SDK use its default "
                "runtime resolution.[/]"
            )
    else:
        notes.append(
            "[dim]Authenticate outside AgentRules with Claude Code's OAuth flow. When the `claude` command "
            "is available, run `claude auth login`; for automated environments, run `claude setup-token` "
            "and export CLAUDE_CODE_OAUTH_TOKEN.[/]"
        )

    if state.sanitize_api_key_env:
        notes.append(
            "[dim]Anthropic API-key environment variables are stripped from Claude Code child processes "
            "so Claude.ai OAuth remains authoritative.[/]"
        )
    elif diagnostics.api_key_env_present_after_sanitization:
        notes.append(
            "[yellow]Anthropic API-key environment variables are visible to Claude Code. "
            "Re-enable sanitization unless you intentionally want API-key precedence.[/]"
        )

    if diagnostics.is_available:
        notes.append(
            "[dim]Next step: choose a Claude Code preset under Settings -> Model presets per phase "
            "to route analysis through this runtime.[/]"
        )

    return notes


def configure_claude_code_runtime(context: CliContext) -> None:
    """Interactive prompts for configuring the local Claude Code runtime."""

    console = context.console
    console.print("\n[bold]Configure Claude Code Runtime[/bold]")
    console.print(
        "Claude Code uses the Claude Agent SDK and Claude.ai OAuth subscription auth. Leave the executable "
        "path blank to use the SDK default runtime; set a path only when you need an explicit override. "
        "AgentRules only stores runtime settings and never stores Anthropic API keys for this provider.\n"
    )

    while True:
        state = configuration.get_claude_code_runtime_state()
        diagnostics = claude_code_runtime.get_claude_code_runtime_diagnostics()
        _render_runtime_summary(context, state, diagnostics)

        selection = questionary.select(
            "Select Claude Code runtime action:",
            choices=[
                value_choice("Claude executable path", _format_cli_path_plain(state.cli_path), value="__CLI_PATH__"),
                value_choice(
                    "Strip Anthropic API-key env",
                    "Yes" if state.sanitize_api_key_env else "No",
                    value="__SANITIZE__",
                ),
                questionary.Choice(title="Show OAuth login instructions", value="__LOGIN_HELP__"),
                value_choice(
                    "Refresh runtime status",
                    "Available" if diagnostics.is_available else "Retry",
                    value="__REFRESH__",
                ),
                navigation_choice("Back", value="__BACK__"),
            ],
            qmark="🧰",
            style=CLI_STYLE,
        ).ask()

        if selection in (None, "__BACK__"):
            console.print("[dim]Leaving Claude Code runtime settings.[/]")
            return

        if selection == "__CLI_PATH__":
            answer = questionary.text(
                "Enter the Claude executable path or command name (leave blank for SDK default):",
                default=state.cli_path or "",
                qmark="🧰",
                style=CLI_STYLE,
            ).ask()
            if answer is None:
                console.print("[yellow]No changes made to Claude executable path.[/]")
                continue
            configuration.save_claude_code_cli_path(answer)
            console.print("[green]Claude executable path updated.[/]")
            continue

        if selection == "__SANITIZE__":
            enabled = questionary.confirm(
                "Strip Anthropic API-key environment variables from Claude Code child processes?",
                default=state.sanitize_api_key_env,
                qmark="🧰",
                style=CLI_STYLE,
            ).ask()
            if enabled is None:
                console.print("[yellow]No changes made to environment sanitization.[/]")
                continue
            configuration.save_claude_code_sanitize_api_key_env(bool(enabled))
            console.print("[green]Claude Code environment sanitization updated.[/]")
            continue

        if selection == "__LOGIN_HELP__":
            console.print("[cyan]Run this in your terminal:[/] claude auth login")
            console.print(
                "[cyan]For automation/CI:[/] claude setup-token, then export CLAUDE_CODE_OAUTH_TOKEN"
            )
            console.print(
                "[dim]Complete the Claude.ai OAuth flow in Claude Code, then return here and refresh status.[/]"
            )
            continue

        if selection == "__REFRESH__":
            console.print("[green]Claude Code runtime status refreshed.[/]")
            continue
