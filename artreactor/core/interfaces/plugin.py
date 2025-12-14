from abc import ABC, abstractmethod
from typing import Any, List

from artreactor.models.plugin import PluginManifest, PluginTiming, PluginType

# Re-export models for backward compatibility
__all__ = [
    "PluginManifest",
    "PluginTiming",
    "PluginType",
    "Plugin",
    "CorePlugin",
    "RouterPlugin",
    "AppPlugin",
    "UiPlugin",
]


class Plugin(ABC):
    def __init__(self, manifest: PluginManifest, context: Any):
        self.manifest = manifest
        self.context = context
        self.tools: List[Any] = []

    @abstractmethod
    async def initialize(self):
        """Called when the plugin is loaded."""
        pass

    @abstractmethod
    async def shutdown(self):
        """Called when the plugin is unloaded or system shuts down."""
        pass


class CorePlugin(Plugin):
    """
    Core plugins extend the system's core capabilities.
    They are typically loaded in the pre-init phase.
    """

    pass


class RouterPlugin(Plugin):
    """
    Router plugins expose MCP-compatible endpoints.
    """

    @abstractmethod
    def get_router(self):
        """Returns a FastAPI APIRouter instance."""
        pass


class AppPlugin(Plugin):
    """
    App plugins control external applications.
    """

    @abstractmethod
    async def launch(self) -> bool:
        """Launches the external application."""
        pass

    @abstractmethod
    async def execute_code(self, code: str) -> Any:
        """Executes code in the external application."""
        pass


class UiPlugin(RouterPlugin):
    """
    UI plugins serve static files via a FastAPI router.
    """

    async def initialize(self):
        pass

    async def shutdown(self):
        pass

    def get_router(self):
        from fastapi import APIRouter
        from fastapi.responses import FileResponse
        from pathlib import Path
        import os

        router = APIRouter()

        # Resolve static_dir
        # Config takes precedence, then dist
        config_dir = self.manifest.config.get("static_dir")
        if config_dir:
            if not os.path.isabs(config_dir) and self.manifest.path:
                static_dir = Path(self.manifest.path) / config_dir
            else:
                static_dir = Path(config_dir)
        elif self.manifest.path:
            static_dir = Path(self.manifest.path) / "dist"
        else:
            return router

        if static_dir.exists():
            # Explicit root handler
            if self.manifest.config.get("html", True):
                index_path = static_dir / "index.html"

                @router.get("/", include_in_schema=False)
                async def serve_root():
                    if index_path.exists():
                        return FileResponse(index_path)
                    from fastapi import HTTPException

                    raise HTTPException(status_code=404, detail="Index not found")

            # Catch-all for assets and SPA fallback
            @router.get("/{path:path}")
            async def serve_catchall(path: str):
                file_path = static_dir / path

                # Check if file exists
                if file_path.exists() and file_path.is_file():
                    return FileResponse(file_path)

                # SPA Fallback logic
                if self.manifest.config.get("html", True):
                    index_path = static_dir / "index.html"
                    if index_path.exists():
                        return FileResponse(index_path)

                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail="Not Found")

        return router
