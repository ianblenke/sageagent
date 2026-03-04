"""Shell command execution tool."""

from __future__ import annotations

import asyncio
from typing import Any

from sageagent.tools.base import Tool, ToolResult


class ShellTool(Tool):
    """Execute shell commands with configurable timeout."""

    def __init__(self, timeout: int = 120) -> None:
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "shell"

    @property
    def description(self) -> str:
        return "Execute a shell command and return stdout, stderr, and exit code"

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
            },
            "required": ["command"],
        }

    @property
    def tags(self) -> list[str]:
        return ["shell", "execution", "command"]

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute a shell command."""
        command = kwargs.get("command", "")
        if not command:
            return ToolResult(output="", status="error", metadata={"error": "No command provided"})
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self._timeout)
            return ToolResult(
                output=stdout.decode(errors="replace"),
                status="success" if proc.returncode == 0 else "error",
                metadata={
                    "exit_code": proc.returncode,
                    "stderr": stderr.decode(errors="replace"),
                },
            )
        except TimeoutError:
            return ToolResult(output="", status="error", metadata={"error": "Command timed out"})
