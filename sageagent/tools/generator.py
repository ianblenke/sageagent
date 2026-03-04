"""Dynamic tool generation using LLM."""

from __future__ import annotations

import contextlib
import importlib
import types
from typing import TYPE_CHECKING

from sageagent.tools.base import Tool, ToolResult
from sageagent.tools.registry import ToolRegistry

if TYPE_CHECKING:
    from sageagent.llm.base import LLMBackend

GENERATION_PROMPT = """Generate a Python tool class that inherits from Tool with these requirements:
- Task: {task_description}
- The class must define: name, description, parameters_schema, and execute method
- The execute method must be async and return a ToolResult
- Only use standard library modules
- Return ONLY the Python code, no markdown fences

Example format:
class GeneratedTool(Tool):
    @property
    def name(self) -> str:
        return "tool_name"

    @property
    def description(self) -> str:
        return "What the tool does"

    @property
    def parameters_schema(self) -> dict:
        return {{"type": "object", "properties": {{}}, "required": []}}

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(output="result")
"""


class DynamicToolGenerator:
    """Generates new tools at runtime using an LLM."""

    def __init__(self, llm: LLMBackend, registry: ToolRegistry) -> None:
        self._llm = llm
        self._registry = registry

    async def generate(self, task_description: str) -> Tool:
        """Generate a new tool from a task description, validate, and register it."""
        response = await self._llm.generate(
            messages=[
                {
                    "role": "user",
                    "content": GENERATION_PROMPT.format(task_description=task_description),
                }
            ],
        )
        code = response.content.strip()
        tool = self._instantiate_tool(code)
        self._validate_tool(tool)
        self._registry.register(tool)
        return tool

    def _instantiate_tool(self, code: str) -> Tool:
        """Compile and instantiate a tool from generated code."""
        module = types.ModuleType("generated_tool")
        module.__dict__["Tool"] = Tool
        module.__dict__["ToolResult"] = ToolResult
        # Make common stdlib modules available
        for mod_name in ("json", "os", "re", "math", "pathlib"):
            with contextlib.suppress(ImportError):
                module.__dict__[mod_name] = importlib.import_module(mod_name)
        exec(compile(code, "<generated>", "exec"), module.__dict__)  # noqa: S102
        for attr in module.__dict__.values():
            if isinstance(attr, type) and issubclass(attr, Tool) and attr is not Tool:
                return attr()
        raise ValueError("Generated code does not contain a Tool subclass")

    def _validate_tool(self, tool: Tool) -> None:
        """Validate that a generated tool has all required attributes."""
        if not tool.name:
            raise ValueError("Generated tool must have a non-empty name")
        if not tool.description:
            raise ValueError("Generated tool must have a non-empty description")
        if not isinstance(tool.parameters_schema, dict):
            raise ValueError("Generated tool must have a dict parameters_schema")
