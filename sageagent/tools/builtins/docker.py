"""Docker sandboxed execution tool."""

from __future__ import annotations

from typing import Any

from sageagent.tools.base import Tool, ToolResult


class DockerTool(Tool):
    """Execute commands in an isolated Docker container."""

    def __init__(self, default_image: str = "python:3.11-slim", memory_limit: str = "512m") -> None:
        self._default_image = default_image
        self._memory_limit = memory_limit

    @property
    def name(self) -> str:
        return "docker_exec"

    @property
    def description(self) -> str:
        return "Execute a command in an isolated Docker container with resource limits"

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Command to execute in the container"},
                "image": {"type": "string", "description": "Docker image to use (optional)"},
            },
            "required": ["command"],
        }

    @property
    def tags(self) -> list[str]:
        return ["docker", "sandbox", "execution", "container"]

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute a command in a Docker container."""
        command = kwargs.get("command", "")
        image = kwargs.get("image", self._default_image)
        if not command:
            return ToolResult(output="", status="error", metadata={"error": "No command provided"})
        try:
            import docker as docker_lib

            client = docker_lib.from_env()
            container = client.containers.run(
                image=image,
                command=["sh", "-c", command],
                mem_limit=self._memory_limit,
                network_mode="none",
                remove=True,
                stdout=True,
                stderr=True,
            )
            output = (
                container.decode(errors="replace")
                if isinstance(container, bytes)
                else str(container)
            )
            return ToolResult(
                output=output,
                status="success",
                metadata={"image": image},
            )
        except ImportError:
            return ToolResult(
                output="", status="error", metadata={"error": "docker package not installed"}
            )
        except Exception as e:
            return ToolResult(output="", status="error", metadata={"error": str(e)})
