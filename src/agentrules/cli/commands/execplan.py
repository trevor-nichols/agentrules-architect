"""Implementation of the `execplan` command group."""

from __future__ import annotations

from pathlib import Path

import typer

from agentrules.core.execplan.creator import create_execplan
from agentrules.core.execplan.milestones import (
    archive_execplan_milestone,
    create_execplan_milestone,
    list_execplan_milestones,
)
from agentrules.core.execplan.registry import DEFAULT_EXECPLANS_DIR, DEFAULT_REGISTRY_PATH

from ..bootstrap import bootstrap_runtime

TITLE_ARGUMENT = typer.Argument(..., help="Human-readable ExecPlan title.")
EXECPLAN_ID_ARGUMENT = typer.Argument(..., help="Canonical ExecPlan ID (EP-YYYYMMDD-NNN).")
MILESTONE_TITLE_ARGUMENT = typer.Argument(..., help="Human-readable milestone title.")
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
MILESTONE_SLUG_OPTION = typer.Option(
    None,
    "--slug",
    help="Optional milestone slug. Defaults to a slugified milestone title.",
)
MILESTONE_OWNER_OPTION = typer.Option(
    None,
    "--owner",
    help="Override milestone owner metadata. Defaults to parent ExecPlan owner.",
)
MILESTONE_DOMAIN_OPTION = typer.Option(
    None,
    "--domain",
    help="Override milestone domain metadata. Defaults to parent ExecPlan domain.",
)
MILESTONE_MS_OPTION = typer.Option(
    ...,
    "--ms",
    min=1,
    max=999,
    help="Milestone sequence number (MS###) to archive.",
)
MILESTONE_INCLUDE_ARCHIVED_OPTION = typer.Option(
    True,
    "--archived/--active-only",
    help="Include archived milestones in list output.",
)


def _resolve_path(root: Path, value: Path) -> Path:
    return value.resolve() if value.is_absolute() else (root / value).resolve()


def register(app: typer.Typer) -> None:
    """Register the `execplan` command group."""

    execplan_app = typer.Typer(help="Create and manage ExecPlan documents.")
    app.add_typer(execplan_app, name="execplan")
    milestone_app = typer.Typer(help="Create and manage milestones for a specific ExecPlan.")
    execplan_app.add_typer(milestone_app, name="milestone")

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

    @milestone_app.command("new")
    def create_new_milestone(  # type: ignore[func-returns-value]
        execplan_id: str = EXECPLAN_ID_ARGUMENT,
        title: str = MILESTONE_TITLE_ARGUMENT,
        root: Path | None = ROOT_OPTION,
        execplans_dir: Path = EXECPLANS_DIR_OPTION,
        slug: str | None = MILESTONE_SLUG_OPTION,
        owner: str | None = MILESTONE_OWNER_OPTION,
        domain: str | None = MILESTONE_DOMAIN_OPTION,
    ) -> None:
        context = bootstrap_runtime()
        console = context.console

        resolved_root = (root or Path.cwd()).resolve()
        resolved_execplans_dir = _resolve_path(resolved_root, execplans_dir)

        try:
            result = create_execplan_milestone(
                root=resolved_root,
                execplan_id=execplan_id.strip(),
                title=title,
                slug=slug,
                owner=owner,
                domain=domain,
                execplans_dir=resolved_execplans_dir,
            )
        except (ValueError, FileNotFoundError) as error:
            raise typer.BadParameter(str(error)) from error
        except FileExistsError as error:
            console.print(f"[red]{error}[/]")
            raise typer.Exit(2) from error
        except OSError as error:
            console.print(f"[red]Milestone creation failed due to filesystem error: {error}[/]")
            raise typer.Exit(2) from error

        console.print(f"[green]Created milestone:[/] {result.milestone_path.as_posix()}")
        console.print(f"[green]Milestone ID:[/] {result.milestone_id}")
        raise typer.Exit(0)

    @milestone_app.command("list")
    def list_milestones(  # type: ignore[func-returns-value]
        execplan_id: str = EXECPLAN_ID_ARGUMENT,
        root: Path | None = ROOT_OPTION,
        execplans_dir: Path = EXECPLANS_DIR_OPTION,
        include_archived: bool = MILESTONE_INCLUDE_ARCHIVED_OPTION,
    ) -> None:
        context = bootstrap_runtime()
        console = context.console

        resolved_root = (root or Path.cwd()).resolve()
        resolved_execplans_dir = _resolve_path(resolved_root, execplans_dir)

        try:
            milestones = list_execplan_milestones(
                root=resolved_root,
                execplan_id=execplan_id.strip(),
                execplans_dir=resolved_execplans_dir,
                include_archived=include_archived,
            )
        except (ValueError, FileNotFoundError) as error:
            raise typer.BadParameter(str(error)) from error

        if not milestones:
            console.print(f"[yellow]No milestones found for {execplan_id.strip()}.[/]")
            raise typer.Exit(0)

        for milestone in milestones:
            status = "[green]active[/]" if milestone.location == "active" else "[yellow]archived[/]"
            console.print(f"{status} {milestone.milestone_id} -> {milestone.path.as_posix()}")
        raise typer.Exit(0)

    @milestone_app.command("archive")
    def archive_milestone(  # type: ignore[func-returns-value]
        execplan_id: str = EXECPLAN_ID_ARGUMENT,
        root: Path | None = ROOT_OPTION,
        execplans_dir: Path = EXECPLANS_DIR_OPTION,
        ms: int = MILESTONE_MS_OPTION,
    ) -> None:
        context = bootstrap_runtime()
        console = context.console

        resolved_root = (root or Path.cwd()).resolve()
        resolved_execplans_dir = _resolve_path(resolved_root, execplans_dir)

        try:
            result = archive_execplan_milestone(
                root=resolved_root,
                execplan_id=execplan_id.strip(),
                sequence=ms,
                execplans_dir=resolved_execplans_dir,
            )
        except (ValueError, FileNotFoundError) as error:
            raise typer.BadParameter(str(error)) from error
        except FileExistsError as error:
            console.print(f"[red]{error}[/]")
            raise typer.Exit(2) from error
        except OSError as error:
            console.print(f"[red]Milestone archive failed due to filesystem error: {error}[/]")
            raise typer.Exit(2) from error

        console.print(f"[green]Archived milestone:[/] {result.milestone_id}")
        console.print(f"[green]From:[/] {result.source_path.as_posix()}")
        console.print(f"[green]To:[/] {result.archived_path.as_posix()}")
        raise typer.Exit(0)
