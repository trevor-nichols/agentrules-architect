"""Rich-based helpers for rendering phase progress during analysis runs."""

from __future__ import annotations

from collections.abc import Awaitable, Iterable, Sequence
from typing import Any, TypeVar

from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TaskID, TextColumn
from rich.table import Table
from rich.text import Text

T = TypeVar("T")


class AnalysisView:
    """Presentational utilities for the multi-phase analysis experience."""

    def __init__(self, console: Console):
        self.console = console
        self._phase_index = 0
        self._agent_progress: dict[str, _AgentProgress] = {}
        self._progress_phases: set[str] = set()

    def _indent(self, renderable: Any, level: int = 1) -> Padding:
        return Padding(renderable, (0, 0, 0, level * 2))

    def render_phase_header(self, title: str, color: str, subtitle: str | None = None) -> None:
        if self._phase_index > 0:
            self.console.print()
        header_panel = Panel.fit(
            Text(title, style=f"bold {color}"),
            border_style=color,
            padding=(0, 2),
        )
        self.console.print(header_panel)
        if subtitle:
            self.console.print(self._indent(Text(subtitle, style="dim")))
        self._phase_index += 1

    def render_agent_overview(self, agents: Iterable[str], color: str, title: str = "Agents") -> None:
        agent_list = list(agents)
        if not agent_list:
            return

        table = Table.grid(padding=(0, 1))
        table.add_column(style="dim")
        table.add_column()
        table.add_row("", Text(title, style=f"bold {color}"))
        for agent in agent_list:
            table.add_row("•", Text(agent, style="white"))
        self.console.print(self._indent(table))

    def render_agent_plan(
        self,
        agents: Sequence[dict[str, Any]],
        color: str,
        heading: str = "Planned agents",
    ) -> None:
        if not agents:
            return

        table = Table.grid(padding=(0, 1))
        table.add_column(style="dim")
        table.add_column()
        table.add_row("", Text(heading, style=f"bold {color}"))
        for agent in agents:
            name = agent.get("name") or "Unnamed Agent"
            files = agent.get("file_assignments") or []
            file_count = len(files)
            if file_count:
                description = f"{name} — {file_count} file{'s' if file_count != 1 else ''}"
            else:
                description = name
            table.add_row("•", Text(description, style="white"))
        self.console.print(self._indent(table))

    def render_note(self, message: str, style: str = "dim", level: int = 1) -> None:
        self.console.print(self._indent(Text(message, style=style), level=level))

    def render_completion(self, message: str, color: str) -> None:
        check = Text("✓", style=f"bold {color}")
        line = Text.assemble(check, " ", Text(message, style=f"{color}"))
        self.console.print(self._indent(line))

    def start_agent_progress(self, phase: str, agents: Sequence[dict[str, Any]], color: str) -> None:
        board = self._agent_progress.pop(phase, None)
        if board:
            board.stop()
        board = _AgentProgress(self.console, color)
        board.start(agents)
        self._agent_progress[phase] = board
        self._progress_phases.add(phase)

    def update_agent_progress(
        self,
        phase: str,
        agent_id: str,
        agent_name: str,
        status: str,
        icon: str,
        icon_color: str,
        board_color: str,
    ) -> None:
        board = self._agent_progress.get(phase)
        if not board:
            board = _AgentProgress(self.console, board_color)
            board.start([])
            self._agent_progress[phase] = board
            self._progress_phases.add(phase)
        board.update(agent_id, agent_name, status, icon, icon_color)

    def stop_agent_progress(self, phase: str) -> None:
        board = self._agent_progress.pop(phase, None)
        if board:
            board.stop()
        self._progress_phases.discard(phase)

    async def run_with_spinner(self, description: str, color: str, awaitable: Awaitable[T]) -> T:
        if self._progress_phases:
            self.console.print(self._indent(Text(f"{description}", style=color)))
            return await awaitable

        spinner = SpinnerColumn(style=color, spinner_name="dots12")
        text = TextColumn("{task.description}", style=color)
        with Progress(spinner, text, console=self.console, transient=True) as progress:
            task_id = progress.add_task(description, total=None)
            try:
                result = await awaitable
            finally:
                progress.stop_task(task_id)
                progress.remove_task(task_id)
        return result


class _AgentProgress:
    """Manage Rich progress rows for agent execution within a phase."""

    def __init__(self, console: Console, color: str):
        self.console = console
        self.color = color
        self.progress = Progress(
            SpinnerColumn(spinner_name="dots12", style=color, finished_text=" "),
            TextColumn("{task.fields[state_icon]}", justify="right"),
            TextColumn("{task.fields[name]}", style="bold white"),
            TextColumn("{task.fields[status]}", style="dim"),
            console=console,
            refresh_per_second=8,
            transient=False,
        )
        self.tasks: dict[str, TaskID] = {}
        self.started = False

    def start(self, agents: Sequence[dict[str, Any]]) -> None:
        for index, agent in enumerate(agents, start=1):
            agent_id = agent.get("id") or agent.get("name") or f"agent_{index}"
            if agent_id in self.tasks:
                continue
            name = agent.get("name") or agent_id
            files = agent.get("file_assignments") or []
            detail = ""
            if files:
                count = len(files)
                label = "file" if count == 1 else "files"
                detail = f"Pending · {count} {label}"
            else:
                detail = "Pending"
            task_id = self.progress.add_task(
                "",
                total=None,
                state_icon="",
                name=name,
                status=detail,
            )
            self.tasks[agent_id] = task_id
        if not self.started:
            self.progress.start()
            self.started = True

    def update(self, agent_id: str, name: str, status: str, icon: str, icon_color: str) -> None:
        if not self.started:
            self.progress.start()
            self.started = True
        task_id = self.tasks.get(agent_id)
        if task_id is None:
            task_id = self.progress.add_task(
                "",
                total=None,
                state_icon=f"[{icon_color}]{icon}[/]",
                name=name,
                status=status,
            )
            self.tasks[agent_id] = task_id
        display_icon = ""
        if icon and icon not in {"⏳", "⟳"}:
            display_icon = f"[{icon_color}]{icon}[/]"
            self.progress.stop_task(task_id)
        else:
            self.progress.start_task(task_id)
        self.progress.update(
            task_id,
            fields={
                "state_icon": display_icon,
                "name": name,
                "status": status,
            },
        )

    def stop(self) -> None:
        if self.started:
            self.progress.stop()
            self.started = False
