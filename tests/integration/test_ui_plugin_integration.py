import pytest
import pytest_asyncio
import os
from fastapi import FastAPI
from fastapi.testclient import TestClient
from artreactor.core.managers.plugin_manager import PluginManager, PluginType


class TestUiPluginIntegration:
    @pytest_asyncio.fixture
    async def manager(self):
        # Use fixture plugins directory
        plugin_dir = os.path.abspath("tests/fixtures/plugins")
        manager = PluginManager(plugin_dir=plugin_dir)
        await manager.load_plugins()
        return manager

    @pytest.mark.asyncio
    async def test_ui_plugin_loading(self, manager):
        # Verify plugin discovered and loaded
        manifests = manager.get_all_plugins()
        ui_manifests = [m for m in manifests if m.type == PluginType.UI]
        assert len(ui_manifests) >= 1
        assert any(m.name == "ui-test-plugin" for m in ui_manifests)

        # Verify plugin instance created
        plugin = manager.get_plugin("ui-test-plugin")
        assert plugin is not None
        assert plugin.manifest.type == PluginType.UI

        # Verify router
        router = plugin.get_router()
        assert router is not None

    @pytest.mark.asyncio
    async def test_ui_plugin_serving(self, manager):
        plugin = manager.get_plugin("ui-test-plugin")
        app = FastAPI()
        app.include_router(plugin.get_router(), prefix="/ui")
        client = TestClient(app)

        response = client.get("/ui/")
        assert response.status_code == 200
        assert "Hello World" in response.text
