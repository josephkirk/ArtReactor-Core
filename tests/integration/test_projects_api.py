import pytest
from fastapi.testclient import TestClient
from artreactor.app import app
from artreactor.api.dependencies import get_project_manager
from artreactor.core.managers.project_manager import ProjectManager
from artreactor.core.managers.database_manager import (
    DatabaseManager,
    SqliteDatabaseProvider,
)

client = TestClient(app)


@pytest.fixture
def temp_project_manager(tmp_path):
    db_path = tmp_path / "test_projects.db"
    db_provider = SqliteDatabaseProvider(str(db_path))
    db_manager = DatabaseManager(db_provider)
    return ProjectManager(db_manager, provider=None)


@pytest.fixture
def override_dependency(temp_project_manager):
    app.dependency_overrides[get_project_manager] = lambda: temp_project_manager
    yield
    app.dependency_overrides = {}


def test_create_and_list_projects(override_dependency):
    # Create
    response = client.post(
        "/projects/",
        json={
            "name": "test-project",
            "path": "/tmp/test",
            "description": "Test Project",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test-project"

    # List
    response = client.get("/projects/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "test-project"


def test_create_duplicate_project(override_dependency):
    client.post("/projects/", json={"name": "p1", "path": "/p1"})
    response = client.post("/projects/", json={"name": "p1", "path": "/p1"})
    assert response.status_code == 400
