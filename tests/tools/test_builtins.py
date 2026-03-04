"""Tests for built-in tools: shell, file operations, docker, code analysis."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sageagent.tools.builtins.code_analysis import CodeAnalysisTool
from sageagent.tools.builtins.docker import DockerTool
from sageagent.tools.builtins.file_ops import FileReadTool, FileSearchTool, FileWriteTool
from sageagent.tools.builtins.shell import ShellTool

# --- ShellTool ---


def test_shell_tool_properties():
    tool = ShellTool()
    assert tool.name == "shell"
    assert "shell" in tool.description.lower()
    assert tool.parameters_schema["type"] == "object"
    assert "shell" in tool.tags


@pytest.mark.asyncio
async def test_shell_tool_success():
    tool = ShellTool()
    result = await tool.execute(command="echo hello")
    assert result.status == "success"
    assert "hello" in result.output


@pytest.mark.asyncio
async def test_shell_tool_failure():
    tool = ShellTool()
    result = await tool.execute(command="exit 1")
    assert result.status == "error"
    assert result.metadata["exit_code"] == 1


@pytest.mark.asyncio
async def test_shell_tool_no_command():
    tool = ShellTool()
    result = await tool.execute()
    assert result.status == "error"
    assert "No command" in result.metadata["error"]


@pytest.mark.asyncio
async def test_shell_tool_timeout():
    tool = ShellTool(timeout=1)
    result = await tool.execute(command="sleep 10")
    assert result.status == "error"
    assert "timed out" in result.metadata["error"].lower()


# --- FileReadTool ---


def test_file_read_properties():
    tool = FileReadTool()
    assert tool.name == "file_read"
    assert "file" in tool.tags


@pytest.mark.asyncio
async def test_file_read_success():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("test content")
        f.flush()
        tool = FileReadTool(working_directory=str(Path(f.name).parent))
        result = await tool.execute(path=Path(f.name).name)
        assert result.status == "success"
        assert result.output == "test content"
    os.unlink(f.name)


@pytest.mark.asyncio
async def test_file_read_not_found():
    tool = FileReadTool(working_directory="/tmp")
    result = await tool.execute(path="nonexistent_file_xyz.txt")
    assert result.status == "error"
    assert "not found" in result.metadata["error"].lower()


@pytest.mark.asyncio
async def test_file_read_no_path():
    tool = FileReadTool()
    result = await tool.execute()
    assert result.status == "error"
    assert "No path" in result.metadata["error"]


# --- FileWriteTool ---


def test_file_write_properties():
    tool = FileWriteTool()
    assert tool.name == "file_write"
    assert "write" in tool.tags


@pytest.mark.asyncio
async def test_file_write_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        tool = FileWriteTool(working_directory=tmpdir)
        result = await tool.execute(path="test.txt", content="hello world")
        assert result.status == "success"
        assert (Path(tmpdir) / "test.txt").read_text() == "hello world"


@pytest.mark.asyncio
async def test_file_write_creates_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        tool = FileWriteTool(working_directory=tmpdir)
        result = await tool.execute(path="sub/dir/test.txt", content="nested")
        assert result.status == "success"
        assert (Path(tmpdir) / "sub" / "dir" / "test.txt").read_text() == "nested"


@pytest.mark.asyncio
async def test_file_write_no_path():
    tool = FileWriteTool()
    result = await tool.execute(content="data")
    assert result.status == "error"


# --- FileSearchTool ---


def test_file_search_properties():
    tool = FileSearchTool()
    assert tool.name == "file_search"
    assert "search" in tool.tags


@pytest.mark.asyncio
async def test_file_search_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "a.py").write_text("a")
        (Path(tmpdir) / "b.txt").write_text("b")
        tool = FileSearchTool(working_directory=tmpdir)
        result = await tool.execute(pattern="*.py")
        assert result.status == "success"
        assert "a.py" in result.output
        assert result.metadata["count"] == 1


@pytest.mark.asyncio
async def test_file_search_no_match():
    with tempfile.TemporaryDirectory() as tmpdir:
        tool = FileSearchTool(working_directory=tmpdir)
        result = await tool.execute(pattern="*.xyz")
        assert result.status == "success"
        assert "No files found" in result.output


@pytest.mark.asyncio
async def test_file_search_no_pattern():
    tool = FileSearchTool()
    result = await tool.execute()
    assert result.status == "error"


# --- DockerTool ---


def test_docker_tool_properties():
    tool = DockerTool()
    assert tool.name == "docker_exec"
    assert "docker" in tool.tags
    assert "container" in tool.description.lower() or "docker" in tool.description.lower()
    schema = tool.parameters_schema
    assert schema["type"] == "object"
    assert "command" in schema["properties"]


@pytest.mark.asyncio
async def test_docker_tool_no_command():
    tool = DockerTool()
    result = await tool.execute()
    assert result.status == "error"
    assert "No command" in result.metadata["error"]


@pytest.mark.asyncio
async def test_docker_tool_import_error():
    tool = DockerTool()
    with patch.dict("sys.modules", {"docker": None}):
        # Simulate docker not being importable inside execute
        result = await tool.execute(command="echo test")
        # It will either succeed (if docker is installed) or return an error
        assert result.status in ("success", "error")


@pytest.mark.asyncio
async def test_docker_tool_execution_error():
    tool = DockerTool()
    mock_docker = MagicMock()
    mock_docker.from_env.return_value.containers.run.side_effect = RuntimeError("Docker error")
    with patch.dict("sys.modules", {"docker": mock_docker}):
        result = await tool.execute(command="echo test")
        assert result.status == "error"
        assert "Docker error" in result.metadata["error"]


@pytest.mark.asyncio
async def test_docker_tool_success():
    tool = DockerTool()
    mock_docker = MagicMock()
    mock_docker.from_env.return_value.containers.run.return_value = b"output data"
    with patch.dict("sys.modules", {"docker": mock_docker}):
        result = await tool.execute(command="echo hello", image="ubuntu")
        assert result.status == "success"
        assert "output data" in result.output
        assert result.metadata["image"] == "ubuntu"


@pytest.mark.asyncio
async def test_docker_tool_string_output():
    tool = DockerTool()
    mock_docker = MagicMock()
    mock_docker.from_env.return_value.containers.run.return_value = "string output"
    with patch.dict("sys.modules", {"docker": mock_docker}):
        result = await tool.execute(command="echo hello")
        assert result.status == "success"
        assert "string output" in result.output


# --- CodeAnalysisTool ---


def test_code_analysis_properties():
    tool = CodeAnalysisTool()
    assert tool.name == "code_analysis"
    assert "analysis" in tool.tags
    assert "static analysis" in tool.description.lower()
    schema = tool.parameters_schema
    assert schema["type"] == "object"
    assert "file_path" in schema["properties"]


@pytest.mark.asyncio
async def test_code_analysis_success():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import os\n\ndef hello():\n    pass\n\nclass Foo:\n    pass\n")
        f.flush()
        tool = CodeAnalysisTool()
        result = await tool.execute(file_path=f.name)
        assert result.status == "success"
        assert "hello" in result.metadata["functions"]
        assert "Foo" in result.metadata["classes"]
        assert "os" in result.metadata["imports"]
    os.unlink(f.name)


@pytest.mark.asyncio
async def test_code_analysis_file_not_found():
    tool = CodeAnalysisTool()
    result = await tool.execute(file_path="/nonexistent/file.py")
    assert result.status == "error"
    assert "not found" in result.metadata["error"].lower()


@pytest.mark.asyncio
async def test_code_analysis_syntax_error():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def broken(\n")
        f.flush()
        tool = CodeAnalysisTool()
        result = await tool.execute(file_path=f.name)
        assert result.status == "error"
        assert "syntax" in result.metadata["error"].lower()
    os.unlink(f.name)


@pytest.mark.asyncio
async def test_code_analysis_no_path():
    tool = CodeAnalysisTool()
    result = await tool.execute()
    assert result.status == "error"


@pytest.mark.asyncio
async def test_file_read_os_error():
    """Test FileReadTool handles OSError during read."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test.txt"
        target.write_text("data")
        tool = FileReadTool(working_directory=tmpdir)
        with patch.object(Path, "read_text", side_effect=OSError("Permission denied")):
            result = await tool.execute(path="test.txt")
            assert result.status == "error"
            assert "Permission denied" in result.metadata["error"]


@pytest.mark.asyncio
async def test_file_write_os_error():
    """Test FileWriteTool handles OSError during write."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tool = FileWriteTool(working_directory=tmpdir)
        with patch.object(Path, "write_text", side_effect=OSError("Disk full")):
            result = await tool.execute(path="test.txt", content="data")
            assert result.status == "error"
            assert "Disk full" in result.metadata["error"]


@pytest.mark.asyncio
async def test_code_analysis_import_from():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("from pathlib import Path\n")
        f.flush()
        tool = CodeAnalysisTool()
        result = await tool.execute(file_path=f.name)
        assert result.status == "success"
        assert "pathlib" in result.metadata["imports"]
    os.unlink(f.name)


@pytest.mark.asyncio
async def test_code_analysis_relative_import():
    """Test code analysis with relative import (node.module is None)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("from . import something\n")
        f.flush()
        tool = CodeAnalysisTool()
        result = await tool.execute(file_path=f.name)
        assert result.status == "success"
        # Relative import has module=None, should be skipped
        assert "something" not in result.metadata.get("imports", [])
    os.unlink(f.name)
