"""Implementation of the `execplan` command group."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import typer

from agentrules.core.execplan.creator import archive_execplan, create_execplan
from agentrules.core.execplan.milestones import (
    archive_execplan_milestone,
    create_execplan_milestone,
    list_execplan_milestones,
)
from agentrules.core.execplan.paths import ARCHIVE_DIR, COMPLETE_DIR, EXECPLAN_ARCHIVE_DIR, EXECPLAN_COMPLETE_DIR
from agentrules.core.execplan.registry import (
    DEFAULT_EXECPLANS_DIR,
    DEFAULT_REGISTRY_PATH,
    collect_execplan_registry,
    list_active_execplan_summaries,
    summarize_registry_activity,
)

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
ARCHIVE_DATE_OPTION = typer.Option(
    None,
    "--date",
    metavar="YYYYMMDD",
    help="Override completion date token used in destination path and metadata update.",
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
    help="Update .agent/exec_plans/registry.json after the command completes.",
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
MILESTONE_NEW_MS_OPTION = typer.Option(
    None,
    "--ms",
    min=1,
    max=999,
    help="Optional milestone sequence number (MS###). Defaults to automatic assignment.",
)
MILESTONE_MS_OPTION = typer.Option(
    ...,
    "--ms",
    min=1,
    max=999,
    help="Milestone sequence number (MS###) to complete.",
)
MILESTONE_INCLUDE_ARCHIVED_OPTION = typer.Option(
    True,
    "--archived/--active-only",
    help="Include completed milestones in list output. Legacy option name retained for compatibility.",
)
PLAN_LIST_INCLUDE_PATH_OPTION = typer.Option(
    False,
    "--path/--no-path",
    help="Include ExecPlan file path in list output.",
)
MILESTONE_REMAINING_INCLUDE_PATH_OPTION = typer.Option(
    False,
    "--path/--no-path",
    help="Include milestone file path in remaining output.",
)


def _resolve_path(root: Path, value: Path) -> Path:
    return value.resolve() if value.is_absolute() else (root / value).resolve()


def _count_active_execplans(
    *,
    root: Path,
    execplans_dir: Path,
    registry: dict[str, Any] | None = None,
) -> int:
    if registry is None:
        collected = collect_execplan_registry(root=root, execplans_dir=execplans_dir)
        registry = collected.registry
    summary = summarize_registry_activity(
        registry=registry,
        root=root,
        execplans_dir=execplans_dir,
    )
    return summary.active_execplans


def _format_milestone_progress(*, active_milestones: int, total_milestones: int) -> str:
    if total_milestones <= 0:
        return "milestones none"
    completed = total_milestones - active_milestones
    return f"milestones {completed}/{total_milestones} completed"


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

    def _complete_or_archive_execplan(  # type: ignore[func-returns-value]
        *,
        destination_dir: Literal["complete", "archive"],
        execplan_id: str = EXECPLAN_ID_ARGUMENT,
        root: Path | None = ROOT_OPTION,
        execplans_dir: Path = EXECPLANS_DIR_OPTION,
        date: str | None = ARCHIVE_DATE_OPTION,
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
            result = archive_execplan(
                root=resolved_root,
                execplan_id=execplan_id.strip(),
                execplans_dir=resolved_execplans_dir,
                archive_date_yyyymmdd=date,
                destination_dir=destination_dir,
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
            console.print(f"[red]ExecPlan completion failed due to filesystem error: {error}[/]")
            raise typer.Exit(2) from error

        console.print(f"[green]Completed ExecPlan:[/] {result.plan_id}")
        console.print(f"[green]From:[/] {result.source_plan_root.as_posix()}")
        console.print(f"[green]To:[/] {result.archived_plan_root.as_posix()}")
        active_count = _count_active_execplans(
            root=resolved_root,
            execplans_dir=resolved_execplans_dir,
            registry=result.registry_result.registry if result.registry_result is not None else None,
        )
        if active_count == 0:
            console.print("[green]Active ExecPlans:[/] none")
        else:
            console.print(f"[green]Active ExecPlans:[/] {active_count}")

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

    @execplan_app.command("complete")
    def complete_existing_execplan(  # type: ignore[func-returns-value]
        execplan_id: str = EXECPLAN_ID_ARGUMENT,
        root: Path | None = ROOT_OPTION,
        execplans_dir: Path = EXECPLANS_DIR_OPTION,
        date: str | None = ARCHIVE_DATE_OPTION,
        out: Path = OUT_OPTION,
        update_registry: bool = UPDATE_REGISTRY_OPTION,
        fail_on_registry_warn: bool = FAIL_ON_REGISTRY_WARN_OPTION,
        registry_timestamp: bool = REGISTRY_TIMESTAMP_OPTION,
    ) -> None:
        _complete_or_archive_execplan(
            destination_dir=EXECPLAN_COMPLETE_DIR,
            execplan_id=execplan_id,
            root=root,
            execplans_dir=execplans_dir,
            date=date,
            out=out,
            update_registry=update_registry,
            fail_on_registry_warn=fail_on_registry_warn,
            registry_timestamp=registry_timestamp,
        )

    @execplan_app.command("archive")
    def archive_existing_execplan(  # type: ignore[func-returns-value]
        execplan_id: str = EXECPLAN_ID_ARGUMENT,
        root: Path | None = ROOT_OPTION,
        execplans_dir: Path = EXECPLANS_DIR_OPTION,
        date: str | None = ARCHIVE_DATE_OPTION,
        out: Path = OUT_OPTION,
        update_registry: bool = UPDATE_REGISTRY_OPTION,
        fail_on_registry_warn: bool = FAIL_ON_REGISTRY_WARN_OPTION,
        registry_timestamp: bool = REGISTRY_TIMESTAMP_OPTION,
    ) -> None:
        _complete_or_archive_execplan(
            destination_dir=EXECPLAN_ARCHIVE_DIR,
            execplan_id=execplan_id,
            root=root,
            execplans_dir=execplans_dir,
            date=date,
            out=out,
            update_registry=update_registry,
            fail_on_registry_warn=fail_on_registry_warn,
            registry_timestamp=registry_timestamp,
        )

    @execplan_app.command("list")
    def list_execplans(  # type: ignore[func-returns-value]
        root: Path | None = ROOT_OPTION,
        execplans_dir: Path = EXECPLANS_DIR_OPTION,
        include_path: bool = PLAN_LIST_INCLUDE_PATH_OPTION,
    ) -> None:
        context = bootstrap_runtime()
        console = context.console

        resolved_root = (root or Path.cwd()).resolve()
        resolved_execplans_dir = _resolve_path(resolved_root, execplans_dir)

        try:
            collected = collect_execplan_registry(
                root=resolved_root,
                execplans_dir=resolved_execplans_dir,
            )
        except FileNotFoundError as error:
            raise typer.BadParameter(str(error)) from error

        if collected.error_count > 0:
            console.print(
                "[red]Cannot list ExecPlans due to registry validation errors.[/] "
                "Run `execplan-registry check` for details."
            )
            raise typer.Exit(2)

        if collected.warning_count > 0:
            console.print(
                "[yellow]Registry warnings detected; listing active plans from valid entries.[/] "
                "Run `execplan-registry check` for details."
            )

        summaries = list_active_execplan_summaries(
            registry=collected.registry,
            root=resolved_root,
            execplans_dir=resolved_execplans_dir,
        )
        if not summaries:
            console.print("[yellow]No active ExecPlans found.[/]")
            raise typer.Exit(0)

        total_milestones = sum(summary.total_milestones for summary in summaries)
        active_milestones = sum(summary.active_milestones for summary in summaries)
        overall_progress = _format_milestone_progress(
            active_milestones=active_milestones,
            total_milestones=total_milestones,
        )
        console.print(f"[green]Active ExecPlans:[/] {len(summaries)} ({overall_progress})")

        for summary in summaries:
            per_plan_progress = _format_milestone_progress(
                active_milestones=summary.active_milestones,
                total_milestones=summary.total_milestones,
            )
            line = (
                f"{summary.id} [{summary.status}] {summary.title} "
                f"({per_plan_progress})"
            )
            if include_path:
                line += f" -> {summary.path}"
            console.print(line, markup=False, soft_wrap=True)
        raise typer.Exit(0)

    @milestone_app.command("new")
    def create_new_milestone(  # type: ignore[func-returns-value]
        execplan_id: str = EXECPLAN_ID_ARGUMENT,
        title: str = MILESTONE_TITLE_ARGUMENT,
        root: Path | None = ROOT_OPTION,
        execplans_dir: Path = EXECPLANS_DIR_OPTION,
        slug: str | None = MILESTONE_SLUG_OPTION,
        owner: str | None = MILESTONE_OWNER_OPTION,
        domain: str | None = MILESTONE_DOMAIN_OPTION,
        ms: int | None = MILESTONE_NEW_MS_OPTION,
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
                sequence=ms,
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
            status = "[green]active[/]" if milestone.location == "active" else "[yellow]completed[/]"
            console.print(f"{status} {milestone.milestone_id} -> {milestone.path.as_posix()}")
        raise typer.Exit(0)

    def _complete_or_archive_milestone(  # type: ignore[func-returns-value]
        *,
        destination_dir: Literal["complete", "archive"],
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
                destination_dir=destination_dir,
            )
        except (ValueError, FileNotFoundError) as error:
            raise typer.BadParameter(str(error)) from error
        except FileExistsError as error:
            console.print(f"[red]{error}[/]")
            raise typer.Exit(2) from error
        except OSError as error:
            console.print(f"[red]Milestone completion failed due to filesystem error: {error}[/]")
            raise typer.Exit(2) from error

        console.print(f"[green]Completed milestone:[/] {result.milestone_id}")
        console.print(f"[green]From:[/] {result.source_path.as_posix()}")
        console.print(f"[green]To:[/] {result.archived_path.as_posix()}")
        raise typer.Exit(0)

    @milestone_app.command("complete")
    def complete_milestone(  # type: ignore[func-returns-value]
        execplan_id: str = EXECPLAN_ID_ARGUMENT,
        root: Path | None = ROOT_OPTION,
        execplans_dir: Path = EXECPLANS_DIR_OPTION,
        ms: int = MILESTONE_MS_OPTION,
    ) -> None:
        _complete_or_archive_milestone(
            destination_dir=COMPLETE_DIR,
            execplan_id=execplan_id,
            root=root,
            execplans_dir=execplans_dir,
            ms=ms,
        )

    @milestone_app.command("archive")
    def archive_milestone(  # type: ignore[func-returns-value]
        execplan_id: str = EXECPLAN_ID_ARGUMENT,
        root: Path | None = ROOT_OPTION,
        execplans_dir: Path = EXECPLANS_DIR_OPTION,
        ms: int = MILESTONE_MS_OPTION,
    ) -> None:
        _complete_or_archive_milestone(
            destination_dir=ARCHIVE_DIR,
            execplan_id=execplan_id,
            root=root,
            execplans_dir=execplans_dir,
            ms=ms,
        )

    @milestone_app.command("remaining")
    def list_remaining_milestones(  # type: ignore[func-returns-value]
        execplan_id: str = EXECPLAN_ID_ARGUMENT,
        root: Path | None = ROOT_OPTION,
        execplans_dir: Path = EXECPLANS_DIR_OPTION,
        include_path: bool = MILESTONE_REMAINING_INCLUDE_PATH_OPTION,
    ) -> None:
        context = bootstrap_runtime()
        console = context.console

        normalized_execplan_id = execplan_id.strip()
        resolved_root = (root or Path.cwd()).resolve()
        resolved_execplans_dir = _resolve_path(resolved_root, execplans_dir)

        try:
            milestones = list_execplan_milestones(
                root=resolved_root,
                execplan_id=normalized_execplan_id,
                execplans_dir=resolved_execplans_dir,
                include_archived=False,
            )
        except (ValueError, FileNotFoundError) as error:
            raise typer.BadParameter(str(error)) from error

        if not milestones:
            console.print(f"[green]No active milestones remaining for {normalized_execplan_id}.[/]")
            raise typer.Exit(0)

        console.print(f"[green]Remaining milestones for {normalized_execplan_id}:[/] {len(milestones)}")
        for milestone in milestones:
            if include_path:
                console.print(f"{milestone.milestone_id} -> {milestone.path.as_posix()}")
            else:
                console.print(milestone.milestone_id)
        raise typer.Exit(0)
