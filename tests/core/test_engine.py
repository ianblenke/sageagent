"""Tests for AgentEngine orchestration."""

import json
from unittest.mock import patch

import pytest

from sageagent.communication.protocols import MessageType
from sageagent.core.config import EngineConfig
from sageagent.core.engine import AgentEngine
from sageagent.core.types import AgentStatus
from sageagent.llm.base import LLMResponse
from tests.conftest import MockLLMBackend


@pytest.fixture
def engine_with_mock_llm(engine_config):
    engine = AgentEngine(engine_config)
    mock_llm = MockLLMBackend(
        responses=[
            LLMResponse(content="TASK_COMPLETE: Done"),
        ]
    )
    engine._llm = mock_llm
    # Rewire components that depend on LLM
    from sageagent.topology.decomposer import TaskDecomposer
    from sageagent.topology.manager import TopologyManager

    engine._decomposer = TaskDecomposer(mock_llm)
    engine._topology = TopologyManager(
        decomposer=engine._decomposer,
        llm=mock_llm,
        tool_registry=engine._tools,
        memory=engine._memory,
        bus=engine._bus,
        config=engine._config.agent,
    )
    return engine, mock_llm


@pytest.mark.asyncio
async def test_engine_task_submission(engine_with_mock_llm):
    engine, mock_llm = engine_with_mock_llm
    result = await engine.run("Test task")
    assert "content" in result


@pytest.mark.asyncio
async def test_engine_result_aggregation(engine_with_mock_llm):
    engine, mock_llm = engine_with_mock_llm
    result = await engine.run("Aggregate task")
    assert result["content"] == "TASK_COMPLETE: Done"


@pytest.mark.asyncio
async def test_engine_run_with_topology(engine_with_mock_llm):
    engine, mock_llm = engine_with_mock_llm
    mock_llm._responses = [
        LLMResponse(content=json.dumps({"decompose": False})),
        LLMResponse(content="Topology result"),
    ]
    mock_llm._call_index = 0
    result = await engine.run_with_topology("Decompose task")
    assert "content" in result


@pytest.mark.asyncio
async def test_engine_shutdown(engine_with_mock_llm):
    engine, mock_llm = engine_with_mock_llm
    await engine.run("Task")
    await engine.shutdown()
    assert len(engine._agents) == 0
    history = engine.bus.get_history(MessageType.SHUTDOWN_REQUEST)
    assert len(history) == 1


@pytest.mark.asyncio
async def test_engine_shutdown_terminates_active(engine_with_mock_llm):
    engine, _ = engine_with_mock_llm
    # Create an agent but don't run it
    from sageagent.core.agent import Agent

    agent = Agent(
        role="test",
        task="test",
        llm=engine._llm,
        tool_registry=engine._tools,
        memory=engine._memory,
        bus=engine._bus,
        config=engine._config.agent,
    )
    engine._agents.append(agent)
    assert agent.status == AgentStatus.CREATED
    await engine.shutdown()
    assert agent.status == AgentStatus.TERMINATED


def test_engine_properties(engine_config):
    engine = AgentEngine(engine_config)
    assert engine.memory is not None
    assert engine.query is not None
    assert engine.bus is not None
    assert engine.tools is not None


def test_engine_default_tools(engine_config):
    engine = AgentEngine(engine_config)
    assert "shell" in engine.tools
    assert "file_read" in engine.tools
    assert "file_write" in engine.tools
    assert "file_search" in engine.tools


def test_engine_claude_backend():
    config = EngineConfig(llm_backend="claude", anthropic_api_key="test")
    engine = AgentEngine(config)
    from sageagent.llm.claude import ClaudeBackend

    assert isinstance(engine._llm, ClaudeBackend)


def test_engine_openai_backend():
    config = EngineConfig(llm_backend="openai", openai_api_key="test")
    engine = AgentEngine(config)
    from sageagent.llm.openai import OpenAIBackend

    assert isinstance(engine._llm, OpenAIBackend)


def test_engine_from_env_config():
    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "key", "OPENAI_API_KEY": ""}, clear=False):
        engine = AgentEngine()
        assert engine._config.anthropic_api_key == "key"
