"""Implementation of the `execplan-registry` command group."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from agentrules.core.utils.execplan_registry import (
    DEFAULT_EXECPLANS_DIR,
    DEFAULT_REGISTRY_PATH,
    RegistryBuildResult,
    build_execplan_registry,
    collect_execplan_registry,
)

from ..bootstrap import bootstrap_runtime


def _resolve_path(root: Path, value: Path) -> Path:
    return value.resolve() if value.is_absolute() else (root / value).resolve()


def _print_issues(result: RegistryBuildResult, *, console) -> None:
    for issue in result.issues:
        prefix = "[yellow]WARNING[/]" if issue.severity == "warning" else "[red]ERROR[/]"
        if issue.path:
            console.print(f"{prefix} {issue.path}: {issue.message}")
        else:
            console.print(f"{prefix} {issue.message}")


def _exit_code_for_result(result: RegistryBuildResult, *, fail_on_warn: bool) -> int:
    if result.error_count > 0:
        return 2
    if fail_on_warn and result.warning_count > 0:
        return 1
    return 0


def _run_check(
    *,
    root: Path,
    execplans_dir: Path,
    include_timestamp: bool,
    fail_on_warn: bool,
) -> tuple[RegistryBuildResult, int]:
    result = collect_execplan_registry(
        root=root,
        execplans_dir=execplans_dir,
        include_timestamp=include_timestamp,
    )
    return result, _exit_code_for_result(result, fail_on_warn=fail_on_warn)


def _run_build(
    *,
    root: Path,
    execplans_dir: Path,
    output_path: Path,
    include_timestamp: bool,
    fail_on_warn: bool,
) -> tuple[RegistryBuildResult, int]:
    result = build_execplan_registry(
        root=root,
        execplans_dir=execplans_dir,
        output_path=output_path,
        include_timestamp=include_timestamp,
        fail_on_warn=fail_on_warn,
    )
    return result, _exit_code_for_result(result, fail_on_warn=fail_on_warn)


def _shared_options() -> tuple[Any, Any, Any, Any]:
    return (
        typer.Option(
            None,
            "--root",
            help="Repository root directory. Defaults to current working directory.",
        ),
        typer.Option(
            DEFAULT_EXECPLANS_DIR,
            "--execplans-dir",
            help="Path to ExecPlans directory (relative to --root unless absolute).",
        ),
        typer.Option(
            DEFAULT_REGISTRY_PATH,
            "--out",
            help="Path to registry.json output (relative to --root unless absolute).",
        ),
        typer.Option(
            False,
            "--timestamp",
            help="Include generated_at timestamp in registry output.",
        ),
    )


def register(app: typer.Typer) -> None:
    """Register the `execplan-registry` command group."""

    registry_app = typer.Typer(help="Build and validate .agent/exec_plans/registry.json.")
    app.add_typer(registry_app, name="execplan-registry")

    ROOT_OPTION, EXECPLANS_DIR_OPTION, OUT_OPTION, TIMESTAMP_OPTION = _shared_options()

    @registry_app.command("check")
    def check_registry(  # type: ignore[func-returns-value]
        root: Path | None = ROOT_OPTION,
        execplans_dir: Path = EXECPLANS_DIR_OPTION,
        timestamp: bool = TIMESTAMP_OPTION,
        fail_on_warn: bool = typer.Option(
            False,
            "--fail-on-warn",
            help="Return non-zero when warnings are present.",
        ),
    ) -> None:
        context = bootstrap_runtime()
        console = context.console

        resolved_root = (root or Path.cwd()).resolve()
        resolved_execplans_dir = _resolve_path(resolved_root, execplans_dir)

        try:
            result, exit_code = _run_check(
                root=resolved_root,
                execplans_dir=resolved_execplans_dir,
                include_timestamp=timestamp,
                fail_on_warn=fail_on_warn,
            )
        except FileNotFoundError as error:
            console.print(f"[red]{error}[/]")
            raise typer.Exit(2) from error

        _print_issues(result, console=console)
        if exit_code == 0:
            console.print(
                f"[green]Registry check passed:[/] {len(result.registry.get('plans', []))} ExecPlans discovered."
            )
        else:
            console.print(
                "[red]Registry check failed.[/] "
                f"errors={result.error_count}, warnings={result.warning_count}"
            )
        raise typer.Exit(exit_code)

    @registry_app.command("build")
    def build_registry(  # type: ignore[func-returns-value]
        root: Path | None = ROOT_OPTION,
        execplans_dir: Path = EXECPLANS_DIR_OPTION,
        out: Path = OUT_OPTION,
        timestamp: bool = TIMESTAMP_OPTION,
        fail_on_warn: bool = typer.Option(
            False,
            "--fail-on-warn",
            help="Do not write registry when warnings are present.",
        ),
    ) -> None:
        context = bootstrap_runtime()
        console = context.console

        resolved_root = (root or Path.cwd()).resolve()
        resolved_execplans_dir = _resolve_path(resolved_root, execplans_dir)
        resolved_output = _resolve_path(resolved_root, out)

        try:
            result, exit_code = _run_build(
                root=resolved_root,
                execplans_dir=resolved_execplans_dir,
                output_path=resolved_output,
                include_timestamp=timestamp,
                fail_on_warn=fail_on_warn,
            )
        except FileNotFoundError as error:
            console.print(f"[red]{error}[/]")
            raise typer.Exit(2) from error
        except OSError as error:
            console.print(f"[red]Registry build failed due to filesystem error: {error}[/]")
            raise typer.Exit(2) from error

        _print_issues(result, console=console)
        if exit_code == 0 and result.wrote_registry and result.output_path is not None:
            console.print(
                f"[green]Wrote registry:[/] {result.output_path.as_posix()} "
                f"({len(result.registry.get('plans', []))} plans)"
            )
        else:
            console.print(
                "[red]Registry build failed.[/] "
                f"errors={result.error_count}, warnings={result.warning_count}"
            )
        raise typer.Exit(exit_code)

    @registry_app.command("update")
    def update_registry(  # type: ignore[func-returns-value]
        root: Path | None = ROOT_OPTION,
        execplans_dir: Path = EXECPLANS_DIR_OPTION,
        out: Path = OUT_OPTION,
        timestamp: bool = TIMESTAMP_OPTION,
        fail_on_warn: bool = typer.Option(
            False,
            "--fail-on-warn",
            help="Do not write registry when warnings are present.",
        ),
    ) -> None:
        """Alias for `build`."""
        context = bootstrap_runtime()
        console = context.console

        resolved_root = (root or Path.cwd()).resolve()
        resolved_execplans_dir = _resolve_path(resolved_root, execplans_dir)
        resolved_output = _resolve_path(resolved_root, out)

        try:
            result, exit_code = _run_build(
                root=resolved_root,
                execplans_dir=resolved_execplans_dir,
                output_path=resolved_output,
                include_timestamp=timestamp,
                fail_on_warn=fail_on_warn,
            )
        except FileNotFoundError as error:
            console.print(f"[red]{error}[/]")
            raise typer.Exit(2) from error
        except OSError as error:
            console.print(f"[red]Registry update failed due to filesystem error: {error}[/]")
            raise typer.Exit(2) from error

        _print_issues(result, console=console)
        if exit_code == 0 and result.wrote_registry and result.output_path is not None:
            console.print(
                f"[green]Updated registry:[/] {result.output_path.as_posix()} "
                f"({len(result.registry.get('plans', []))} plans)"
            )
        else:
            console.print(
                "[red]Registry update failed.[/] "
                f"errors={result.error_count}, warnings={result.warning_count}"
            )
        raise typer.Exit(exit_code)
