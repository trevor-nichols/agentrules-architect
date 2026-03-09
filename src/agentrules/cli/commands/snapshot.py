"""Implementation of the `snapshot` command group."""

from __future__ import annotations

import os
from pathlib import Path

import typer

from agentrules.core.configuration import get_config_manager
from agentrules.core.utils.file_creation.snapshot_artifact import sync_snapshot_artifact
from agentrules.core.utils.file_creation.snapshot_policy import build_snapshot_additional_exclude_paths
from agentrules.core.utils.file_system.gitignore import load_gitignore_spec

from ..bootstrap import bootstrap_runtime
from ..services.output_validation import (
    validate_pipeline_output_filenames,
)


def _validate_filename(ctx: typer.Context, param: typer.CallbackParam, value: str | None) -> str | None:
    if value is None:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    if "/" in candidate or "\\" in candidate:
        raise typer.BadParameter("must be a file name, not a path", ctx=ctx, param=param)
    return candidate


def _validate_positive(ctx: typer.Context, param: typer.CallbackParam, value: int | None) -> int | None:
    if value is None:
        return None
    if value < 1:
        raise typer.BadParameter("must be greater than zero", ctx=ctx, param=param)
    return value


PATH_ARGUMENT = typer.Argument(
    Path.cwd(),
    exists=True,
    dir_okay=True,
    file_okay=False,
    resolve_path=True,
)
FILENAME_OPTION = typer.Option(
    None,
    "--filename",
    "-f",
    help="Snapshot filename to write (defaults to configured value).",
    callback=_validate_filename,
)
MAX_DEPTH_OPTION = typer.Option(
    None,
    "--max-depth",
    "-d",
    help="Maximum directory depth to include in the snapshot tree.",
    callback=_validate_positive,
)
DRY_RUN_OPTION = typer.Option(
    False,
    "--dry-run",
    help="Preview changes without writing the snapshot file.",
)


def _find_snapshot_files(path: Path, filename: str) -> list[Path]:
    matches: list[Path] = []
    for root, _dirs, files in os.walk(path, followlinks=False):
        if filename in files:
            matches.append(Path(root) / filename)
    return sorted(matches)


def _run_snapshot_generation(
    *,
    path: Path,
    filename: str | None,
    max_depth: int | None,
    dry_run: bool,
    mode: str,
) -> None:
    context = bootstrap_runtime()
    console = context.console
    config_manager = get_config_manager()

    snapshot_filename = filename or config_manager.get_snapshot_filename()
    rules_filename = config_manager.resolve_rules_filename()
    tree_depth = max_depth if max_depth is not None else config_manager.get_tree_max_depth()

    try:
        validate_pipeline_output_filenames(
            target_directory=path,
            rules_filename=rules_filename,
            snapshot_filename=snapshot_filename,
            generate_snapshot=True,
        )
    except ValueError as error:
        console.print(f"[red]Invalid output configuration:[/] {error}")
        console.print(
            f"[dim]Current values: rules={rules_filename}, snapshot={snapshot_filename}[/]"
        )
        raise typer.Exit(2) from error

    exclude_dirs, exclude_files, exclude_exts = config_manager.get_effective_exclusions()
    gitignore_spec = None
    if config_manager.should_respect_gitignore():
        loaded = load_gitignore_spec(path)
        if loaded:
            gitignore_spec = loaded.spec

    try:
        result = sync_snapshot_artifact(
            path,
            output_path=path / snapshot_filename,
            tree_max_depth=tree_depth,
            exclude_dirs=exclude_dirs,
            exclude_files=exclude_files,
            exclude_extensions=exclude_exts,
            gitignore_spec=gitignore_spec,
            include_file_contents=True,
            additional_exclude_relative_paths=build_snapshot_additional_exclude_paths(
                rules_filename,
                snapshot_filename,
            ),
            write=not dry_run,
        )
    except (OSError, ValueError) as error:
        console.print(f"[red]Snapshot {mode} failed:[/] {error}")
        raise typer.Exit(2) from error

    if not result.changed:
        if mode == "generate":
            console.print(f"[dim]Snapshot already up-to-date:[/] {result.output_path}")
        else:
            console.print(f"[dim]No snapshot updates needed:[/] {result.output_path}")
        raise typer.Exit(0)

    if mode == "generate":
        status = "would be generated" if dry_run else "generated"
    else:
        status = "would be updated" if dry_run else "updated"
    updated_paths = len(result.added_paths) + len(result.removed_paths)
    console.print(
        f"[green]Snapshot {status}:[/] {result.output_path} "
        f"([bold]{updated_paths}[/] path{'s' if updated_paths != 1 else ''} changed)"
    )
    if dry_run:
        console.print("[dim]Dry run only: no files were written.[/]")


def register(app: typer.Typer) -> None:
    """Register the `snapshot` command group."""

    snapshot_app = typer.Typer(help="Create and maintain SNAPSHOT artifacts.")
    app.add_typer(snapshot_app, name="snapshot")

    @snapshot_app.command("find")
    def find(  # type: ignore[func-returns-value]
        path: Path = PATH_ARGUMENT,
        filename: str | None = FILENAME_OPTION,
    ) -> None:
        """Locate snapshot artifacts recursively under a directory."""

        context = bootstrap_runtime()
        console = context.console
        config_manager = get_config_manager()
        snapshot_filename = filename or config_manager.get_snapshot_filename()

        matches = _find_snapshot_files(path, snapshot_filename)
        if not matches:
            console.print(f"[dim]No {snapshot_filename} files found under:[/] {path}")
            raise typer.Exit(0)

        count = len(matches)
        console.print(
            f"[green]Found {count} {snapshot_filename} file{'s' if count != 1 else ''} under:[/] {path}"
        )
        for match in matches:
            rel_path = match.relative_to(path).as_posix()
            console.print(f"[green]-[/] {rel_path}")

    @snapshot_app.command("generate")
    def generate(  # type: ignore[func-returns-value]
        path: Path = PATH_ARGUMENT,
        filename: str | None = FILENAME_OPTION,
        max_depth: int | None = MAX_DEPTH_OPTION,
        dry_run: bool = DRY_RUN_OPTION,
    ) -> None:
        """Generate SNAPSHOT.md (or configured filename) for a directory."""

        _run_snapshot_generation(
            path=path,
            filename=filename,
            max_depth=max_depth,
            dry_run=dry_run,
            mode="generate",
        )

    @snapshot_app.command("sync")
    def sync(  # type: ignore[func-returns-value]
        path: Path = PATH_ARGUMENT,
        filename: str | None = FILENAME_OPTION,
        max_depth: int | None = MAX_DEPTH_OPTION,
        dry_run: bool = DRY_RUN_OPTION,
    ) -> None:
        """Update/sync snapshot artifact while preserving inline tree comments."""

        _run_snapshot_generation(
            path=path,
            filename=filename,
            max_depth=max_depth,
            dry_run=dry_run,
            mode="sync",
        )
