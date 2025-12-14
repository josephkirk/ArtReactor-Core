import pytest
from artreactor.core.managers.plugin_manager import PluginManager
from artreactor.core.interfaces.plugin import Plugin, PluginManifest, PluginType
from artreactor.core.decorators import tool


# Mock Plugin
class MockDecoratedPlugin(Plugin):
    async def initialize(self):
        pass

    async def shutdown(self):
        pass

    @tool(name="mock_tool", description="A mock tool")
    def my_tool(self, x: int) -> int:
        """Original docstring"""
        return x * 2

    @tool()
    def another_tool(self):
        pass


@pytest.mark.asyncio
async def test_plugin_tool_loading():
    # Setup
    manager = PluginManager()
    manifest = PluginManifest(name="mock-plugin", version="1.0.0", type=PluginType.CORE)

    # Manually inject the mock plugin class logic since we can't easily mock file loading here
    # We will use the internal _scan_for_tools directly or mock _load_plugin

    plugin = MockDecoratedPlugin(manifest, None)

    # Act
    manager._scan_for_tools(plugin)

    # Assert
    assert len(plugin.tools) == 2

    tool1 = next(t for t in plugin.tools if t.name == "mock_tool")
    assert tool1.description == "A mock tool"
    assert tool1.func == plugin.my_tool

    tool2 = next(t for t in plugin.tools if t.name == "another_tool")
    assert tool2.func == plugin.another_tool
