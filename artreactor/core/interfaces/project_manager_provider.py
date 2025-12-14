"""Project Manager Provider Interface.

This module defines the protocol for external project management integrations
(Kitsu, Ftrack, ShotGrid).
"""

from typing import List, Optional, Protocol

from artreactor.models.domain import Entity, Project, Version


class ProjectManagerProvider(Protocol):
    """Protocol for external project management service providers.

    Implementations should connect to services like Kitsu, Shotgrid, or Ftrack
    to fetch and update entity and project data.
    """

    # --- Entity Operations ---
    async def get_entity(self, uri: str) -> Optional[Entity]:
        """Get an entity from the external service.

        Args:
            uri: The entity URI to fetch

        Returns:
            Entity if found, None otherwise
        """
        ...

    async def get_version(self, uri: str, version: str) -> Optional[Version]:
        """Get a specific version of an entity from the external service.

        Args:
            uri: The entity URI
            version: The version identifier

        Returns:
            Version if found, None otherwise
        """
        ...

    async def create_entity(self, entity: Entity) -> Entity:
        """Create a new entity in the external service.

        Args:
            entity: The entity to create

        Returns:
            The created entity with any service-generated metadata
        """
        ...

    async def update_entity(self, uri: str, entity: Entity) -> Entity:
        """Update an existing entity in the external service.

        Args:
            uri: The entity URI to update
            entity: The updated entity data

        Returns:
            The updated entity
        """
        ...

    # --- Project Operations ---
    def fetch_project(self, name: str) -> Optional[Project]:
        """Fetch a project from the external service.

        Args:
            name: Project name

        Returns:
            Project data from the external service, or None if not found
        """
        ...

    def fetch_projects(self) -> List[Project]:
        """Fetch all projects from the external service.

        Returns:
            List of all projects from the external service
        """
        ...

    def prefetch_entities_for_project(self, name: str) -> List[Entity]:
        """Fetch all entities for a project to populate the cache.

        Args:
            name: Project name

        Returns:
            List of entities to cache
        """
        ...
