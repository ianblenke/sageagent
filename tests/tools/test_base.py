"""Tests for tool base class and result types."""

import pytest

from sageagent.tools.base import ToolResult


def test_tool_result_success():
    result = ToolResult(output="data", status="success", metadata={"key": "val"})
    assert result.output == "data"
    assert result.status == "success"
    assert result.is_error is False


def test_tool_result_error():
    result = ToolResult(output="", status="error")
    assert result.is_error is True


def test_tool_result_defaults():
    result = ToolResult()
    assert result.output == ""
    assert result.status == "success"
    assert result.metadata == {}
    assert result.is_error is False


def test_mock_tool_schema(mock_llm):
    """Test tool schema exposure via MockTool from conftest."""
    from tests.conftest import MockTool

    tool = MockTool(name="test_tool")
    schema = tool.to_llm_schema()
    assert schema["name"] == "test_tool"
    assert "description" in schema
    assert "input_schema" in schema
    assert isinstance(schema["input_schema"], dict)


def test_mock_tool_tags():
    from tests.conftest import MockTool

    tool = MockTool(name="tagged", tool_tags=["a", "b"])
    assert tool.tags == ["a", "b"]


@pytest.mark.asyncio
async def test_mock_tool_execute():
    from tests.conftest import MockTool

    tool = MockTool(name="exec_test", result=ToolResult(output="result"))
    result = await tool.execute(input="hello")
    assert result.output == "result"
    assert tool.execute_calls == [{"input": "hello"}]


def test_tool_base_tags_default():
    """Test that the Tool base class tags property returns empty list."""
    from sageagent.tools.base import Tool, ToolResult

    class MinimalTool(Tool):
        @property
        def name(self) -> str:
            return "minimal"

        @property
        def description(self) -> str:
            return "A minimal tool"

        @property
        def parameters_schema(self) -> dict:
            return {"type": "object"}

        async def execute(self, **kwargs) -> ToolResult:
            return ToolResult()

    tool = MinimalTool()
    assert tool.tags == []
