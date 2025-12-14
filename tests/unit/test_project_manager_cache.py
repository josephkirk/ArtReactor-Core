"""Unit tests for ProjectManager caching functionality."""

import logging

import pytest

from artreactor.core.managers.database_manager import (
    DatabaseManager,
    SqliteDatabaseProvider,
)
from artreactor.core.managers.project_manager import ProjectManager

from ..mocks.mock_project_manager_provider import MockProjectManagerProvider


@pytest.fixture
def database_manager(tmp_path):
    """Create a database manager for testing."""
    db_path = tmp_path / "test_cache.db"
    provider = SqliteDatabaseProvider(str(db_path))
    return DatabaseManager(provider)


@pytest.fixture
def mock_provider():
    """Create a mock external provider."""
    return MockProjectManagerProvider()


def test_cache_miss_fetches_from_provider(database_manager, mock_provider):
    """Test that cache miss triggers fetch from external provider."""
    # Setup mock provider with a project
    mock_provider.add_mock_project("test-project", "/path/to/project", "Test Project")

    pm = ProjectManager(database_manager, provider=mock_provider)

    # First call should fetch from provider
    project = pm.get_project("test-project")
    assert project is not None
    assert project.name == "test-project"
    assert len(mock_provider.fetch_project_calls) == 1


def test_cache_hit_skips_provider(database_manager, mock_provider):
    """Test that cache hit doesn't call external provider."""
    # Setup mock provider
    mock_provider.add_mock_project("cached-project", "/path/to/cached", "Cached")

    pm = ProjectManager(database_manager, provider=mock_provider)

    # First call fetches and caches
    pm.get_project("cached-project")
    assert len(mock_provider.fetch_project_calls) == 1

    # Second call should use cache
    project = pm.get_project("cached-project")
    assert project is not None
    assert project.name == "cached-project"
    # Should not call provider again
    assert len(mock_provider.fetch_project_calls) == 1


def test_list_projects_with_provider_fetches_and_caches(
    database_manager, mock_provider
):
    """Test that list_projects fetches from provider and caches results."""
    # Setup mock provider with multiple projects
    mock_provider.add_mock_project("project1", "/path1", "Project 1")
    mock_provider.add_mock_project("project2", "/path2", "Project 2")

    pm = ProjectManager(database_manager, provider=mock_provider)

    # List projects should fetch from provider
    projects = pm.list_projects()
    assert len(projects) == 2
    assert len(mock_provider.fetch_projects_calls) == 1

    # Verify all projects are cached
    cached_project1 = pm.get_project("project1")
    cached_project2 = pm.get_project("project2")
    assert cached_project1 is not None
    assert cached_project2 is not None
    # Should not call fetch_project since they're cached
    assert len(mock_provider.fetch_project_calls) == 0


def test_list_projects_without_provider_returns_cached(database_manager):
    """Test that list_projects without provider returns cached projects."""
    pm = ProjectManager(database_manager, provider=None)

    # Create projects in cache
    pm.create_project("local1", "/path1", "Local 1")
    pm.create_project("local2", "/path2", "Local 2")

    # List should return cached projects
    projects = pm.list_projects()
    assert len(projects) == 2
    names = [p.name for p in projects]
    assert "local1" in names
    assert "local2" in names


def test_create_project_stores_in_cache(database_manager):
    """Test that create_project stores in cache."""
    pm = ProjectManager(database_manager, provider=None)

    project = pm.create_project("new-project", "/path", "New Project")
    assert project.name == "new-project"

    # Verify it's in cache
    cached = pm.get_project("new-project")
    assert cached is not None
    assert cached.name == "new-project"


def test_create_duplicate_project_raises_error(database_manager):
    """Test that creating duplicate project raises error."""
    pm = ProjectManager(database_manager, provider=None)

    pm.create_project("duplicate", "/path", "First")

    with pytest.raises(ValueError, match="already exists"):
        pm.create_project("duplicate", "/path2", "Second")


def test_delete_project_removes_from_cache(database_manager):
    """Test that delete removes project from cache."""
    pm = ProjectManager(database_manager, provider=None)

    pm.create_project("to-delete", "/path", "Will be deleted")
    assert pm.get_project("to-delete") is not None

    pm.delete_project("to-delete")
    assert pm.get_project("to-delete") is None


def test_clear_cache_removes_all_projects(database_manager, mock_provider):
    """Test that clear_cache removes all cached projects."""
    mock_provider.add_mock_project("project1", "/path1")
    mock_provider.add_mock_project("project2", "/path2")

    pm = ProjectManager(database_manager, provider=mock_provider)

    # Fetch and cache projects
    pm.list_projects()
    assert len(pm.list_projects()) == 2

    # Clear cache
    pm.clear_cache()

    # Without provider fetching again, should be empty
    pm_no_provider = ProjectManager(database_manager, provider=None)
    assert len(pm_no_provider.list_projects()) == 0


def test_nonexistent_project_returns_none(database_manager, mock_provider):
    """Test that nonexistent project returns None."""
    pm = ProjectManager(database_manager, provider=mock_provider)

    project = pm.get_project("nonexistent")
    assert project is None


def test_project_datetime_serialization(database_manager):
    """Test that project datetime fields are properly serialized."""
    pm = ProjectManager(database_manager, provider=None)

    # Create project (which has created_at datetime)
    project = pm.create_project("datetime-test", "/path", "Test")
    assert project.created_at is not None

    # Retrieve from cache
    cached = pm.get_project("datetime-test")
    assert cached is not None
    # Datetime should be reconstructed (as string from JSON, but still valid)

    assert "created_at" in cached.model_dump()


def test_prefetch_entities_on_project_fetch(database_manager, mock_provider):
    """Test that entities are prefetched and cached when project is fetched."""
    # Setup mock provider with project and entities
    mock_provider.add_mock_project("game_project", "/path/to/game")

    # Add entities to mock provider
    from artreactor.models.domain import Entity, EntityType, Version

    entity1 = Entity(
        uri="entity://game_project/asset/hero",
        name="hero",
        project_name="game_project",
        type=EntityType.ASSET,
        versions=[Version(id="v1")],
    )
    entity2 = Entity(
        uri="entity://game_project/level/level1",
        name="level1",
        project_name="game_project",
        type=EntityType.LEVEL,
        versions=[Version(id="v1")],
    )

    mock_provider.add_mock_entity(entity1)
    mock_provider.add_mock_entity(entity2)

    pm = ProjectManager(database_manager, provider=mock_provider)

    # Fetch project
    project = pm.get_project("game_project")
    assert project is not None

    # Verify prefetch was called
    assert "game_project" in mock_provider.prefetch_entities_calls

    # Verify entities are cached in the entities_cache collection
    # We access the cache directly to verify
    cached_entities = database_manager.get_all("entities_cache")
    assert len(cached_entities) == 2

    # Check if correct entities are cached
    # Note: URI parsing logic in ProjectManager._cache_entities determines the key
    # base_uri = "entity://game_project/asset/hero"
    assert "entity://game_project/asset/hero" in cached_entities
    assert "entity://game_project/level/level1" in cached_entities


def test_prefetch_entities_exception_logged(database_manager, mock_provider, caplog):
    """Test that exceptions during entity prefetch are logged."""
    # Setup mock provider with a project
    mock_provider.add_mock_project("test_project", "/path/to/test")

    # Create a provider that raises an exception on prefetch
    class FailingProvider:
        def fetch_project(self, name: str):
            from artreactor.models.domain import Project

            return Project(name=name, path="/path/to/test", description="Test")

        def prefetch_entities_for_project(self, name: str):
            raise RuntimeError("Simulated prefetch failure")

    failing_provider = FailingProvider()
    pm = ProjectManager(database_manager, provider=failing_provider)

    # Fetch project - should not raise exception
    with caplog.at_level(logging.WARNING):
        project = pm.get_project("test_project")

    # Project should still be retrieved despite prefetch failure
    assert project is not None
    assert project.name == "test_project"

    # Verify the exception was logged
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "WARNING"
    assert "Failed to prefetch entities for project 'test_project'" in caplog.text
    assert "Simulated prefetch failure" in caplog.text


def test_prefetch_entities_attribute_error_logged(database_manager, caplog):
    """Test that AttributeError during entity prefetch is logged."""

    # Create a provider without prefetch_entities_for_project method
    class MinimalProvider:
        def fetch_project(self, name: str):
            from artreactor.models.domain import Project

            return Project(name=name, path="/path/to/test", description="Test")

    minimal_provider = MinimalProvider()
    pm = ProjectManager(database_manager, provider=minimal_provider)

    # Fetch project - should not raise exception
    with caplog.at_level(logging.WARNING):
        project = pm.get_project("test_project")

    # Project should still be retrieved despite missing method
    assert project is not None
    assert project.name == "test_project"

    # Verify the AttributeError was logged
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "WARNING"
    assert "Failed to prefetch entities for project 'test_project'" in caplog.text
