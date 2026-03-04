"""Tests for Claude LLM backend."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from sageagent.llm.base import LLMResponse
from sageagent.llm.claude import DEFAULT_MODEL, ClaudeBackend


@pytest.fixture
def mock_anthropic_client():
    client = AsyncMock()
    return client


@pytest.fixture
def claude_backend(mock_anthropic_client):
    backend = ClaudeBackend(api_key="test-key")
    backend._client = mock_anthropic_client
    return backend


def _make_text_response(text: str, model: str = "claude-sonnet-4-20250514"):
    """Helper to create a mock Anthropic response with text content."""
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.content = [block]
    response.stop_reason = "end_turn"
    response.id = "msg-123"
    response.model = model
    return response


def _make_tool_use_response(tool_name: str, tool_input: dict, tool_id: str = "tool-1"):
    """Helper to create a mock Anthropic response with tool use."""
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "I'll use a tool."
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = tool_name
    tool_block.input = tool_input
    tool_block.id = tool_id
    response = MagicMock()
    response.content = [text_block, tool_block]
    response.stop_reason = "tool_use"
    response.id = "msg-456"
    response.model = "claude-sonnet-4-20250514"
    return response


@pytest.mark.asyncio
async def test_claude_generate(claude_backend, mock_anthropic_client):
    mock_anthropic_client.messages.create.return_value = _make_text_response("Hello!")
    resp = await claude_backend.generate(
        messages=[{"role": "user", "content": "Hi"}],
    )
    assert isinstance(resp, LLMResponse)
    assert resp.content == "Hello!"
    assert resp.stop_reason == "end_turn"
    assert resp.has_tool_calls is False
    mock_anthropic_client.messages.create.assert_called_once()


@pytest.mark.asyncio
async def test_claude_generate_with_system(claude_backend, mock_anthropic_client):
    mock_anthropic_client.messages.create.return_value = _make_text_response("OK")
    resp = await claude_backend.generate(
        messages=[{"role": "user", "content": "test"}],
        system="Be helpful",
    )
    assert resp.content == "OK"
    call_kwargs = mock_anthropic_client.messages.create.call_args[1]
    assert call_kwargs["system"] == "Be helpful"


@pytest.mark.asyncio
async def test_claude_generate_with_model_override(claude_backend, mock_anthropic_client):
    mock_anthropic_client.messages.create.return_value = _make_text_response("OK")
    await claude_backend.generate(
        messages=[{"role": "user", "content": "test"}],
        model="claude-opus-4-20250514",
    )
    call_kwargs = mock_anthropic_client.messages.create.call_args[1]
    assert call_kwargs["model"] == "claude-opus-4-20250514"


@pytest.mark.asyncio
async def test_claude_generate_with_tools(claude_backend, mock_anthropic_client):
    mock_anthropic_client.messages.create.return_value = _make_tool_use_response(
        "search", {"query": "test"}, "tool-abc"
    )
    tools = [{"name": "search", "description": "Search", "input_schema": {}}]
    resp = await claude_backend.generate_with_tools(
        messages=[{"role": "user", "content": "Search for test"}],
        tools=tools,
    )
    assert resp.has_tool_calls is True
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0].tool_name == "search"
    assert resp.tool_calls[0].arguments == {"query": "test"}
    assert resp.tool_calls[0].call_id == "tool-abc"
    assert resp.content == "I'll use a tool."


@pytest.mark.asyncio
async def test_claude_generate_with_tools_and_system(claude_backend, mock_anthropic_client):
    mock_anthropic_client.messages.create.return_value = _make_text_response("Done")
    await claude_backend.generate_with_tools(
        messages=[{"role": "user", "content": "test"}],
        tools=[],
        system="You are an agent",
    )
    call_kwargs = mock_anthropic_client.messages.create.call_args[1]
    assert call_kwargs["system"] == "You are an agent"


@pytest.mark.asyncio
async def test_claude_generate_with_tools_non_dict_input(claude_backend, mock_anthropic_client):
    """Test that non-dict tool input is handled gracefully."""
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "test"
    tool_block.input = "not a dict"
    tool_block.id = "tool-1"
    response = MagicMock()
    response.content = [tool_block]
    response.stop_reason = "tool_use"
    response.id = "msg-789"
    response.model = "claude-sonnet-4-20250514"
    mock_anthropic_client.messages.create.return_value = response
    resp = await claude_backend.generate_with_tools(
        messages=[{"role": "user", "content": "test"}],
        tools=[],
    )
    assert resp.tool_calls[0].arguments == {}


def test_claude_default_model():
    backend = ClaudeBackend(api_key="key")
    assert backend._model == DEFAULT_MODEL


def test_claude_custom_model():
    backend = ClaudeBackend(api_key="key", model="custom-model")
    assert backend._model == "custom-model"


@pytest.mark.asyncio
async def test_claude_generate_without_system(claude_backend, mock_anthropic_client):
    """Test that system kwarg is NOT passed when system is empty."""
    mock_anthropic_client.messages.create.return_value = _make_text_response("OK")
    await claude_backend.generate(
        messages=[{"role": "user", "content": "test"}],
        system="",
    )
    call_kwargs = mock_anthropic_client.messages.create.call_args[1]
    assert "system" not in call_kwargs


@pytest.mark.asyncio
async def test_claude_generate_with_tools_without_system(claude_backend, mock_anthropic_client):
    """Test that system kwarg is NOT passed for tool calls when system is empty."""
    mock_anthropic_client.messages.create.return_value = _make_text_response("OK")
    await claude_backend.generate_with_tools(
        messages=[{"role": "user", "content": "test"}],
        tools=[],
        system="",
    )
    call_kwargs = mock_anthropic_client.messages.create.call_args[1]
    assert "system" not in call_kwargs


@pytest.mark.asyncio
async def test_claude_generate_empty_content_blocks(claude_backend, mock_anthropic_client):
    """Test response with empty content list (branch: for loop not entered)."""
    response = MagicMock()
    response.content = []
    response.stop_reason = "end_turn"
    response.id = "msg-empty"
    response.model = "claude-sonnet-4-20250514"
    mock_anthropic_client.messages.create.return_value = response
    resp = await claude_backend.generate(messages=[{"role": "user", "content": "test"}])
    assert resp.content == ""


@pytest.mark.asyncio
async def test_claude_generate_non_text_block(claude_backend, mock_anthropic_client):
    """Test generate() with a non-text block type (skipped by the if check)."""
    non_text_block = MagicMock()
    non_text_block.type = "image"
    response = MagicMock()
    response.content = [non_text_block]
    response.stop_reason = "end_turn"
    response.id = "msg-nt"
    response.model = "claude-sonnet-4-20250514"
    mock_anthropic_client.messages.create.return_value = response
    resp = await claude_backend.generate(messages=[{"role": "user", "content": "test"}])
    assert resp.content == ""


@pytest.mark.asyncio
async def test_claude_generate_with_tools_empty_content_blocks(
    claude_backend, mock_anthropic_client
):
    """Test tool response with empty content list (branch: for loop not entered)."""
    response = MagicMock()
    response.content = []
    response.stop_reason = "end_turn"
    response.id = "msg-empty"
    response.model = "claude-sonnet-4-20250514"
    mock_anthropic_client.messages.create.return_value = response
    resp = await claude_backend.generate_with_tools(
        messages=[{"role": "user", "content": "test"}], tools=[]
    )
    assert resp.content == ""
    assert resp.has_tool_calls is False


@pytest.mark.asyncio
async def test_claude_generate_with_tools_unknown_block_type(claude_backend, mock_anthropic_client):
    """Test generate_with_tools() with a block that is neither text nor tool_use."""
    unknown_block = MagicMock()
    unknown_block.type = "thinking"
    response = MagicMock()
    response.content = [unknown_block]
    response.stop_reason = "end_turn"
    response.id = "msg-unk"
    response.model = "claude-sonnet-4-20250514"
    mock_anthropic_client.messages.create.return_value = response
    resp = await claude_backend.generate_with_tools(
        messages=[{"role": "user", "content": "test"}], tools=[]
    )
    assert resp.content == ""
    assert resp.has_tool_calls is False
