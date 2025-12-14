import pytest
import toml
from pathlib import Path
from artreactor.core.managers.plugin_manager import PluginManager


@pytest.fixture
def temp_config_env(tmp_path):
    """Creates a temporary environment with a config file and a dummy plugin."""
    plugin_dir = tmp_path / "extra_plugins"
    plugin_dir.mkdir()

    # Create a dummy plugin
    dummy_plugin_dir = plugin_dir / "dummy-plugin"
    dummy_plugin_dir.mkdir()

    with open(dummy_plugin_dir / "plugin.toml", "w") as f:
        f.write("""
name = "dummy-plugin"
version = "0.0.1"
type = "core"
description = "Dummy plugin for config test"
""")

    config_path = tmp_path / "config.toml"
    config = {
        "plugin_dirs": [str(plugin_dir)],
        "plugins": {
            "dummy-plugin": {"enabled": True},
            "disabled-plugin": {"enabled": False},  # We'll simulate this one existing
        },
    }

    with open(config_path, "w") as f:
        toml.dump(config, f)

    return config_path, plugin_dir


@pytest.mark.asyncio
async def test_plugin_manager_loads_config(temp_config_env):
    """Verify PluginManager loads plugin_dirs and respects enabled/disabled config."""
    config_path, plugin_dir = temp_config_env

    # Create a "disabled" plugin to test filtering
    disabled_plugin_dir = plugin_dir / "disabled-plugin"
    disabled_plugin_dir.mkdir()
    with open(disabled_plugin_dir / "plugin.toml", "w") as f:
        f.write("""
name = "disabled-plugin"
version = "0.0.1"
type = "core"
description = "Should be disabled"
""")

    manager = PluginManager(config_path=str(config_path))

    # Verify plugin_dirs loaded
    assert Path(plugin_dir) in manager.plugin_dirs

    # Discovery
    manifests = manager.discover_plugins()
    plugin_names = [m.name for m in manifests]

    # Verify dummy-plugin is present
    assert "dummy-plugin" in plugin_names

    # Verify disabled-plugin is NOT present (filtered out)
    assert "disabled-plugin" not in plugin_names


@pytest.mark.asyncio
async def test_plugin_manager_auto_install_config(tmp_path):
    """Verify PluginManager detects missing plugins with source and auto-installs (mocked)."""
    config_path = tmp_path / "auto_install_config.toml"
    config = {
        "plugin_dirs": [str(tmp_path / "plugins")],
        "plugins": {
            "git-plugin": {"enabled": True, "source": "git@github.com:fake/repo.git"}
        },
    }
    with open(config_path, "w") as f:
        toml.dump(config, f)

    # Mock subprocess to avoid actual git clone
    with pytest.MonkeyPatch.context() as m:
        import subprocess
        from unittest.mock import MagicMock

        mock_run = MagicMock()
        m.setattr(subprocess, "run", mock_run)

        _ = PluginManager(config_path=str(config_path))

        # It should have attempted to clone
        # Check if subprocess.run was called with git clone command
        mock_run.assert_called()
        args = mock_run.call_args[0][0]
        assert args[0] == "git"
        assert args[1] == "clone"
        assert args[2] == "git@github.com:fake/repo.git"
