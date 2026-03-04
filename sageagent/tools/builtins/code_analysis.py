"""Static code analysis tool."""

from __future__ import annotations

from typing import Any

from sageagent.tools.base import Tool, ToolResult


class CodeAnalysisTool(Tool):
    """Run static analysis on source code files."""

    def __init__(self, timeout: int = 60) -> None:
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "code_analysis"

    @property
    def description(self) -> str:
        return "Run static analysis (ast parsing and basic checks) on a Python file"

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the Python file to analyze",
                },
            },
            "required": ["file_path"],
        }

    @property
    def tags(self) -> list[str]:
        return ["analysis", "code", "static", "python"]

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Analyze a Python file using ast and compile checks."""
        file_path = kwargs.get("file_path", "")
        if not file_path:
            return ToolResult(
                output="", status="error", metadata={"error": "No file_path provided"}
            )
        try:
            import ast
            from pathlib import Path

            path = Path(file_path)
            if not path.is_file():
                return ToolResult(
                    output="", status="error", metadata={"error": f"File not found: {file_path}"}
                )
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=file_path)
            functions = [
                node.name
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
            return ToolResult(
                output=f"Functions: {functions}\nClasses: {classes}\nImports: {imports}",
                status="success",
                metadata={
                    "functions": functions,
                    "classes": classes,
                    "imports": imports,
                    "lines": len(source.splitlines()),
                },
            )
        except SyntaxError as e:
            return ToolResult(output="", status="error", metadata={"error": f"Syntax error: {e}"})
