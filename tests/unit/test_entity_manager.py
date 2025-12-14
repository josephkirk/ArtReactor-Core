"""Unit tests for Entity Manager."""

import pytest

from artreactor.core.managers.database_manager import (
    DatabaseManager,
    SqliteDatabaseProvider,
)
from artreactor.core.managers.entity_manager import EntityManager
from artreactor.core.managers.project_manager import ProjectManager
from artreactor.models.domain import Entity, EntityType, ProjectManagerLink, Version

from ..mocks.mock_project_manager_provider import MockProjectManagerProvider


@pytest.fixture
def database_manager(tmp_path):
    """Create a database manager for testing."""
    db_path = tmp_path / "test_entities.db"
    provider = SqliteDatabaseProvider(str(db_path))
    return DatabaseManager(provider)


@pytest.fixture
def mock_provider():
    """Create a mock project manager provider."""
    return MockProjectManagerProvider()


@pytest.fixture
def project_manager(database_manager, mock_provider):
    """Create a project manager with mock provider."""
    return ProjectManager(database_manager, provider=mock_provider)


@pytest.fixture
def entity_manager(database_manager, project_manager):
    """Create an entity manager with database and project manager."""
    return EntityManager(database_manager, project_manager)


@pytest.fixture
def sample_entity():
    """Create a sample entity for testing."""
    return Entity(
        uri="entity://projectA/asset/characters/hero",
        name="hero",
        project_name="projectA",
        type=EntityType.ASSET,
        description="Hero character asset",
        versions=[
            Version(id="v001", env_vars={"ENV": "test"}),
            Version(id="v002", env_vars={"ENV": "prod"}),
        ],
    )


@pytest.mark.asyncio
async def test_add_entity_without_publish(entity_manager, sample_entity):
    """Test adding an entity without publishing to external service."""
    result = await entity_manager.add_entity(sample_entity, publish=False)

    assert result.uri == sample_entity.uri
    assert result.name == sample_entity.name
    assert len(result.versions) == 2


@pytest.mark.asyncio
async def test_add_entity_with_publish(entity_manager, mock_provider, sample_entity):
    """Test adding an entity with publishing to external service."""
    result = await entity_manager.add_entity(sample_entity, publish=True)

    assert result.uri == sample_entity.uri
    assert len(mock_provider.create_entity_calls) == 1
    assert mock_provider.create_entity_calls[0] == sample_entity.uri


@pytest.mark.asyncio
async def test_get_entity_from_cache(entity_manager, sample_entity):
    """Test retrieving an entity from cache."""
    # Add entity to cache
    await entity_manager.add_entity(sample_entity, publish=False)

    # Retrieve from cache
    result = await entity_manager.get_entity(sample_entity.uri)

    assert result is not None
    assert result.uri == sample_entity.uri
    assert result.name == sample_entity.name
    assert len(result.versions) == 2


@pytest.mark.asyncio
async def test_get_entity_with_specific_version(entity_manager, sample_entity):
    """Test retrieving a specific version of an entity."""
    # Add entity to cache
    await entity_manager.add_entity(sample_entity, publish=False)

    # Retrieve specific version
    result = await entity_manager.get_entity(
        "entity://projectA/asset/characters/hero?version=v001"
    )

    assert result is not None
    assert len(result.versions) == 1
    assert result.versions[0].id == "v001"


@pytest.mark.asyncio
async def test_get_entity_from_provider(entity_manager, mock_provider, sample_entity):
    """Test retrieving an entity from external provider when not in cache."""
    # Add entity to mock provider
    mock_provider.add_mock_entity(sample_entity)

    # Retrieve from provider
    result = await entity_manager.get_entity(sample_entity.uri)

    assert result is not None
    assert result.uri == sample_entity.uri
    assert len(mock_provider.get_entity_calls) == 1


@pytest.mark.asyncio
async def test_get_nonexistent_entity(entity_manager):
    """Test retrieving a non-existent entity returns None."""
    result = await entity_manager.get_entity("entity://projectA/asset/nonexistent")

    assert result is None


@pytest.mark.asyncio
async def test_update_entity(entity_manager, sample_entity):
    """Test updating an entity."""
    # Add entity first
    await entity_manager.add_entity(sample_entity, publish=False)

    # Update entity
    updates = {"description": "Updated hero character"}
    result = await entity_manager.update_entity(
        sample_entity.uri, updates, publish=False
    )

    assert result is not None
    assert result.description == "Updated hero character"


@pytest.mark.asyncio
async def test_update_entity_with_publish(entity_manager, mock_provider, sample_entity):
    """Test updating an entity with publish to external service."""
    # Add entity first
    await entity_manager.add_entity(sample_entity, publish=False)

    # Update entity with publish
    updates = {"description": "Updated hero"}
    result = await entity_manager.update_entity(
        sample_entity.uri, updates, publish=True
    )

    assert result is not None
    assert len(mock_provider.update_entity_calls) == 1


@pytest.mark.asyncio
async def test_update_nonexistent_entity(entity_manager):
    """Test updating a non-existent entity returns None."""
    result = await entity_manager.update_entity(
        "entity://projectA/asset/nonexistent",
        {"description": "test"},
        publish=False,
    )

    assert result is None


def test_list_entities(entity_manager, sample_entity):
    """Test listing all entities."""
    # Add some entities
    entity_manager._cache_entity(sample_entity)

    # List all
    entities = entity_manager.list_entities()

    assert len(entities) == 1
    assert entities[0].uri == sample_entity.uri


def test_list_entities_by_type(entity_manager, sample_entity):
    """Test listing entities filtered by type."""
    # Add entity
    entity_manager._cache_entity(sample_entity)

    # Add another entity of different type
    shot_entity = Entity(
        uri="entity://projectA/shot/level1/intro",
        name="intro",
        project_name="projectA",
        type=EntityType.SHOT,
        description="Intro shot",
        versions=[],
    )
    entity_manager._cache_entity(shot_entity)

    # List only assets
    assets = entity_manager.list_entities(entity_type=EntityType.ASSET)
    assert len(assets) == 1
    assert assets[0].type == EntityType.ASSET

    # List only shots
    shots = entity_manager.list_entities(entity_type=EntityType.SHOT)
    assert len(shots) == 1
    assert shots[0].type == EntityType.SHOT


@pytest.mark.asyncio
async def test_resolve_dependencies(entity_manager, sample_entity):
    """Test resolving dependencies for a version."""
    # Create a dependency entity
    dep_entity = Entity(
        uri="entity://projectA/asset/textures/hero_diffuse",
        name="hero_diffuse",
        project_name="projectA",
        type=EntityType.ASSET,
        description="Hero diffuse texture",
        versions=[Version(id="v005")],
    )
    entity_manager._cache_entity(dep_entity)

    # Add dependency to sample entity version
    sample_entity.versions[1].dependencies = {
        "entity://projectA/asset/textures/hero_diffuse": "v005"
    }
    entity_manager._cache_entity(sample_entity)

    # Resolve dependencies
    resolved = await entity_manager.resolve_dependencies(sample_entity, "v002")

    assert len(resolved) == 1
    assert "entity://projectA/asset/textures/hero_diffuse" in resolved
    assert (
        resolved["entity://projectA/asset/textures/hero_diffuse"].name == "hero_diffuse"
    )


@pytest.mark.asyncio
async def test_resolve_dependencies_no_version(entity_manager, sample_entity):
    """Test resolving dependencies for non-existent version."""
    entity_manager._cache_entity(sample_entity)

    resolved = await entity_manager.resolve_dependencies(sample_entity, "v999")

    assert len(resolved) == 0


@pytest.mark.asyncio
async def test_custom_entity_type(entity_manager):
    """Test that custom entity types work without code modification."""
    # Create an entity with a custom type that's not in EntityType constants
    custom_entity = Entity(
        uri="entity://projectA/custom_type/items/special_item",
        name="special_item",
        project_name="projectA",
        type="custom_type",  # Custom type not defined in EntityType constants
        description="A custom entity type",
        versions=[Version(id="v001")],
    )

    # Should be able to add and retrieve without errors
    await entity_manager.add_entity(custom_entity, publish=False)
    result = await entity_manager.get_entity(custom_entity.uri)

    assert result is not None
    assert result.type == "custom_type"
    assert result.name == "special_item"

    # Should be able to list by custom type
    custom_entities = entity_manager.list_entities(entity_type="custom_type")
    assert len(custom_entities) == 1
    assert custom_entities[0].type == "custom_type"


@pytest.mark.asyncio
async def test_entity_with_multiple_project_manager_links(entity_manager):
    """Test entity version with links to multiple project management providers."""
    # Create an entity with version linked to multiple providers
    entity = Entity(
        uri="entity://projectA/asset/characters/hero",
        name="hero",
        project_name="projectA",
        type=EntityType.ASSET,
        description="Hero character tracked in multiple systems",
        versions=[
            Version(
                id="v001",
                project_manager_links=[
                    ProjectManagerLink(
                        provider="kitsu",
                        provider_id="kitsu-asset-123",
                        metadata={"status": "in_progress", "task_id": "task-456"},
                    ),
                    ProjectManagerLink(
                        provider="shotgrid",
                        provider_id="sg-version-789",
                        metadata={"status": "approved", "department": "modeling"},
                    ),
                    ProjectManagerLink(
                        provider="ftrack",
                        provider_id="ftrack-asset-abc",
                        metadata={"status": "review"},
                    ),
                ],
            )
        ],
    )

    # Add and retrieve entity
    await entity_manager.add_entity(entity, publish=False)
    result = await entity_manager.get_entity(entity.uri)

    # Verify entity was stored and retrieved correctly
    assert result is not None
    assert len(result.versions) == 1
    assert len(result.versions[0].project_manager_links) == 3

    # Verify Kitsu link
    kitsu_link = next(
        (
            link
            for link in result.versions[0].project_manager_links
            if link.provider == "kitsu"
        ),
        None,
    )
    assert kitsu_link is not None
    assert kitsu_link.provider_id == "kitsu-asset-123"
    assert kitsu_link.metadata["status"] == "in_progress"
    assert kitsu_link.metadata["task_id"] == "task-456"

    # Verify ShotGrid link
    sg_link = next(
        (
            link
            for link in result.versions[0].project_manager_links
            if link.provider == "shotgrid"
        ),
        None,
    )
    assert sg_link is not None
    assert sg_link.provider_id == "sg-version-789"
    assert sg_link.metadata["department"] == "modeling"

    # Verify Ftrack link
    ftrack_link = next(
        (
            link
            for link in result.versions[0].project_manager_links
            if link.provider == "ftrack"
        ),
        None,
    )
    assert ftrack_link is not None
    assert ftrack_link.provider_id == "ftrack-asset-abc"


@pytest.mark.asyncio
async def test_entity_version_without_project_manager_links(entity_manager):
    """Test that entity versions work fine without any project manager links."""
    # Create entity with no project manager links (backwards compatibility)
    entity = Entity(
        uri="entity://projectA/asset/props/sword",
        name="sword",
        project_name="projectA",
        type=EntityType.ASSET,
        versions=[Version(id="v001")],  # No project_manager_links specified
    )

    await entity_manager.add_entity(entity, publish=False)
    result = await entity_manager.get_entity(entity.uri)

    assert result is not None
    assert len(result.versions) == 1
    assert len(result.versions[0].project_manager_links) == 0  # Empty list by default


@pytest.mark.asyncio
async def test_entity_added_event_emission(entity_manager, sample_entity):
    """Test that entity.added event is emitted when adding an entity."""
    # Track event emissions
    events_received = []

    async def on_entity_added(entity):
        events_received.append(("entity.added", entity))

    # Register event listener
    entity_manager.event_manager.on("entity.added", on_entity_added)

    # Add entity
    await entity_manager.add_entity(sample_entity, publish=False)

    # Verify event was emitted
    assert len(events_received) == 1
    assert events_received[0][0] == "entity.added"
    assert events_received[0][1].uri == sample_entity.uri


@pytest.mark.asyncio
async def test_entity_updated_event_emission(entity_manager, sample_entity):
    """Test that entity.updated event is emitted when updating an entity."""
    # Add entity first
    await entity_manager.add_entity(sample_entity, publish=False)

    # Track event emissions
    events_received = []

    async def on_entity_updated(uri, entity):
        events_received.append(("entity.updated", uri, entity))

    # Register event listener
    entity_manager.event_manager.on("entity.updated", on_entity_updated)

    # Update entity
    updates = {"description": "Updated description"}
    await entity_manager.update_entity(sample_entity.uri, updates, publish=False)

    # Verify event was emitted
    assert len(events_received) == 1
    assert events_received[0][0] == "entity.updated"
    assert events_received[0][1] == sample_entity.uri
    assert events_received[0][2].description == "Updated description"


@pytest.mark.asyncio
async def test_entity_open_method_emits_event(entity_manager, sample_entity):
    """Test that entity.opened event is emitted when opening an entity."""
    # Add entity first
    await entity_manager.add_entity(sample_entity, publish=False)

    # Track event emissions
    events_received = []

    async def on_entity_opened(uri, version_id):
        events_received.append(("entity.opened", uri, version_id))

    # Register event listener
    entity_manager.event_manager.on("entity.opened", on_entity_opened)

    # Try to open entity (should raise NotImplementedError but still emit event)
    with pytest.raises(NotImplementedError):
        await entity_manager.open(sample_entity.uri, version_id="v001")

    # Verify event was emitted before NotImplementedError
    assert len(events_received) == 1
    assert events_received[0][0] == "entity.opened"
    assert events_received[0][1] == sample_entity.uri
    assert events_received[0][2] == "v001"


@pytest.mark.asyncio
async def test_entity_open_without_version(entity_manager, sample_entity):
    """Test that open method can be called without specifying a version."""
    # Add entity first
    await entity_manager.add_entity(sample_entity, publish=False)

    # Track event emissions
    events_received = []

    async def on_entity_opened(uri, version_id):
        events_received.append(("entity.opened", uri, version_id))

    # Register event listener
    entity_manager.event_manager.on("entity.opened", on_entity_opened)

    # Try to open entity without version
    with pytest.raises(NotImplementedError):
        await entity_manager.open(sample_entity.uri)

    # Verify event was emitted with None version_id
    assert len(events_received) == 1
    assert events_received[0][0] == "entity.opened"
    assert events_received[0][1] == sample_entity.uri
    assert events_received[0][2] is None


@pytest.mark.asyncio
async def test_entity_open_nonexistent_entity(entity_manager):
    """Test that opening a non-existent entity raises ValueError."""
    with pytest.raises(ValueError, match="Entity not found"):
        await entity_manager.open("entity://projectA/asset/nonexistent")
