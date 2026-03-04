"""Configuration models for SageAgent."""

from __future__ import annotations

import os
from typing import Literal

from pydantic import BaseModel, Field


class MemoryConfig(BaseModel):
    """Configuration for the memory graph."""

    max_age_seconds: int = Field(
        default=3600, ge=0, description="Max node age before GC eligibility"
    )
    gc_interval_seconds: int = Field(default=300, ge=1, description="Interval between GC runs")
    pin_active_tasks: bool = Field(default=True, description="Keep active task nodes from GC")


class ToolConfig(BaseModel):
    """Configuration for tool execution."""

    execution_timeout_seconds: int = Field(default=120, ge=1, description="Max tool execution time")
    docker_enabled: bool = Field(default=False, description="Enable Docker sandboxed execution")
    docker_image: str = Field(default="python:3.11-slim", description="Default Docker image")
    docker_memory_limit: str = Field(default="512m", description="Docker container memory limit")
    working_directory: str = Field(default=".", description="Working directory for file tools")


class AgentConfig(BaseModel):
    """Configuration for agent behavior."""

    max_iterations: int = Field(default=50, ge=1, description="Max execution loop iterations")
    max_hierarchy_depth: int = Field(default=5, ge=1, description="Max sub-agent nesting depth")


class EngineConfig(BaseModel):
    """Top-level configuration for the AgentEngine."""

    llm_backend: Literal["claude", "openai"] = Field(
        default="claude", description="LLM backend to use"
    )
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    openai_api_key: str = Field(default="", description="OpenAI API key")
    model_name: str = Field(default="", description="Model name override")
    agent: AgentConfig = Field(default_factory=AgentConfig)
    tools: ToolConfig = Field(default_factory=ToolConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)

    @classmethod
    def from_env(cls) -> EngineConfig:
        """Load configuration from environment variables with sensible defaults."""
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        backend = "claude" if anthropic_key else "openai" if openai_key else "claude"
        return cls(
            llm_backend=backend,
            anthropic_api_key=anthropic_key,
            openai_api_key=openai_key,
        )
