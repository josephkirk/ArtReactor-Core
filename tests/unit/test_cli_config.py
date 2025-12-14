import os
from unittest.mock import patch
from typer.testing import CliRunner
from artreactor.cli.main import app

runner = CliRunner()


def test_start_command_with_config():
    """Verify that --config sets the ARTE_CONFIG_PATH environment variable."""
    # We mock uvicorn.run to prevent actual server startup
    with patch("uvicorn.run"):
        # We also need to mock os.environ to avoid side effects
        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(
                app, ["start", "--config", "test_config.toml", "--port", "9000"]
            )

            assert result.exit_code == 0
            assert os.environ.get("ARTE_CONFIG_PATH") == str(
                os.path.abspath("test_config.toml")
            )
            assert "Using config file: test_config.toml" in result.stdout


def test_start_command_without_config():
    """Verify that ARTE_CONFIG_PATH is not set if --config is omitted."""
    with patch("uvicorn.run"):
        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(app, ["start"])

            assert result.exit_code == 0
            assert "ARTE_CONFIG_PATH" not in os.environ
