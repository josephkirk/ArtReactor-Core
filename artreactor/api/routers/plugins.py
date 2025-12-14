from typing import List

from fastapi import APIRouter, Depends

from artreactor.api.dependencies import get_plugin_manager
from artreactor.core.managers.plugin_manager import PluginManager
from artreactor.models.plugin import PluginManifest, PluginTiming

router = APIRouter(prefix="/plugins", tags=["plugins"])


@router.get("/", response_model=List[PluginManifest])
async def list_plugins(pm: PluginManager = Depends(get_plugin_manager)):
    return pm.get_all_plugins()


@router.post("/reload")
async def reload_plugins(pm: PluginManager = Depends(get_plugin_manager)):
    # Reloading plugins at runtime is complex.
    # For now, we'll just attempt to load DEFAULT and AFTER_INIT again.
    # Note: This doesn't unload existing ones properly in this simple implementation
    # unless PluginManager handles re-loading checks (which it does, it skips if loaded).
    # To fully reload, we'd need to shutdown and clear.
    await pm.load_plugins(PluginTiming.DEFAULT)
    await pm.load_plugins(PluginTiming.AFTER_INIT)
    return {"status": "reloaded", "count": len(pm.plugins)}
