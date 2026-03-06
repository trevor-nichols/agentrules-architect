import io
import unittest

from rich.console import Console

from agentrules.cli.ui.analysis_view import _AgentProgress


class _ProgressSpy:
    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self._next_task_id = 0

    def start(self) -> None:
        self.calls.append(("start",))

    def stop(self) -> None:
        self.calls.append(("stop",))

    def add_task(self, _description: str, total=None, **fields):  # type: ignore[no-untyped-def]
        task_id = self._next_task_id
        self._next_task_id += 1
        self.calls.append(("add_task", task_id, total, fields))
        return task_id

    def start_task(self, task_id: int) -> None:
        self.calls.append(("start_task", task_id))

    def stop_task(self, task_id: int) -> None:
        self.calls.append(("stop_task", task_id))

    def update(self, task_id: int, *, fields: dict[str, str]) -> None:
        self.calls.append(("update", task_id, fields))


class AgentProgressTests(unittest.TestCase):
    def _make_board(self) -> _AgentProgress:
        console = Console(file=io.StringIO(), force_terminal=False)
        return _AgentProgress(console, "yellow")

    def test_start_adds_all_rows_before_progress_starts(self) -> None:
        board = self._make_board()
        spy = _ProgressSpy()
        board.progress = spy  # type: ignore[assignment]

        board.start(
            [
                {"id": "agent_1", "name": "Alpha", "file_assignments": ["a.py"]},
                {"id": "agent_2", "name": "Beta", "file_assignments": ["b.py"]},
                {"id": "agent_3", "name": "Gamma", "file_assignments": ["c.py"]},
            ]
        )

        self.assertEqual(
            [call[0] for call in spy.calls],
            ["add_task", "add_task", "add_task", "start"],
        )
        self.assertEqual(list(board.tasks), ["agent_1", "agent_2", "agent_3"])

    def test_update_uses_state_icon_for_late_added_rows(self) -> None:
        board = self._make_board()
        spy = _ProgressSpy()
        board.progress = spy  # type: ignore[assignment]

        board.update("agent_1", "Alpha", "Completed", "✓", "green")

        add_call = next(call for call in spy.calls if call[0] == "add_task")
        fields = add_call[3]
        self.assertIn("state_icon", fields)
        self.assertNotIn("icon", fields)


if __name__ == "__main__":
    unittest.main()
