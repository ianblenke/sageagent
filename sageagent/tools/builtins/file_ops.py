"""File operation tools: read, write, search."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sageagent.tools.base import Tool, ToolResult


class FileReadTool(Tool):
    """Read file contents."""

    def __init__(self, working_directory: str = ".") -> None:
        self._cwd = Path(working_directory).resolve()

    @property
    def name(self) -> str:
        return "file_read"

    @property
    def description(self) -> str:
        return "Read the contents of a file"

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"},
            },
            "required": ["path"],
        }

    @property
    def tags(self) -> list[str]:
        return ["file", "read", "filesystem"]

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Read a file's contents."""
        path_str = kwargs.get("path", "")
        if not path_str:
            return ToolResult(output="", status="error", metadata={"error": "No path provided"})
        target = (self._cwd / path_str).resolve()
        if not target.is_file():
            return ToolResult(
                output="", status="error", metadata={"error": f"File not found: {target}"}
            )
        try:
            content = target.read_text(encoding="utf-8", errors="replace")
            return ToolResult(output=content, status="success", metadata={"path": str(target)})
        except OSError as e:
            return ToolResult(output="", status="error", metadata={"error": str(e)})


class FileWriteTool(Tool):
    """Write content to a file."""

    def __init__(self, working_directory: str = ".") -> None:
        self._cwd = Path(working_directory).resolve()

    @property
    def name(self) -> str:
        return "file_write"

    @property
    def description(self) -> str:
        return "Write content to a file, creating directories as needed"

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        }

    @property
    def tags(self) -> list[str]:
        return ["file", "write", "filesystem"]

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Write content to a file."""
        path_str = kwargs.get("path", "")
        content = kwargs.get("content", "")
        if not path_str:
            return ToolResult(output="", status="error", metadata={"error": "No path provided"})
        target = (self._cwd / path_str).resolve()
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return ToolResult(
                output=f"Wrote {len(content)} bytes to {target}",
                status="success",
                metadata={"path": str(target)},
            )
        except OSError as e:
            return ToolResult(output="", status="error", metadata={"error": str(e)})


class FileSearchTool(Tool):
    """Search for files matching a glob pattern."""

    def __init__(self, working_directory: str = ".") -> None:
        self._cwd = Path(working_directory).resolve()

    @property
    def name(self) -> str:
        return "file_search"

    @property
    def description(self) -> str:
        return "Search for files matching a glob pattern in the working directory"

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match (e.g., '**/*.py')",
                },
            },
            "required": ["pattern"],
        }

    @property
    def tags(self) -> list[str]:
        return ["file", "search", "filesystem", "glob"]

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Search for files matching a glob pattern."""
        pattern = kwargs.get("pattern", "")
        if not pattern:
            return ToolResult(output="", status="error", metadata={"error": "No pattern provided"})
        matches = sorted(
            str(p.relative_to(self._cwd)) for p in self._cwd.rglob(pattern) if p.is_file()
        )
        return ToolResult(
            output="\n".join(matches) if matches else "No files found",
            status="success",
            metadata={"count": len(matches)},
        )
