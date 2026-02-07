"""Implementation of the `execplan` command group."""

from __future__ import annotations

from pathlib import Path

import typer

from agentrules.core.utils.execplan_creator import create_execplan
from agentrules.core.utils.execplan_registry import DEFAULT_EXECPLANS_DIR, DEFAULT_REGISTRY_PATH

from ..bootstrap import bootstrap_runtime

TITLE_ARGUMENT = typer.Argument(..., help="Human-readable ExecPlan title.")
ROOT_OPTION = typer.Option(
    None,
    "--root",
    help="Repository root directory. Defaults to current working directory.",
)
SLUG_OPTION = typer.Option(
    None,
    "--slug",
    help="Optional directory/file slug. Defaults to a slugified title.",
)
OWNER_OPTION = typer.Option("@codex", "--owner", help="ExecPlan owner metadata.")
KIND_OPTION = typer.Option("feature", "--kind", help="ExecPlan kind metadata.")
DOMAIN_OPTION = typer.Option("backend", "--domain", help="ExecPlan domain metadata.")
DATE_OPTION = typer.Option(
    None,
    "--date",
    metavar="YYYYMMDD",
    help="Override date token used in ExecPlan ID generation.",
)
EXECPLANS_DIR_OPTION = typer.Option(
    DEFAULT_EXECPLANS_DIR,
    "--execplans-dir",
    help="Path to ExecPlans directory (relative to --root unless absolute).",
)
OUT_OPTION = typer.Option(
    DEFAULT_REGISTRY_PATH,
    "--out",
    help="Path to registry output (relative to --root unless absolute).",
)
UPDATE_REGISTRY_OPTION = typer.Option(
    True,
    "--update-registry/--no-update-registry",
    help="Update .agent/exec_plans/registry.json after creating the plan.",
)
FAIL_ON_REGISTRY_WARN_OPTION = typer.Option(
    False,
    "--fail-on-registry-warn",
    help="Treat registry warnings as blocking when updating registry.",
)
REGISTRY_TIMESTAMP_OPTION = typer.Option(
    False,
    "--registry-timestamp",
    help="Include generated_at timestamp when refreshing registry.",
)


def _resolve_path(root: Path, value: Path) -> Path:
    return value.resolve() if value.is_absolute() else (root / value).resolve()


def register(app: typer.Typer) -> None:
    """Register the `execplan` command group."""

    execplan_app = typer.Typer(help="Create and manage ExecPlan documents.")
    app.add_typer(execplan_app, name="execplan")

    @execplan_app.command("new")
    def create_new_execplan(  # type: ignore[func-returns-value]
        title: str = TITLE_ARGUMENT,
        root: Path | None = ROOT_OPTION,
        slug: str | None = SLUG_OPTION,
        owner: str = OWNER_OPTION,
        kind: str = KIND_OPTION,
        domain: str = DOMAIN_OPTION,
        date: str | None = DATE_OPTION,
        execplans_dir: Path = EXECPLANS_DIR_OPTION,
        out: Path = OUT_OPTION,
        update_registry: bool = UPDATE_REGISTRY_OPTION,
        fail_on_registry_warn: bool = FAIL_ON_REGISTRY_WARN_OPTION,
        registry_timestamp: bool = REGISTRY_TIMESTAMP_OPTION,
    ) -> None:
        context = bootstrap_runtime()
        console = context.console

        resolved_root = (root or Path.cwd()).resolve()
        resolved_execplans_dir = _resolve_path(resolved_root, execplans_dir)
        resolved_registry = _resolve_path(resolved_root, out)

        try:
            result = create_execplan(
                root=resolved_root,
                title=title,
                slug=slug,
                owner=owner,
                kind=kind,
                domain=domain,
                date_yyyymmdd=date,
                execplans_dir=resolved_execplans_dir,
                update_registry=update_registry,
                registry_path=resolved_registry,
                include_registry_timestamp=registry_timestamp,
                fail_on_registry_warn=fail_on_registry_warn,
            )
        except (ValueError, FileNotFoundError) as error:
            raise typer.BadParameter(str(error)) from error
        except FileExistsError as error:
            console.print(f"[red]{error}[/]")
            raise typer.Exit(2) from error
        except OSError as error:
            console.print(f"[red]ExecPlan creation failed due to filesystem error: {error}[/]")
            raise typer.Exit(2) from error

        created_path = result.plan_path.as_posix()
        console.print(f"[green]Created ExecPlan:[/] {created_path}")
        console.print(f"[green]ExecPlan ID:[/] {result.plan_id}")

        registry_result = result.registry_result
        if not update_registry or registry_result is None:
            raise typer.Exit(0)

        for issue in registry_result.issues:
            prefix = "[yellow]WARNING[/]" if issue.severity == "warning" else "[red]ERROR[/]"
            if issue.path:
                console.print(f"{prefix} {issue.path}: {issue.message}")
            else:
                console.print(f"{prefix} {issue.message}")

        if registry_result.wrote_registry and registry_result.output_path is not None:
            console.print(f"[green]Updated registry:[/] {registry_result.output_path.as_posix()}")
            raise typer.Exit(0)

        if registry_result.error_count > 0:
            console.print(
                "[red]Registry update failed.[/] "
                f"errors={registry_result.error_count}, warnings={registry_result.warning_count}"
            )
            raise typer.Exit(1)

        if fail_on_registry_warn and registry_result.warning_count > 0:
            console.print(
                "[yellow]Registry not written due to warnings.[/] "
                f"errors={registry_result.error_count}, warnings={registry_result.warning_count}"
            )
            raise typer.Exit(1)

        console.print("[yellow]Registry was not updated.[/]")
        raise typer.Exit(1)
