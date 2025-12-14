from typing import Any
from fastapi import APIRouter
from artreactor.core.interfaces.plugin import RouterPlugin, PluginManifest
from artreactor.core.decorators import tool
import subprocess


class ExampleGitSkillPlugin(RouterPlugin):
    def __init__(self, manifest: PluginManifest, context: Any):
        super().__init__(manifest, context)
        self.router = APIRouter()
        
        @self.router.get("/status")
        async def git_status():
            """Get the git status of the current repository."""
            try:
                result = subprocess.run(
                    ["git", "status", "--short"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=30
                )
                return {"status": "success", "output": result.stdout}
            except subprocess.CalledProcessError as e:
                return {"status": "error", "message": str(e)}
        
        @self.router.get("/log")
        async def git_log(limit: int = 5):
            """Get the git log with a specified number of commits."""
            try:
                result = subprocess.run(
                    ["git", "log", f"-{limit}", "--oneline"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=30
                )
                return {"status": "success", "output": result.stdout}
            except subprocess.CalledProcessError as e:
                return {"status": "error", "message": str(e)}

    @tool(name="check_git_status", description="Check the git status of the repository")
    async def check_status(self):
        """Check git status using the tool decorator."""
        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error: {e}"

    async def initialize(self):
        """Called when the plugin is loaded."""
        pass

    async def shutdown(self):
        """Called when the plugin is unloaded."""
        pass

    def get_router(self) -> APIRouter:
        return self.router
