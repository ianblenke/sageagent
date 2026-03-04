"""Tests for dynamic tool generator."""

from unittest.mock import patch

import pytest

from sageagent.llm.base import LLMResponse
from sageagent.tools.generator import DynamicToolGenerator
from sageagent.tools.registry import ToolRegistry
from tests.conftest import MockLLMBackend

VALID_TOOL_CODE = """
class GeneratedTool(Tool):
    @property
    def name(self) -> str:
        return "word_counter"

    @property
    def description(self) -> str:
        return "Count words in text"

    @property
    def parameters_schema(self) -> dict:
        return {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}

    async def execute(self, **kwargs) -> ToolResult:
        text = kwargs.get("text", "")
        count = len(text.split())
        return ToolResult(output=str(count))
"""


@pytest.mark.asyncio
async def test_generate_tool():
    llm = MockLLMBackend(responses=[LLMResponse(content=VALID_TOOL_CODE)])
    registry = ToolRegistry()
    gen = DynamicToolGenerator(llm, registry)
    tool = await gen.generate("Count words in text")
    assert tool.name == "word_counter"
    assert "word_counter" in registry
    result = await tool.execute(text="hello world foo")
    assert result.output == "3"


@pytest.mark.asyncio
async def test_generate_tool_no_subclass():
    llm = MockLLMBackend(responses=[LLMResponse(content="x = 1")])
    registry = ToolRegistry()
    gen = DynamicToolGenerator(llm, registry)
    with pytest.raises(ValueError, match="does not contain a Tool subclass"):
        await gen.generate("bad task")


@pytest.mark.asyncio
async def test_generate_tool_empty_name():
    code = """
class BadTool(Tool):
    @property
    def name(self) -> str:
        return ""
    @property
    def description(self) -> str:
        return "desc"
    @property
    def parameters_schema(self) -> dict:
        return {}
    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult()
"""
    llm = MockLLMBackend(responses=[LLMResponse(content=code)])
    registry = ToolRegistry()
    gen = DynamicToolGenerator(llm, registry)
    with pytest.raises(ValueError, match="non-empty name"):
        await gen.generate("task")


@pytest.mark.asyncio
async def test_generate_tool_empty_description():
    code = """
class BadTool(Tool):
    @property
    def name(self) -> str:
        return "bad"
    @property
    def description(self) -> str:
        return ""
    @property
    def parameters_schema(self) -> dict:
        return {}
    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult()
"""
    llm = MockLLMBackend(responses=[LLMResponse(content=code)])
    registry = ToolRegistry()
    gen = DynamicToolGenerator(llm, registry)
    with pytest.raises(ValueError, match="non-empty description"):
        await gen.generate("task")


@pytest.mark.asyncio
async def test_generate_tool_bad_schema():
    code = """
class BadTool(Tool):
    @property
    def name(self) -> str:
        return "bad"
    @property
    def description(self) -> str:
        return "desc"
    @property
    def parameters_schema(self):
        return "not a dict"
    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult()
"""
    llm = MockLLMBackend(responses=[LLMResponse(content=code)])
    registry = ToolRegistry()
    gen = DynamicToolGenerator(llm, registry)
    with pytest.raises(ValueError, match="dict parameters_schema"):
        await gen.generate("task")


@pytest.mark.asyncio
async def test_generate_tool_stdlib_import_error():
    """Test that ImportError during stdlib import is silently caught."""
    llm = MockLLMBackend(responses=[LLMResponse(content=VALID_TOOL_CODE)])
    registry = ToolRegistry()
    gen = DynamicToolGenerator(llm, registry)
    # Patch importlib.import_module to fail for one module
    original_import = __import__("importlib").import_module

    def failing_import(name):
        if name == "math":
            raise ImportError("Mocked failure")
        return original_import(name)

    with patch("importlib.import_module", side_effect=failing_import):
        tool = await gen.generate("task")
        assert tool.name == "word_counter"
