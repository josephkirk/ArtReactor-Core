"""Integration tests for Database API endpoints."""

import pytest
from fastapi.testclient import TestClient

from artreactor.api.dependencies import get_database_manager
from artreactor.app import app
from artreactor.core.managers.database_manager import (
    DatabaseManager,
    SqliteDatabaseProvider,
)

client = TestClient(app)


@pytest.fixture
def temp_database_manager(tmp_path):
    """Create a temporary database manager for testing."""
    db_path = tmp_path / "test_api_database.db"
    provider = SqliteDatabaseProvider(str(db_path))
    return DatabaseManager(provider)


@pytest.fixture
def override_dependency(temp_database_manager):
    """Override the database manager dependency for testing."""
    app.dependency_overrides[get_database_manager] = lambda: temp_database_manager
    yield
    app.dependency_overrides = {}


def test_set_and_get_data_via_api(override_dependency):
    """Test storing and retrieving data through the API."""
    # Set data
    set_response = client.post(
        "/database/set",
        json={
            "collection": "assets",
            "key": "asset_001",
            "data": {"name": "Character Model", "type": "3d", "version": 1},
        },
    )
    assert set_response.status_code == 200
    set_data = set_response.json()
    assert set_data["status"] == "success"
    assert set_data["collection"] == "assets"
    assert set_data["key"] == "asset_001"

    # Get data
    get_response = client.post(
        "/database/get", json={"collection": "assets", "key": "asset_001"}
    )
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["key"] == "asset_001"
    assert get_data["data"]["name"] == "Character Model"
    assert get_data["data"]["version"] == 1


def test_get_nonexistent_data(override_dependency):
    """Test retrieving data that doesn't exist returns 404."""
    response = client.post(
        "/database/get", json={"collection": "nonexistent", "key": "missing"}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_existing_data(override_dependency):
    """Test updating existing data through the API."""
    # Initial data
    client.post(
        "/database/set",
        json={
            "collection": "projects",
            "key": "project_1",
            "data": {"status": "draft", "progress": 10},
        },
    )

    # Update data
    client.post(
        "/database/set",
        json={
            "collection": "projects",
            "key": "project_1",
            "data": {"status": "in_progress", "progress": 50},
        },
    )

    # Verify update
    response = client.post(
        "/database/get", json={"collection": "projects", "key": "project_1"}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "in_progress"
    assert data["progress"] == 50


def test_remove_data(override_dependency):
    """Test removing data through the API."""
    # Set data
    client.post(
        "/database/set",
        json={"collection": "temp", "key": "temp_key", "data": {"value": "temporary"}},
    )

    # Remove data
    remove_response = client.post(
        "/database/remove", json={"collection": "temp", "key": "temp_key"}
    )
    assert remove_response.status_code == 200
    remove_data = remove_response.json()
    assert remove_data["status"] == "success"
    assert remove_data["removed"] is True

    # Verify removal
    get_response = client.post(
        "/database/get", json={"collection": "temp", "key": "temp_key"}
    )
    assert get_response.status_code == 404


def test_remove_nonexistent_data(override_dependency):
    """Test removing data that doesn't exist returns success but removed=False."""
    response = client.post(
        "/database/remove", json={"collection": "test", "key": "missing"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["removed"] is False


def test_list_keys_in_collection(override_dependency):
    """Test listing keys in a collection through the API."""
    # Add multiple items
    for i in range(5):
        client.post(
            "/database/set",
            json={
                "collection": "metadata",
                "key": f"key_{i}",
                "data": {"index": i},
            },
        )

    # List keys
    response = client.post("/database/list-keys", json={"collection": "metadata"})
    assert response.status_code == 200
    data = response.json()
    assert data["collection"] == "metadata"
    assert len(data["keys"]) == 5
    assert "key_0" in data["keys"]
    assert "key_4" in data["keys"]


def test_list_keys_empty_collection(override_dependency):
    """Test listing keys in an empty collection returns empty list."""
    response = client.post("/database/list-keys", json={"collection": "empty"})
    assert response.status_code == 200
    data = response.json()
    assert data["keys"] == []


def test_list_collections(override_dependency):
    """Test listing all collections through the API."""
    # Add data to multiple collections
    client.post(
        "/database/set",
        json={"collection": "assets", "key": "a1", "data": {"type": "asset"}},
    )
    client.post(
        "/database/set",
        json={"collection": "projects", "key": "p1", "data": {"type": "project"}},
    )
    client.post(
        "/database/set",
        json={"collection": "metadata", "key": "m1", "data": {"type": "meta"}},
    )

    # List collections
    response = client.get("/database/collections")
    assert response.status_code == 200
    data = response.json()
    assert len(data["collections"]) == 3
    assert "assets" in data["collections"]
    assert "projects" in data["collections"]
    assert "metadata" in data["collections"]


def test_list_collections_empty_database(override_dependency):
    """Test listing collections in an empty database returns empty list."""
    response = client.get("/database/collections")
    assert response.status_code == 200
    data = response.json()
    assert data["collections"] == []


def test_complex_json_via_api(override_dependency):
    """Test storing and retrieving complex nested JSON through the API."""
    complex_data = {
        "pipeline": {
            "stages": [
                {"name": "modeling", "status": "complete", "duration": 120},
                {"name": "texturing", "status": "in_progress", "duration": 60},
            ],
            "metadata": {
                "author": "Artist Name",
                "tags": ["game", "character", "hero"],
            },
        },
        "assets": {"meshes": 15, "textures": 30, "materials": 8},
    }

    # Set complex data
    set_response = client.post(
        "/database/set",
        json={"collection": "pipelines", "key": "pipeline_001", "data": complex_data},
    )
    assert set_response.status_code == 200

    # Get and verify
    get_response = client.post(
        "/database/get", json={"collection": "pipelines", "key": "pipeline_001"}
    )
    assert get_response.status_code == 200
    retrieved = get_response.json()["data"]
    assert retrieved == complex_data
    assert retrieved["pipeline"]["stages"][1]["status"] == "in_progress"
    assert len(retrieved["pipeline"]["metadata"]["tags"]) == 3


def test_multiple_collections_isolation(override_dependency):
    """Test that collections properly isolate their data."""
    # Same key in different collections
    client.post(
        "/database/set",
        json={"collection": "collection_a", "key": "shared", "data": {"source": "A"}},
    )
    client.post(
        "/database/set",
        json={"collection": "collection_b", "key": "shared", "data": {"source": "B"}},
    )

    # Verify each collection has its own data
    response_a = client.post(
        "/database/get", json={"collection": "collection_a", "key": "shared"}
    )
    response_b = client.post(
        "/database/get", json={"collection": "collection_b", "key": "shared"}
    )

    assert response_a.json()["data"]["source"] == "A"
    assert response_b.json()["data"]["source"] == "B"
