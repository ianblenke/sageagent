"""CLI entry point for SageAgent."""

from __future__ import annotations

import asyncio
import json

import typer

from sageagent.core.config import EngineConfig
from sageagent.core.engine import AgentEngine

app = typer.Typer(name="sageagent", help="SageAgent: Open-source Agent Development Kit")


@app.command()
def run(
    task: str = typer.Argument(..., help="Task description for the agent to execute"),
    backend: str = typer.Option("claude", "--backend", "-b", help="LLM backend: claude or openai"),
    model: str = typer.Option("", "--model", "-m", help="Model name override"),
    decompose: bool = typer.Option(
        False, "--decompose", "-d", help="Use topology manager for task decomposition"
    ),
    max_depth: int = typer.Option(5, "--max-depth", help="Maximum agent hierarchy depth"),
    timeout: int = typer.Option(120, "--timeout", "-t", help="Tool execution timeout in seconds"),
) -> None:
    """Run an agent task."""
    config = EngineConfig(
        llm_backend=backend,  # type: ignore[arg-type]
        model_name=model,
        agent={"max_hierarchy_depth": max_depth},  # type: ignore[arg-type]
        tools={"execution_timeout_seconds": timeout},  # type: ignore[arg-type]
    )
    config = EngineConfig.from_env().model_copy(
        update={
            "llm_backend": backend,
            "model_name": model,
        }
    )
    config.agent.max_hierarchy_depth = max_depth
    config.tools.execution_timeout_seconds = timeout

    engine = AgentEngine(config)

    async def _run() -> dict:
        try:
            if decompose:
                return await engine.run_with_topology(task)
            return await engine.run(task)
        finally:
            await engine.shutdown()

    result = asyncio.run(_run())
    typer.echo(json.dumps(result, indent=2, default=str))


@app.command()
def config() -> None:
    """Show current configuration."""
    cfg = EngineConfig.from_env()
    # Mask API keys
    data = cfg.model_dump()
    if data.get("anthropic_api_key"):
        data["anthropic_api_key"] = "***"
    if data.get("openai_api_key"):
        data["openai_api_key"] = "***"
    typer.echo(json.dumps(data, indent=2))


if __name__ == "__main__":
    app()
