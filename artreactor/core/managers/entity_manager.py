"""Entity Manager for ArtReactor Core.

This module provides the central service for managing entities (assets, shots,
sequences, levels) with URI resolution, versioning, and external project
manager integration.
"""

from typing import Any, Dict, List, Optional

from artreactor.core.events import event_manager
from artreactor.core.managers.database_manager import DatabaseManager
from artreactor.core.managers.project_manager import ProjectManager
from artreactor.core.utils.uri_parser import get_entity_cache_key, parse_entity_uri
from artreactor.models.domain import Entity


class EntityManager:
    """Entity Manager with database caching and project manager integration.

    This manager uses a database for caching entity data and can optionally
    sync with external project management services (Kitsu, Ftrack, ShotGrid).

    Events emitted:
        - entity.added: When a new entity is added (args: entity)
        - entity.updated: When an entity is updated (args: uri, entity)
        - entity.opened: When an entity is opened (args: uri, version_id)
    """

    CACHE_COLLECTION = "entities_cache"

    def __init__(
        self,
        db_manager: DatabaseManager,
        project_manager: Optional[ProjectManager] = None,
        event_manager_instance=None,
    ):
        """Initialize the entity manager.

        Args:
            db_manager: DatabaseManager instance for caching
            project_manager: Optional ProjectManager instance for external sync
            event_manager_instance: Optional EventManager instance (defaults to global)
        """
        self.db = db_manager
        self.project_manager = project_manager
        self.event_manager = event_manager_instance or event_manager

    async def get_entity(self, uri: str) -> Optional[Entity]:
        """Resolve URI to Entity.

        Args:
            uri: The entity URI to resolve

        Returns:
            Entity if found, None otherwise
        """
        # Parse URI to extract base URI (without version)
        parsed = parse_entity_uri(uri)
        base_uri = get_entity_cache_key(uri)

        # Try cache first
        cached = self.db.get(self.CACHE_COLLECTION, base_uri)
        if cached:
            entity = Entity(**cached)

            # If a specific version is requested, filter to that version
            if parsed.version:
                entity.versions = [v for v in entity.versions if v.id == parsed.version]
                if not entity.versions:
                    # Version not in cache, try external providers
                    return await self._fetch_from_providers(uri, parsed.version)

            return entity

        # If not in cache, try external providers
        return await self._fetch_from_providers(uri)

    async def _fetch_from_providers(
        self, uri: str, version: Optional[str] = None
    ) -> Optional[Entity]:
        """Fetch entity from external project managers.

        Args:
            uri: The entity URI
            version: Optional specific version to fetch

        Returns:
            Entity if found, None otherwise. If a specific version is requested,
            returns an Entity with only that version filtered.
        """
        if not self.project_manager or not self.project_manager.provider:
            return None

        provider = self.project_manager.provider

        if version:
            # Fetch specific version object first to verify it exists
            version_obj = await provider.get_version(uri, version)
            if not version_obj:
                # Version doesn't exist
                return None

            # Get the full entity to cache it with all versions
            entity = await provider.get_entity(uri)
            if entity:
                # Cache the full entity (with all versions)
                self._cache_entity(entity)

                # Return a copy of the entity filtered to just the requested version
                # This ensures the caller gets only the version they asked for
                # Use base URI (without version parameter) for consistency
                base_uri = get_entity_cache_key(uri)
                filtered_entity = Entity(
                    uri=base_uri,
                    name=entity.name,
                    project_name=entity.project_name,
                    type=entity.type,
                    description=entity.description,
                    versions=[v for v in entity.versions if v.id == version],
                )
                return filtered_entity

            # If get_entity failed but get_version succeeded, construct minimal entity
            # with just the version we fetched
            base_uri = get_entity_cache_key(uri)
            parsed = parse_entity_uri(uri)

            # Extract entity name from path, defaulting to last component
            # Handle edge cases where path might be empty or not contain slashes
            entity_name = parsed.path.strip("/")
            if "/" in entity_name:
                entity_name = entity_name.split("/")[-1]
            if not entity_name:
                entity_name = f"{parsed.entity_type}_unknown"

            minimal_entity = Entity(
                uri=base_uri,
                name=entity_name,
                project_name=parsed.project,
                type=parsed.entity_type,
                versions=[version_obj],
            )
            # Cache this minimal entity
            self._cache_entity(minimal_entity)
            return minimal_entity
        else:
            # Fetch full entity with all versions
            entity = await provider.get_entity(uri)
            if entity:
                # Cache the entity
                self._cache_entity(entity)
                return entity

        return None

    async def add_entity(self, entity: Entity, publish: bool = False) -> Entity:
        """Add a new entity.

        If publish=True, pushes to external Project Manager.
        Always caches to DatabaseManager.

        Args:
            entity: The entity to add
            publish: Whether to publish to external project managers

        Returns:
            The added entity
        """
        # Always cache locally
        self._cache_entity(entity)

        # Optionally publish to external providers
        if publish and self.project_manager and self.project_manager.provider:
            # Publish to the provider
            entity = await self.project_manager.provider.create_entity(entity)
            # Update cache with any provider-generated metadata
            self._cache_entity(entity)

        # Emit entity.added event
        await self.event_manager.emit("entity.added", entity)

        return entity

    async def update_entity(
        self, uri: str, updates: Dict[str, Any], publish: bool = False
    ) -> Optional[Entity]:
        """Update an existing entity.

        If publish=True, pushes updates to external Project Manager.
        Always updates cache in DatabaseManager.

        Args:
            uri: The entity URI to update
            updates: Dictionary of fields to update
            publish: Whether to publish updates to external project managers

        Returns:
            The updated entity if found, None otherwise
        """
        # Get the existing entity
        entity = await self.get_entity(uri)
        if not entity:
            return None

        # Apply updates
        for key, value in updates.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        # Update cache
        self._cache_entity(entity)

        # Optionally publish to external providers
        if publish and self.project_manager and self.project_manager.provider:
            entity = await self.project_manager.provider.update_entity(uri, entity)
            # Update cache with any provider changes
            self._cache_entity(entity)

        # Emit entity.updated event
        await self.event_manager.emit("entity.updated", uri, entity)

        return entity

    def _cache_entity(self, entity: Entity) -> None:
        """Cache an entity in the database.

        Args:
            entity: The entity to cache
        """
        # Get base URI (without version parameter) to use as cache key
        base_uri = get_entity_cache_key(entity.uri)

        # Store using base URI as key
        self.db.set(self.CACHE_COLLECTION, base_uri, entity.model_dump())

    def list_entities(self, entity_type: Optional[str] = None) -> List[Entity]:
        """List all cached entities.

        Args:
            entity_type: Optional filter by entity type (e.g., "asset", "shot", etc.)

        Returns:
            List of entities
        """
        all_data = self.db.get_all(self.CACHE_COLLECTION)
        entities = [Entity(**data) for data in all_data.values()]

        if entity_type:
            entities = [e for e in entities if e.type == entity_type]

        return entities

    async def resolve_dependencies(
        self, entity: Entity, version_id: str
    ) -> Dict[str, Entity]:
        """Resolve dependencies for a specific version of an entity.

        Args:
            entity: The entity containing the version
            version_id: The version ID to resolve dependencies for

        Returns:
            Dictionary mapping dependency URIs to resolved Entity objects
        """
        # Find the specified version
        version = None
        for v in entity.versions:
            if v.id == version_id:
                version = v
                break

        if not version:
            return {}

        # Resolve each dependency
        resolved = {}
        for dep_uri, dep_version in version.dependencies.items():
            # Create full URI with version
            full_uri = f"{dep_uri}?version={dep_version}"
            # Use async get_entity to resolve dependencies
            dep_entity = await self.get_entity(full_uri)
            if dep_entity:
                resolved[dep_uri] = dep_entity

        return resolved

    async def open(self, uri: str, version_id: Optional[str] = None) -> None:
        """Open an entity in the appropriate software with correct environment.

        This is a placeholder method that will be implemented in the future to:
        1. Sync the entity from source control
        2. Set up the appropriate environment variables
        3. Launch the appropriate software with the entity loaded

        Args:
            uri: The entity URI to open
            version_id: Optional specific version ID to open (defaults to latest)

        Raises:
            NotImplementedError: This method is not yet implemented

        Note:
            Future implementation will:
            - Check entity's VersionControlInfo to sync from source control
            - Use entity's SoftwareInfo to determine which software to launch
            - Apply entity's env_vars to the environment
            - Emit entity.opened event with uri and version_id
        """
        # Get the entity to validate it exists
        full_uri = f"{uri}?version={version_id}" if version_id else uri
        entity = await self.get_entity(full_uri)

        if not entity:
            raise ValueError(f"Entity not found: {uri}")

        # Emit entity.opened event
        await self.event_manager.emit("entity.opened", uri, version_id)

        # TODO: Future implementation will include:
        # 1. Sync from source control using version_control info
        # 2. Set up environment using env_vars
        # 3. Launch software using software info
        # 4. Load the entity in the software

        raise NotImplementedError(
            "Entity opening functionality is not yet implemented. "
            "Future versions will sync from source control and launch "
            "the appropriate software with the correct environment."
        )
