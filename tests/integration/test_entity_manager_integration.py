"""Integration tests for Entity Manager with database and project manager adapters."""

import pytest

from artreactor.core.managers.database_manager import (
    DatabaseManager,
    SqliteDatabaseProvider,
)
from artreactor.core.managers.entity_manager import EntityManager
from artreactor.core.managers.project_manager import ProjectManager
from artreactor.models.domain import (
    Entity,
    EntityType,
    ProjectManagerLink,
    SoftwareInfo,
    Version,
    VersionControlInfo,
)

from ..mocks.mock_project_manager_provider import MockProjectManagerProvider


@pytest.fixture
def database_manager(tmp_path):
    """Create a database manager for testing."""
    db_path = tmp_path / "test_entities_integration.db"
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


@pytest.mark.asyncio
async def test_full_workflow_with_dependencies(entity_manager):
    """Test a complete workflow: create entity with dependencies, retrieve, update."""
    # Create a texture dependency entity
    texture_entity = Entity(
        uri="entity://projectA/asset/textures/hero_diffuse",
        name="hero_diffuse",
        project_name="projectA",
        type=EntityType.ASSET,
        description="Hero diffuse texture",
        versions=[
            Version(
                id="v001",
                software=SoftwareInfo(name="Substance", version="2024.1"),
                env_vars={"RESOLUTION": "4096"},
            )
        ],
    )
    await entity_manager.add_entity(texture_entity, publish=False)

    # Create a hero asset that depends on the texture
    hero_entity = Entity(
        uri="entity://projectA/asset/characters/hero",
        name="hero",
        project_name="projectA",
        type=EntityType.ASSET,
        description="Hero character asset",
        versions=[
            Version(
                id="v001",
                version_control=VersionControlInfo(
                    method="git",
                    repository="https://git.example.com/assets",
                    commit="abc123",
                ),
                software=SoftwareInfo(name="Maya", version="2024"),
                dependencies={"entity://projectA/asset/textures/hero_diffuse": "v001"},
            )
        ],
    )
    await entity_manager.add_entity(hero_entity, publish=False)

    # Retrieve the hero entity
    retrieved = await entity_manager.get_entity(hero_entity.uri)
    assert retrieved is not None
    assert retrieved.name == "hero"
    assert len(retrieved.versions) == 1
    assert retrieved.versions[0].software.name == "Maya"

    # Resolve dependencies
    deps = await entity_manager.resolve_dependencies(retrieved, "v001")
    assert len(deps) == 1
    assert "entity://projectA/asset/textures/hero_diffuse" in deps
    assert deps["entity://projectA/asset/textures/hero_diffuse"].name == "hero_diffuse"

    # Update the hero entity
    updates = {"description": "Updated hero character"}
    updated = await entity_manager.update_entity(
        hero_entity.uri, updates, publish=False
    )
    assert updated.description == "Updated hero character"

    # Verify cache persistence
    retrieved_again = await entity_manager.get_entity(hero_entity.uri)
    assert retrieved_again.description == "Updated hero character"


@pytest.mark.asyncio
async def test_cache_hit_avoids_provider_calls(entity_manager, mock_provider):
    """Test that cached entities don't trigger provider calls."""
    entity = Entity(
        uri="entity://projectA/asset/props/sword",
        name="sword",
        project_name="projectA",
        type=EntityType.ASSET,
        description="Sword prop",
        versions=[Version(id="v001")],
    )

    # Add to cache
    await entity_manager.add_entity(entity, publish=False)

    # Clear provider call logs
    mock_provider.get_entity_calls.clear()

    # Retrieve from cache
    result = await entity_manager.get_entity(entity.uri)

    assert result is not None
    # No provider calls should have been made

    assert len(mock_provider.get_entity_calls) == 0


@pytest.mark.asyncio
async def test_provider_fallback_when_not_in_cache(entity_manager, mock_provider):
    """Test that providers are queried when entity is not in cache."""
    entity = Entity(
        uri="entity://projectA/shot/level1/intro",
        name="intro",
        project_name="projectA",
        type=EntityType.SHOT,
        description="Intro shot",
        versions=[Version(id="v001")],
    )

    # Add to provider's storage
    mock_provider.add_mock_entity(entity)

    # Retrieve (should fetch from provider and cache)
    result = await entity_manager.get_entity(entity.uri)

    assert result is not None
    assert result.name == "intro"
    # Provider should have been called
    assert len(mock_provider.get_entity_calls) == 1

    # Second retrieval should hit cache
    mock_provider.get_entity_calls.clear()
    result2 = await entity_manager.get_entity(entity.uri)
    assert result2 is not None
    assert len(mock_provider.get_entity_calls) == 0


@pytest.mark.asyncio
async def test_specific_version_resolution(entity_manager):
    """Test resolving specific versions from URIs."""
    entity = Entity(
        uri="entity://projectA/asset/vehicles/car",
        name="car",
        project_name="projectA",
        type=EntityType.ASSET,
        description="Car asset",
        versions=[
            Version(id="v001", env_vars={"LOD": "high"}),
            Version(id="v002", env_vars={"LOD": "medium"}),
            Version(id="v003", env_vars={"LOD": "low"}),
        ],
    )
    await entity_manager.add_entity(entity, publish=False)

    # Get specific version
    result = await entity_manager.get_entity(
        "entity://projectA/asset/vehicles/car?version=v002"
    )

    assert result is not None
    assert len(result.versions) == 1
    assert result.versions[0].id == "v002"
    assert result.versions[0].env_vars["LOD"] == "medium"


@pytest.mark.asyncio
async def test_publish_to_external_provider(entity_manager, mock_provider):
    """Test publishing entities to external providers."""
    entity = Entity(
        uri="entity://projectA/sequence/act1/scene1",
        name="scene1",
        project_name="projectA",
        type=EntityType.SEQUENCE,
        description="First scene",
        versions=[Version(id="v001")],
    )

    # Add with publish=True
    result = await entity_manager.add_entity(entity, publish=True)

    assert result is not None
    # Provider should have create_entity called
    assert len(mock_provider.create_entity_calls) == 1
    assert mock_provider.create_entity_calls[0] == entity.uri


@pytest.mark.asyncio
async def test_list_entities_by_type(entity_manager):
    """Test listing and filtering entities by type."""
    # Add multiple entities of different types
    asset1 = Entity(
        uri="entity://projectA/asset/props/item1",
        name="item1",
        project_name="projectA",
        type=EntityType.ASSET,
        versions=[],
    )
    asset2 = Entity(
        uri="entity://projectA/asset/props/item2",
        name="item2",
        project_name="projectA",
        type=EntityType.ASSET,
        versions=[],
    )
    shot1 = Entity(
        uri="entity://projectA/shot/level1/shot1",
        name="shot1",
        project_name="projectA",
        type=EntityType.SHOT,
        versions=[],
    )

    await entity_manager.add_entity(asset1, publish=False)
    await entity_manager.add_entity(asset2, publish=False)
    await entity_manager.add_entity(shot1, publish=False)

    # List all assets
    assets = entity_manager.list_entities(entity_type=EntityType.ASSET)
    assert len(assets) == 2
    assert all(e.type == EntityType.ASSET for e in assets)

    # List all shots
    shots = entity_manager.list_entities(entity_type=EntityType.SHOT)
    assert len(shots) == 1
    assert shots[0].type == EntityType.SHOT

    # List all entities
    all_entities = entity_manager.list_entities()
    assert len(all_entities) == 3


@pytest.mark.asyncio
async def test_complex_dependency_chain(entity_manager):
    """Test resolving complex dependency chains."""
    # Create a chain: hero -> rig -> skeleton
    skeleton = Entity(
        uri="entity://projectA/asset/rigs/base_skeleton",
        name="base_skeleton",
        project_name="projectA",
        type=EntityType.ASSET,
        versions=[Version(id="v001")],
    )

    rig = Entity(
        uri="entity://projectA/asset/rigs/hero_rig",
        name="hero_rig",
        project_name="projectA",
        type=EntityType.ASSET,
        versions=[
            Version(
                id="v001",
                dependencies={"entity://projectA/asset/rigs/base_skeleton": "v001"},
            )
        ],
    )

    hero = Entity(
        uri="entity://projectA/asset/characters/hero",
        name="hero",
        project_name="projectA",
        type=EntityType.ASSET,
        versions=[
            Version(
                id="v001",
                dependencies={"entity://projectA/asset/rigs/hero_rig": "v001"},
            )
        ],
    )

    # Add all entities
    await entity_manager.add_entity(skeleton, publish=False)
    await entity_manager.add_entity(rig, publish=False)
    await entity_manager.add_entity(hero, publish=False)

    # Resolve hero dependencies
    hero_deps = await entity_manager.resolve_dependencies(hero, "v001")
    assert len(hero_deps) == 1
    assert "entity://projectA/asset/rigs/hero_rig" in hero_deps

    # Resolve rig dependencies
    rig_deps = await entity_manager.resolve_dependencies(rig, "v001")
    assert len(rig_deps) == 1
    assert "entity://projectA/asset/rigs/base_skeleton" in rig_deps


@pytest.mark.asyncio
async def test_multi_provider_workflow(entity_manager):
    """Test complete workflow with multiple project management providers."""
    # Create an entity version that will be synced to multiple providers
    entity = Entity(
        uri="entity://studioProject/asset/characters/protagonist",
        name="protagonist",
        project_name="studioProject",
        type=EntityType.ASSET,
        description="Main character tracked across multiple systems",
        versions=[
            Version(
                id="v001",
                software=SoftwareInfo(name="Maya", version="2024"),
                version_control=VersionControlInfo(
                    method="git", repository="git@studio.com/assets", commit="abc123"
                ),
                project_manager_links=[],  # Will be populated as we sync
            )
        ],
    )

    # Add entity locally
    await entity_manager.add_entity(entity, publish=False)

    # Simulate syncing to Kitsu
    retrieved = await entity_manager.get_entity(entity.uri)
    retrieved.versions[0].project_manager_links.append(
        ProjectManagerLink(
            provider="kitsu",
            provider_id="kitsu-char-001",
            metadata={
                "project_id": "proj-123",
                "entity_type_id": "char-type-1",
                "status": "wip",
            },
        )
    )
    await entity_manager.update_entity(
        entity.uri, {"versions": retrieved.versions}, publish=False
    )

    # Simulate syncing to ShotGrid
    retrieved = await entity_manager.get_entity(entity.uri)
    retrieved.versions[0].project_manager_links.append(
        ProjectManagerLink(
            provider="shotgrid",
            provider_id="sg-asset-456",
            metadata={
                "project_name": "StudioProject",
                "pipeline_step": "modeling",
                "status_code": "rev",
            },
        )
    )
    await entity_manager.update_entity(
        entity.uri, {"versions": retrieved.versions}, publish=False
    )

    # Verify final state
    final = await entity_manager.get_entity(entity.uri)
    assert len(final.versions[0].project_manager_links) == 2

    # Verify we can find specific provider links
    providers = {link.provider for link in final.versions[0].project_manager_links}
    assert "kitsu" in providers
    assert "shotgrid" in providers

    # Verify provider-specific data
    kitsu_link = next(
        link
        for link in final.versions[0].project_manager_links
        if link.provider == "kitsu"
    )
    assert kitsu_link.provider_id == "kitsu-char-001"
    assert kitsu_link.metadata["status"] == "wip"

    sg_link = next(
        link
        for link in final.versions[0].project_manager_links
        if link.provider == "shotgrid"
    )
    assert sg_link.provider_id == "sg-asset-456"
    assert sg_link.metadata["pipeline_step"] == "modeling"
