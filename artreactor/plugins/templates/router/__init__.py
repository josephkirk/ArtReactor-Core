from typing import Any
from fastapi import APIRouter
from artreactor.core.interfaces.plugin import RouterPlugin, PluginManifest

class {{class_name}}(RouterPlugin):
    def __init__(self, manifest: PluginManifest, context: Any):
        super().__init__(manifest, context)
        self.router = APIRouter()
        
        @self.router.get("/")
        async def root():
            return {"message": f"Hello from {{name}}!"}

    async def initialize(self):
        """Called when the plugin is loaded."""
        pass

    async def shutdown(self):
        """Called when the plugin is unloaded."""
        pass

    def get_router(self) -> APIRouter:
        return self.router
