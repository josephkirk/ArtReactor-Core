import pytest
from unittest.mock import patch, AsyncMock
from artreactor.core.managers.plugin_manager import PluginManager
from artreactor.core.interfaces.plugin import PluginManifest, PluginType, PluginTiming


@pytest.fixture
def plugin_manager():
    return PluginManager(plugin_dir="tests/plugins")


@pytest.fixture
def mock_manifest():
    return PluginManifest(
        name="test-plugin",
        version="0.1.0",
        type=PluginType.CORE,
        timing=PluginTiming.DEFAULT,
        priority=10,
    )


@pytest.mark.asyncio
async def test_load_plugins_timing(plugin_manager, mock_manifest):
    # Mock discover_plugins to return our manifest
    with patch.object(plugin_manager, "discover_plugins", return_value=[mock_manifest]):
        # Mock _load_plugin
        plugin_manager._load_plugin = AsyncMock()

        # Test loading correct timing
        await plugin_manager.load_plugins(PluginTiming.DEFAULT)
        plugin_manager._load_plugin.assert_called_once_with(mock_manifest)

        # Test loading incorrect timing
        plugin_manager._load_plugin.reset_mock()
        await plugin_manager.load_plugins(PluginTiming.PRE_INIT)
        plugin_manager._load_plugin.assert_not_called()


@pytest.mark.asyncio
async def test_load_plugins_priority(plugin_manager):
    m1 = PluginManifest(name="p1", version="1", type=PluginType.CORE, priority=10)
    m2 = PluginManifest(name="p2", version="1", type=PluginType.CORE, priority=20)

    with patch.object(plugin_manager, "discover_plugins", return_value=[m1, m2]):
        plugin_manager._load_plugin = AsyncMock()

        await plugin_manager.load_plugins(PluginTiming.DEFAULT)

        # Verify call order
        calls = plugin_manager._load_plugin.call_args_list
        assert calls[0][0][0] == m2  # Higher priority first
        assert calls[1][0][0] == m1


def test_discover_plugins_empty(plugin_manager):
    with patch("pathlib.Path.exists", return_value=False):
        assert plugin_manager.discover_plugins() == []
