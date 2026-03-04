"""Tests for tool registry."""

import pytest

from sageagent.tools.registry import ToolRegistry
from tests.conftest import MockTool


@pytest.fixture
def registry_with_tools():
    reg = ToolRegistry()
    reg.register(MockTool(name="shell", tool_tags=["shell", "exec"]))
    reg.register(MockTool(name="file_read", tool_tags=["file", "read"]))
    return reg


def test_register_and_get(tool_registry):
    tool = MockTool(name="test")
    tool_registry.register(tool)
    assert tool_registry.get("test") is tool


def test_get_not_found(tool_registry):
    with pytest.raises(KeyError, match="not found"):
        tool_registry.get("nonexistent")


def test_unregister(tool_registry):
    tool = MockTool(name="test")
    tool_registry.register(tool)
    tool_registry.unregister("test")
    assert "test" not in tool_registry


def test_unregister_not_found(tool_registry):
    with pytest.raises(KeyError, match="not found"):
        tool_registry.unregister("nonexistent")


def test_list_tools(registry_with_tools):
    tools = registry_with_tools.list_tools()
    assert len(tools) == 2
    names = {t.name for t in tools}
    assert names == {"shell", "file_read"}


def test_find_by_tag(registry_with_tools):
    results = registry_with_tools.find_by_tag("shell")
    assert len(results) == 1
    assert results[0].name == "shell"


def test_find_by_tag_no_match(registry_with_tools):
    results = registry_with_tools.find_by_tag("nonexistent")
    assert len(results) == 0


def test_find_by_description(registry_with_tools):
    results = registry_with_tools.find_by_description("shell")
    assert len(results) == 1


def test_find_by_description_no_match(registry_with_tools):
    results = registry_with_tools.find_by_description("zzz_no_match")
    assert len(results) == 0


def test_to_llm_schemas(registry_with_tools):
    schemas = registry_with_tools.to_llm_schemas()
    assert len(schemas) == 2
    assert all("name" in s for s in schemas)


def test_contains(tool_registry):
    tool = MockTool(name="check")
    tool_registry.register(tool)
    assert "check" in tool_registry
    assert "missing" not in tool_registry


def test_len(tool_registry):
    assert len(tool_registry) == 0
    tool_registry.register(MockTool(name="a"))
    assert len(tool_registry) == 1
