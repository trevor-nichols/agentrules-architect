"""Event sink bridging analysis events with the Rich-based CLI view."""

from __future__ import annotations

from numbers import Real

from agentrules.core.analysis.events import AnalysisEvent, AnalysisEventSink

from .analysis_view import AnalysisView


class ViewEventSink(AnalysisEventSink):
    """Translate analysis events into Rich-rendered status updates."""

    PHASE_COLORS = {
        "phase2": "blue",
        "phase3": "yellow",
    }

    def __init__(self, view: AnalysisView):
        self.view = view
        self._agents: dict[str, dict] = {}

    def publish(self, event: AnalysisEvent) -> None:
        if event.phase == "phase2" and event.type == "agent_plan":
            agents = list(event.payload.get("agents", []))
            self._cache_agents(agents)
            self.view.render_agent_plan(agents, color=self.PHASE_COLORS["phase2"])
            return

        if event.phase not in self.PHASE_COLORS:
            return

        phase_color = self.PHASE_COLORS[event.phase]
        payload = dict(event.payload)
        agent_id = payload.get("id")
        if agent_id:
            agent_info = self._agents.setdefault(agent_id, {})
            agent_info.update(payload)
        agent_name = self._resolve_agent_name(payload)

        if event.type == "agent_registered":
            detail = self._format_detail(payload)
            message = f"Pending{detail}" if detail else "Pending"
            self.view.update_agent_progress(
                event.phase,
                agent_id or agent_name,
                agent_name,
                message,
                "⏳",
                phase_color,
                phase_color,
            )
            return
        if event.type == "agent_started":
            detail = self._format_detail(payload)
            message = f"In progress{detail}"
            self.view.update_agent_progress(
                event.phase,
                agent_id or agent_name,
                agent_name,
                message,
                "⟳",
                phase_color,
                phase_color,
            )
        elif event.type == "agent_completed":
            detail = self._format_detail(payload)
            message = f"Completed{detail}"
            duration = payload.get("duration")
            if isinstance(duration, Real):
                message += f" in {duration:.1f}s"
            self.view.update_agent_progress(
                event.phase,
                agent_id or agent_name,
                agent_name,
                message,
                "✓",
                phase_color,
                phase_color,
            )
        elif event.type == "agent_failed":
            error = payload.get("error", "unknown error")
            duration = payload.get("duration")
            message = f"Failed: {error}"
            if isinstance(duration, Real):
                message += f" after {duration:.1f}s"
            self.view.update_agent_progress(
                event.phase,
                agent_id or agent_name,
                agent_name,
                message,
                "✗",
                "red",
                phase_color,
            )
        elif event.type == "agent_batch_started":
            message = self._format_batch_status(
                payload,
                prefix="Batch",
                in_progress=True,
            )
            self.view.update_agent_progress(
                event.phase,
                agent_id or agent_name,
                agent_name,
                message,
                "⟳",
                phase_color,
                phase_color,
            )
        elif event.type == "agent_batch_completed":
            message = self._format_batch_status(
                payload,
                prefix="Completed batch",
                in_progress=False,
            )
            self.view.update_agent_progress(
                event.phase,
                agent_id or agent_name,
                agent_name,
                message,
                "",
                phase_color,
                phase_color,
            )

    def _cache_agents(self, agents: list[dict]) -> None:
        for entry in agents:
            agent_id = entry.get("id")
            if agent_id:
                self._agents.setdefault(agent_id, {}).update(entry)

    def _resolve_agent_name(self, payload: dict) -> str:
        if payload.get("name"):
            return str(payload["name"])
        if payload.get("id"):
            return str(payload["id"])
        return "Agent"

    def _format_detail(self, payload: dict) -> str:
        files = payload.get("files")
        file_count = payload.get("file_count")
        batches = payload.get("batches")

        count = None
        if isinstance(file_count, int):
            count = file_count
        if files:
            try:
                count = len(files)  # type: ignore[arg-type]
            except TypeError:
                pass

        parts: list[str] = []
        if isinstance(count, int):
            label = "file" if count == 1 else "files"
            parts.append(f"{count} {label}")
        if isinstance(batches, int) and batches > 1:
            label = "batch" if batches == 1 else "batches"
            parts.append(f"{batches} {label}")

        return f" · {' · '.join(parts)}" if parts else ""

    def _format_batch_status(self, payload: dict, *, prefix: str, in_progress: bool) -> str:
        index = payload.get("batch_index")
        total = payload.get("batch_total")
        files = payload.get("files")

        parts: list[str] = []
        if isinstance(index, int) and isinstance(total, int):
            parts.append(f"{prefix} {index}/{total}")
        elif isinstance(index, int):
            parts.append(f"{prefix} {index}")
        else:
            parts.append(prefix)

        file_detail = self._format_detail({"files": files, "file_count": len(files) if files else None})
        if file_detail:
            parts.append(file_detail.strip(" ·"))

        if in_progress:
            return " ".join(parts)
        return " ".join(parts)
