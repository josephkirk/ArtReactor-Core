import pytest
import os
from fastapi.testclient import TestClient
from artreactor.core.interfaces.plugin import UiPlugin, PluginManifest, PluginType


class TestUiPlugin:
    @pytest.fixture
    def manifest(self):
        # Point to the fixture directory
        fixture_path = os.path.abspath("tests/fixtures/plugins/ui_plugin")
        return PluginManifest(
            name="ui-test-plugin",
            version="0.1.0",
            type=PluginType.UI,
            config={"static_dir": "dist"},
            path=fixture_path,
        )

    @pytest.fixture
    def plugin(self, manifest):
        return UiPlugin(manifest, context=None)

    @pytest.fixture
    def client(self, plugin):
        from fastapi import FastAPI

        app = FastAPI()
        # Include with a prefix to simulate real usage and avoid empty path issues
        app.include_router(plugin.get_router(), prefix="/test-ui")
        return TestClient(app)

    def test_verify_path_debug(self, manifest):
        import os

        static_dir = os.path.join(manifest.path, manifest.config["static_dir"])
        print(f"DEBUG PATH: {static_dir}")
        assert os.path.exists(static_dir), f"Path does not exist: {static_dir}"
        assert os.path.exists(os.path.join(static_dir, "index.html")), (
            "index.html missing"
        )

    def test_serve_index(self, client):
        # Debug: try explicitly first
        res = client.get("/test-ui/index.html")
        print(f"Explicit index: {res.status_code}")

        response = client.get("/test-ui/")
        print(f"Root index: {response.status_code}")

        # If explicit works but root doesn't, it's html=True issue or trailing slash
        if res.status_code == 200:
            assert response.status_code == 200, (
                "Explicit index works but root directory serving failed"
            )

        assert response.status_code == 200
        assert "Hello World" in response.text
        assert "text/html" in response.headers["content-type"]

    def test_serve_asset(self, client):
        response = client.get("/test-ui/assets/app.js")
        assert response.status_code == 200
        assert "console.log" in response.text
        # content-type might vary depending on system mime types, generally application/javascript

    def test_serve_404_or_fallback(self, client):
        # With html=True (default), we expect SPA fallback to index.html
        response = client.get("/test-ui/nonexistent.html")
        assert response.status_code == 200
        assert "Hello World" in response.text

    def test_spa_fallback_logic(self, manifest):
        # Already tested above, but let's be specific about configuration if needed
        pass

    def test_diagnostics_direct_mount(self, manifest):
        from fastapi import FastAPI
        from fastapi.staticfiles import StaticFiles
        import os

        static_dir = os.path.join(manifest.path, "dist")

        app = FastAPI()
        app.mount(
            "/direct", StaticFiles(directory=static_dir, html=True), name="direct"
        )
        client = TestClient(app)

        res = client.get("/direct/")
        print(f"Direct mount root: {res.status_code}")
        assert res.status_code == 200
        assert "Hello World" in res.text

    def test_router_mount_logic(self, plugin):
        # Verify the router itself has the route
        router = plugin.get_router()
        found = False
        for route in router.routes:
            print(f"Route: {route.path} {route.name}")
            if route.path == "/":
                found = True
        assert found, "Router did not have '/' mounted"
