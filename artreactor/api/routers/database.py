"""Database API Router.

Provides REST endpoints for database operations, allowing plugins and
external systems to store and query JSON-like data.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from artreactor.api.dependencies import get_database_manager
from artreactor.core.managers.database_manager import DatabaseManager

router = APIRouter(prefix="/database", tags=["database"])


class DataSetRequest(BaseModel):
    """Request model for setting data."""

    collection: str
    key: str
    data: Dict[str, Any]


class DataGetRequest(BaseModel):
    """Request model for getting data."""

    collection: str
    key: str


class DataRemoveRequest(BaseModel):
    """Request model for removing data."""

    collection: str
    key: str


class ListKeysRequest(BaseModel):
    """Request model for listing keys in a collection."""

    collection: str


@router.post("/set")
async def set_data(
    request: DataSetRequest, db: DatabaseManager = Depends(get_database_manager)
):
    """Store or update data in the database.

    Args:
        request: Contains collection name, key, and data to store

    Returns:
        Success status and the key that was set
    """
    db.set(request.collection, request.key, request.data)
    return {"status": "success", "collection": request.collection, "key": request.key}


@router.post("/get")
async def get_data(
    request: DataGetRequest, db: DatabaseManager = Depends(get_database_manager)
):
    """Retrieve data from the database.

    Args:
        request: Contains collection name and key

    Returns:
        The stored data, or 404 if not found
    """
    data = db.get(request.collection, request.key)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Data not found for key '{request.key}' in collection '{request.collection}'",
        )
    return {"collection": request.collection, "key": request.key, "data": data}


@router.post("/remove")
async def remove_data(
    request: DataRemoveRequest, db: DatabaseManager = Depends(get_database_manager)
):
    """Remove data from the database.

    Args:
        request: Contains collection name and key

    Returns:
        Success status and whether data was removed
    """
    removed = db.remove(request.collection, request.key)
    return {
        "status": "success",
        "collection": request.collection,
        "key": request.key,
        "removed": removed,
    }


@router.post("/list-keys")
async def list_keys(
    request: ListKeysRequest, db: DatabaseManager = Depends(get_database_manager)
):
    """List all keys in a collection.

    Args:
        request: Contains collection name

    Returns:
        List of all keys in the collection
    """
    keys = db.list_keys(request.collection)
    return {"collection": request.collection, "keys": keys}


@router.get("/collections")
async def list_collections(db: DatabaseManager = Depends(get_database_manager)):
    """List all collections in the database.

    Returns:
        List of all collection names
    """
    collections = db.list_collections()
    return {"collections": collections}
