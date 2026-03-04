"""Tests for OpenAI LLM backend."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from sageagent.llm.base import LLMResponse
from sageagent.llm.openai import DEFAULT_MODEL, OpenAIBackend


@pytest.fixture
def mock_openai_client():
    return AsyncMock()


@pytest.fixture
def openai_backend(mock_openai_client):
    backend = OpenAIBackend(api_key="test-key")
    backend._client = mock_openai_client
    return backend


def _make_chat_response(content: str, finish_reason: str = "stop"):
    message = MagicMock()
    message.content = content
    message.tool_calls = None
    choice = MagicMock()
    choice.message = message
    choice.finish_reason = finish_reason
    response = MagicMock()
    response.choices = [choice]
    response.id = "chatcmpl-123"
    response.model = "gpt-4o"
    return response


def _make_tool_call_response(tool_name: str, arguments: str, tc_id: str = "call-1"):
    tc = MagicMock()
    tc.function.name = tool_name
    tc.function.arguments = arguments
    tc.id = tc_id
    message = MagicMock()
    message.content = ""
    message.tool_calls = [tc]
    choice = MagicMock()
    choice.message = message
    choice.finish_reason = "tool_calls"
    response = MagicMock()
    response.choices = [choice]
    response.id = "chatcmpl-456"
    response.model = "gpt-4o"
    return response


@pytest.mark.asyncio
async def test_openai_generate(openai_backend, mock_openai_client):
    mock_openai_client.chat.completions.create.return_value = _make_chat_response("Hello!")
    resp = await openai_backend.generate(
        messages=[{"role": "user", "content": "Hi"}],
    )
    assert isinstance(resp, LLMResponse)
    assert resp.content == "Hello!"
    assert resp.stop_reason == "stop"
    assert resp.has_tool_calls is False


@pytest.mark.asyncio
async def test_openai_generate_with_system(openai_backend, mock_openai_client):
    mock_openai_client.chat.completions.create.return_value = _make_chat_response("OK")
    await openai_backend.generate(
        messages=[{"role": "user", "content": "test"}],
        system="Be helpful",
    )
    call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
    msgs = call_kwargs["messages"]
    assert msgs[0]["role"] == "system"
    assert msgs[0]["content"] == "Be helpful"


@pytest.mark.asyncio
async def test_openai_generate_with_model_override(openai_backend, mock_openai_client):
    mock_openai_client.chat.completions.create.return_value = _make_chat_response("OK")
    await openai_backend.generate(
        messages=[{"role": "user", "content": "test"}],
        model="gpt-4-turbo",
    )
    call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
    assert call_kwargs["model"] == "gpt-4-turbo"


@pytest.mark.asyncio
async def test_openai_generate_with_tools(openai_backend, mock_openai_client):
    mock_openai_client.chat.completions.create.return_value = _make_tool_call_response(
        "search", '{"query": "test"}', "call-abc"
    )
    tools = [{"name": "search", "description": "Search", "input_schema": {"type": "object"}}]
    resp = await openai_backend.generate_with_tools(
        messages=[{"role": "user", "content": "Search"}],
        tools=tools,
    )
    assert resp.has_tool_calls is True
    assert resp.tool_calls[0].tool_name == "search"
    assert resp.tool_calls[0].arguments == {"query": "test"}
    assert resp.tool_calls[0].call_id == "call-abc"


@pytest.mark.asyncio
async def test_openai_generate_with_tools_and_system(openai_backend, mock_openai_client):
    mock_openai_client.chat.completions.create.return_value = _make_chat_response("Done")
    await openai_backend.generate_with_tools(
        messages=[{"role": "user", "content": "test"}],
        tools=[{"name": "t", "description": "d", "parameters": {}}],
        system="You are an agent",
    )
    call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
    assert call_kwargs["messages"][0]["content"] == "You are an agent"


@pytest.mark.asyncio
async def test_openai_generate_with_tools_no_calls(openai_backend, mock_openai_client):
    mock_openai_client.chat.completions.create.return_value = _make_chat_response("No tools needed")
    resp = await openai_backend.generate_with_tools(
        messages=[{"role": "user", "content": "test"}],
        tools=[],
    )
    assert resp.has_tool_calls is False
    assert resp.content == "No tools needed"


@pytest.mark.asyncio
async def test_openai_generate_with_tools_non_dict_parsed(openai_backend, mock_openai_client):
    """Test that non-dict parsed arguments are handled as empty dict."""
    mock_openai_client.chat.completions.create.return_value = _make_tool_call_response(
        "test", '"just a string"'
    )
    resp = await openai_backend.generate_with_tools(
        messages=[{"role": "user", "content": "test"}],
        tools=[{"name": "test", "description": "d", "parameters": {}}],
    )
    assert resp.tool_calls[0].arguments == {}


@pytest.mark.asyncio
async def test_openai_generate_none_content(openai_backend, mock_openai_client):
    """Test handling of None content from OpenAI."""
    message = MagicMock()
    message.content = None
    message.tool_calls = None
    choice = MagicMock()
    choice.message = message
    choice.finish_reason = "stop"
    response = MagicMock()
    response.choices = [choice]
    response.id = "chatcmpl-789"
    response.model = "gpt-4o"
    mock_openai_client.chat.completions.create.return_value = response
    resp = await openai_backend.generate(messages=[{"role": "user", "content": "test"}])
    assert resp.content == ""


def test_openai_default_model():
    backend = OpenAIBackend(api_key="key")
    assert backend._model == DEFAULT_MODEL


def test_openai_custom_model():
    backend = OpenAIBackend(api_key="key", model="custom")
    assert backend._model == "custom"
