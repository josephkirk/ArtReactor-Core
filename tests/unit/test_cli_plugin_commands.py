"""Tests for plugin CLI commands."""

import sys
import os
import pytest
from typer.testing import CliRunner
from artreactor.cli.main import app

runner = CliRunner()


@pytest.fixture
def change_test_dir(tmp_path):
    """Fixture to change to temp directory and restore on cleanup."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)


def test_plugin_templates_command():
    """Verify that the templates command lists available templates."""
    result = runner.invoke(app, ["plugin", "templates"])

    assert result.exit_code == 0
    assert "core" in result.stdout
    assert "router" in result.stdout
    assert "ui" in result.stdout
    assert "Available plugin templates" in result.stdout


def test_plugin_create_command(change_test_dir):
    """Verify that plugin create works correctly."""
    result = runner.invoke(app, ["plugin", "create", "test-plugin", "--type", "core"])

    assert result.exit_code == 0
    assert "Created plugin test-plugin" in result.stdout

    # Check that files were created
    plugin_dir = change_test_dir / "plugins" / "test-plugin"
    assert plugin_dir.exists()
    assert (plugin_dir / "plugin.toml").exists()
    assert (plugin_dir / "__init__.py").exists()


def test_plugin_init_project_command(change_test_dir):
    """Verify that init-project creates a complete project structure."""
    result = runner.invoke(
        app, ["plugin", "init-project", "my-plugin", "--type", "core"]
    )

    assert result.exit_code == 0
    assert "Successfully initialized plugin project" in result.stdout

    # Check project files
    assert (change_test_dir / "pyproject.toml").exists()
    assert (change_test_dir / "README.md").exists()
    assert (change_test_dir / ".gitignore").exists()
    assert (change_test_dir / "tests" / "test_plugin_load.py").exists()
    assert (change_test_dir / "plugins" / "my-plugin" / "plugin.toml").exists()

    # Verify pyproject.toml content
    pyproject_content = (change_test_dir / "pyproject.toml").read_text()
    assert "my-plugin" in pyproject_content
    assert "artreactor" in pyproject_content

    # Verify README content
    readme_content = (change_test_dir / "README.md").read_text()
    assert "my-plugin" in readme_content
    assert "arte plugin install" in readme_content


def test_plugin_install_local_copy(tmp_path):
    """Verify that plugin install copies a local plugin."""
    original_cwd = os.getcwd()

    # Create source plugin
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    plugin_dir = source_dir / "test-plugin"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.toml").write_text("name = 'test-plugin'\ntype = 'core'\n")

    # Create host directory
    host_dir = tmp_path / "host"
    host_dir.mkdir()
    os.chdir(host_dir)

    try:
        result = runner.invoke(app, ["plugin", "install", str(plugin_dir)])

        assert result.exit_code == 0
        assert "Installing plugin test-plugin" in result.stdout

        # Check that plugin was copied
        installed_dir = host_dir / "plugins" / "test-plugin"
        assert installed_dir.exists()
        assert (installed_dir / "plugin.toml").exists()

        # Verify it's a copy, not a symlink
        assert not installed_dir.is_symlink()

    finally:
        os.chdir(original_cwd)


def test_plugin_install_with_link(tmp_path):
    """Verify that plugin install with --link creates a link (junction on Windows, symlink on Unix)."""
    original_cwd = os.getcwd()

    # Create source plugin
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    plugin_dir = source_dir / "test-plugin"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.toml").write_text("name = 'test-plugin'\ntype = 'core'\n")

    # Create host directory
    host_dir = tmp_path / "host"
    host_dir.mkdir()
    os.chdir(host_dir)

    try:
        result = runner.invoke(app, ["plugin", "install", str(plugin_dir), "--link"])

        assert result.exit_code == 0
        assert "Linking plugin test-plugin" in result.stdout

        # Check that plugin was linked
        installed_dir = host_dir / "plugins" / "test-plugin"
        assert installed_dir.exists()

        # On Windows, junctions are not symlinks but still redirect to target
        # On Unix, it should be a symlink
        if sys.platform == "win32":
            # Junction: verify content is accessible
            assert (installed_dir / "plugin.toml").exists()
        else:
            assert installed_dir.is_symlink()
            assert installed_dir.resolve() == plugin_dir.resolve()

    finally:
        os.chdir(original_cwd)


def test_plugin_install_auto_detect_workspace(tmp_path):
    """Verify that plugin install auto-detects plugins in workspace structure."""
    original_cwd = os.getcwd()

    # Create workspace with plugins/
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    plugins_dir = workspace_dir / "plugins"
    plugins_dir.mkdir()
    plugin_dir = plugins_dir / "test-plugin"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.toml").write_text("name = 'test-plugin'\ntype = 'core'\n")

    # Create host directory
    host_dir = tmp_path / "host"
    host_dir.mkdir()
    os.chdir(host_dir)

    try:
        result = runner.invoke(app, ["plugin", "install", str(workspace_dir)])

        assert result.exit_code == 0
        assert "Installing plugin test-plugin" in result.stdout

        # Check that plugin was copied
        installed_dir = host_dir / "plugins" / "test-plugin"
        assert installed_dir.exists()
        assert (installed_dir / "plugin.toml").exists()

    finally:
        os.chdir(original_cwd)


def test_plugin_install_no_plugin_toml(tmp_path):
    """Verify that plugin install fails gracefully when no plugin.toml found."""
    original_cwd = os.getcwd()

    # Create empty directory
    source_dir = tmp_path / "empty"
    source_dir.mkdir()

    # Create host directory
    host_dir = tmp_path / "host"
    host_dir.mkdir()
    os.chdir(host_dir)

    try:
        result = runner.invoke(app, ["plugin", "install", str(source_dir)])

        assert result.exit_code == 1
        assert "No plugin.toml found" in result.output

    finally:
        os.chdir(original_cwd)


def test_plugin_install_multiple_plugins_error(tmp_path):
    """Verify that plugin install fails when multiple plugins are found."""
    original_cwd = os.getcwd()

    # Create workspace with multiple plugins
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    plugins_dir = workspace_dir / "plugins"
    plugins_dir.mkdir()

    plugin1_dir = plugins_dir / "plugin1"
    plugin1_dir.mkdir()
    (plugin1_dir / "plugin.toml").write_text("name = 'plugin1'\ntype = 'core'\n")

    plugin2_dir = plugins_dir / "plugin2"
    plugin2_dir.mkdir()
    (plugin2_dir / "plugin.toml").write_text("name = 'plugin2'\ntype = 'core'\n")

    # Create host directory
    host_dir = tmp_path / "host"
    host_dir.mkdir()
    os.chdir(host_dir)

    try:
        result = runner.invoke(app, ["plugin", "install", str(workspace_dir)])

        assert result.exit_code == 1
        assert "Multiple plugins found" in result.output

    finally:
        os.chdir(original_cwd)
