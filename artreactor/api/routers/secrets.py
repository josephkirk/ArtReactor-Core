from typing import Optional

from fastapi import APIRouter, Depends

from artreactor.api.dependencies import get_secret_manager
from artreactor.core.managers.secret_manager import SecretManager
from artreactor.models.api import SecretSetRequest
from artreactor.models.domain import SecretScope

router = APIRouter(prefix="/secrets", tags=["secrets"])


@router.get("/")
async def list_secrets(
    scope: Optional[SecretScope] = None,
    project: Optional[str] = None,
    sm: SecretManager = Depends(get_secret_manager),
):
    # The current SecretManager implementation doesn't support listing keys.
    # We should add it to the ABC and implementation.
    # For now, we'll return a message or implement it if possible.
    # Sqlite implementation can support it.
    # Let's assume we update SecretManager to support listing.
    # But wait, T007 didn't include list_secrets.
    # I should update SecretManager first or just implement get/set for now and return empty list or error.
    # The spec says "List available secret keys".
    # I'll update SecretManager to support listing.
    pass
    return {"message": "Listing not implemented yet"}


@router.post("/")
async def set_secret(
    request: SecretSetRequest, sm: SecretManager = Depends(get_secret_manager)
):
    sm.set_secret(request.key, request.value, request.scope, request.project)
    return {"status": "success", "key": request.key}
