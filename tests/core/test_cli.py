"""Tests for the CLI entry point."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from sageagent.cli import app

runner = CliRunner()


def test_config_command():
    with patch.dict(
        "os.environ", {"ANTHROPIC_API_KEY": "sk-test", "OPENAI_API_KEY": ""}, clear=False
    ):
        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["anthropic_api_key"] == "***"


def test_config_command_openai():
    with patch.dict(
        "os.environ", {"ANTHROPIC_API_KEY": "", "OPENAI_API_KEY": "sk-oai"}, clear=False
    ):
        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["openai_api_key"] == "***"


def test_config_command_no_keys():
    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "", "OPENAI_API_KEY": ""}, clear=False):
        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["anthropic_api_key"] == ""


def test_run_command():
    with patch("sageagent.cli.AgentEngine") as mock_engine_cls:
        mock_engine = MagicMock()
        mock_engine.run = AsyncMock(return_value={"content": "done"})
        mock_engine.shutdown = AsyncMock()
        mock_engine_cls.return_value = mock_engine

        result = runner.invoke(app, ["run", "Test task", "--backend", "claude"])
        assert result.exit_code == 0
        assert "done" in result.stdout


def test_run_command_with_decompose():
    with patch("sageagent.cli.AgentEngine") as mock_engine_cls:
        mock_engine = MagicMock()
        mock_engine.run_with_topology = AsyncMock(return_value={"content": "decomposed"})
        mock_engine.shutdown = AsyncMock()
        mock_engine_cls.return_value = mock_engine

        result = runner.invoke(app, ["run", "Complex task", "--decompose"])
        assert result.exit_code == 0
        assert "decomposed" in result.stdout


def test_run_command_with_options():
    with patch("sageagent.cli.AgentEngine") as mock_engine_cls:
        mock_engine = MagicMock()
        mock_engine.run = AsyncMock(return_value={"content": "ok"})
        mock_engine.shutdown = AsyncMock()
        mock_engine_cls.return_value = mock_engine

        result = runner.invoke(
            app,
            [
                "run",
                "Task",
                "--backend",
                "openai",
                "--model",
                "gpt-4",
                "--max-depth",
                "3",
                "--timeout",
                "30",
            ],
        )
        assert result.exit_code == 0
