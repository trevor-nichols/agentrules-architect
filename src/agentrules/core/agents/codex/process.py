"""Subprocess wrapper for launching Codex app-server."""

from __future__ import annotations

import asyncio
import json
import os
from collections import deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import CodexExecutableNotFoundError, CodexProcessError


def _format_config_override(value: Any) -> str:
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value)


@dataclass(frozen=True)
class CodexProcessLaunchConfig:
    executable_path: str
    codex_home: str | None = None
    cwd: str | None = None
    config_overrides: Mapping[str, Any] = field(default_factory=dict)

    def build_command(self) -> list[str]:
        command = [self.executable_path, "app-server"]
        for key, value in self.config_overrides.items():
            command.extend(["-c", f"{key}={_format_config_override(value)}"])
        return command


class CodexAppServerProcess:
    """Manage the lifetime of a `codex app-server` subprocess."""

    def __init__(
        self,
        launch_config: CodexProcessLaunchConfig,
        *,
        command: Sequence[str] | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        self.launch_config = launch_config
        self._command = tuple(command) if command is not None else tuple(launch_config.build_command())
        self._env_overrides = dict(env or {})
        self._process: asyncio.subprocess.Process | None = None
        self._stderr_lines: deque[str] = deque(maxlen=50)

    @property
    def command(self) -> tuple[str, ...]:
        return self._command

    @property
    def process(self) -> asyncio.subprocess.Process:
        if self._process is None:
            raise CodexProcessError("Codex app-server process has not been started.")
        return self._process

    @property
    def stdout(self) -> asyncio.StreamReader:
        stdout = self.process.stdout
        if stdout is None:
            raise CodexProcessError("Codex app-server stdout is not available.")
        return stdout

    @property
    def stdin(self) -> asyncio.StreamWriter:
        stdin = self.process.stdin
        if stdin is None:
            raise CodexProcessError("Codex app-server stdin is not available.")
        return stdin

    @property
    def recent_stderr(self) -> tuple[str, ...]:
        return tuple(self._stderr_lines)

    @property
    def returncode(self) -> int | None:
        return self._process.returncode if self._process is not None else None

    async def start(self) -> None:
        if self._process is not None:
            return

        env = os.environ.copy()
        env.update(self._env_overrides)
        if self.launch_config.codex_home is not None:
            codex_home_path = Path(self.launch_config.codex_home).expanduser()
            codex_home_path.mkdir(parents=True, exist_ok=True)
            env["CODEX_HOME"] = str(codex_home_path)

        try:
            self._process = await asyncio.create_subprocess_exec(
                *self._command,
                cwd=self.launch_config.cwd,
                env=env,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            executable = self._command[0] if self._command else self.launch_config.executable_path
            raise CodexExecutableNotFoundError(
                f"Could not launch Codex app-server; executable not found: {executable}"
            ) from exc
        except Exception as exc:  # pragma: no cover - defensive
            raise CodexProcessError(f"Failed to start Codex app-server: {exc}") from exc

    async def read_stderr_forever(self) -> None:
        stderr = self.process.stderr
        if stderr is None:
            return
        while True:
            line = await stderr.readline()
            if not line:
                return
            message = line.decode("utf-8", errors="replace").rstrip()
            if message:
                self._stderr_lines.append(message)

    async def stop(self) -> None:
        if self._process is None:
            return

        process = self._process
        self._process = None

        stdin = process.stdin
        if stdin is not None and not stdin.is_closing():
            stdin.close()

        try:
            await asyncio.wait_for(process.wait(), timeout=1.0)
            return
        except TimeoutError:
            pass

        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=3.0)
            return
        except TimeoutError:
            process.kill()
            await process.wait()

    def describe_launch(self) -> dict[str, str | None]:
        return {
            "command": " ".join(self._command),
            "codex_home": self.launch_config.codex_home,
            "cwd": self.launch_config.cwd,
        }
