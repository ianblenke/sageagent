"""Tests for configuration models."""

import os
from unittest.mock import patch

from sageagent.core.config import AgentConfig, EngineConfig, MemoryConfig, ToolConfig


def test_memory_config_defaults():
    cfg = MemoryConfig()
    assert cfg.max_age_seconds == 3600
    assert cfg.gc_interval_seconds == 300
    assert cfg.pin_active_tasks is True


def test_tool_config_defaults():
    cfg = ToolConfig()
    assert cfg.execution_timeout_seconds == 120
    assert cfg.docker_enabled is False
    assert cfg.docker_image == "python:3.11-slim"
    assert cfg.docker_memory_limit == "512m"
    assert cfg.working_directory == "."


def test_agent_config_defaults():
    cfg = AgentConfig()
    assert cfg.max_iterations == 50
    assert cfg.max_hierarchy_depth == 5


def test_engine_config_defaults():
    cfg = EngineConfig()
    assert cfg.llm_backend == "claude"
    assert cfg.anthropic_api_key == ""
    assert cfg.openai_api_key == ""
    assert cfg.model_name == ""
    assert isinstance(cfg.agent, AgentConfig)
    assert isinstance(cfg.tools, ToolConfig)
    assert isinstance(cfg.memory, MemoryConfig)


def test_engine_config_from_env_anthropic():
    with patch.dict(
        os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test", "OPENAI_API_KEY": ""}, clear=False
    ):
        cfg = EngineConfig.from_env()
        assert cfg.llm_backend == "claude"
        assert cfg.anthropic_api_key == "sk-ant-test"


def test_engine_config_from_env_openai():
    with patch.dict(
        os.environ, {"ANTHROPIC_API_KEY": "", "OPENAI_API_KEY": "sk-oai-test"}, clear=False
    ):
        cfg = EngineConfig.from_env()
        assert cfg.llm_backend == "openai"
        assert cfg.openai_api_key == "sk-oai-test"


def test_engine_config_from_env_no_keys():
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "", "OPENAI_API_KEY": ""}, clear=False):
        cfg = EngineConfig.from_env()
        assert cfg.llm_backend == "claude"


def test_engine_config_custom_values():
    cfg = EngineConfig(
        llm_backend="openai",
        openai_api_key="key",
        model_name="gpt-4",
        agent=AgentConfig(max_iterations=5),
        tools=ToolConfig(execution_timeout_seconds=30),
        memory=MemoryConfig(max_age_seconds=100),
    )
    assert cfg.llm_backend == "openai"
    assert cfg.agent.max_iterations == 5
    assert cfg.tools.execution_timeout_seconds == 30
    assert cfg.memory.max_age_seconds == 100
