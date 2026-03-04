"""Tests for LLM base types."""

from sageagent.llm.base import LLMResponse, ToolCall


def test_tool_call_creation():
    tc = ToolCall(tool_name="test", arguments={"key": "val"}, call_id="id-1")
    assert tc.tool_name == "test"
    assert tc.arguments == {"key": "val"}
    assert tc.call_id == "id-1"


def test_tool_call_defaults():
    tc = ToolCall(tool_name="test")
    assert tc.arguments == {}
    assert tc.call_id == ""


def test_llm_response_no_tool_calls():
    resp = LLMResponse(content="hello", stop_reason="end_turn")
    assert resp.content == "hello"
    assert resp.has_tool_calls is False
    assert resp.tool_calls == []
    assert resp.raw == {}


def test_llm_response_with_tool_calls():
    tc = ToolCall(tool_name="search", arguments={"q": "test"})
    resp = LLMResponse(content="", tool_calls=[tc], stop_reason="tool_use")
    assert resp.has_tool_calls is True
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0].tool_name == "search"


def test_llm_response_defaults():
    resp = LLMResponse()
    assert resp.content == ""
    assert resp.stop_reason == ""
    assert resp.has_tool_calls is False
