"""Mock Project Manager Provider for testing."""

from typing import Dict, List, Optional, Tuple

from artreactor.models.domain import Entity, Project, Version


class MockProjectManagerProvider:
    """Mock implementation of ProjectManagerProvider for testing."""

    def __init__(self):
        """Initialize the mock provider."""
        self.entities: Dict[str, Entity] = {}
        self.projects: Dict[str, Project] = {}
        self.get_entity_calls: List[str] = []
        self.get_version_calls: List[Tuple[str, str]] = []
        self.create_entity_calls: List[str] = []
        self.update_entity_calls: List[str] = []
        self.fetch_project_calls: List[str] = []
        self.fetch_projects_calls: List[bool] = []
        self.prefetch_entities_calls: List[str] = []

    async def get_entity(self, uri: str) -> Optional[Entity]:
        """Get an entity from the mock storage.

        Args:
            uri: The entity URI to fetch

        Returns:
            Entity if found, None otherwise
        """
        self.get_entity_calls.append(uri)
        # Strip version parameter if present
        base_uri = uri.split("?")[0]
        return self.entities.get(base_uri)

    async def get_version(self, uri: str, version: str) -> Optional[Version]:
        """Get a specific version from the mock storage.

        Args:
            uri: The entity URI
            version: The version identifier

        Returns:
            Version if found, None otherwise
        """
        self.get_version_calls.append((uri, version))
        base_uri = uri.split("?")[0]
        entity = self.entities.get(base_uri)
        if not entity:
            return None

        for v in entity.versions:
            if v.id == version:
                return v
        return None

    async def create_entity(self, entity: Entity) -> Entity:
        """Create a new entity in the mock storage.

        Args:
            entity: The entity to create

        Returns:
            The created entity
        """
        self.create_entity_calls.append(entity.uri)
        base_uri = entity.uri.split("?")[0]
        self.entities[base_uri] = entity
        return entity

    async def update_entity(self, uri: str, entity: Entity) -> Entity:
        """Update an existing entity in the mock storage.

        Args:
            uri: The entity URI to update
            entity: The updated entity data

        Returns:
            The updated entity
        """
        self.update_entity_calls.append(uri)
        base_uri = uri.split("?")[0]
        self.entities[base_uri] = entity
        return entity

    def fetch_project(self, name: str) -> Optional[Project]:
        """Simulate fetching from external service."""
        self.fetch_project_calls.append(name)
        return self.projects.get(name)

    def fetch_projects(self) -> List[Project]:
        """Simulate fetching all projects from external service."""
        self.fetch_projects_calls.append(True)
        return list(self.projects.values())

    def prefetch_entities_for_project(self, name: str) -> List[Entity]:
        """Fetch all entities for a project to populate the cache."""
        self.prefetch_entities_calls.append(name)
        # Return all entities belonging to this project from our mock storage
        project_entities = []
        for entity in self.entities.values():
            if entity.project_name == name:
                project_entities.append(entity)
        return project_entities

    def add_mock_entity(self, entity: Entity) -> None:
        """Add a mock entity directly to storage (for test setup).

        Args:
            entity: The entity to add
        """
        base_uri = entity.uri.split("?")[0]
        self.entities[base_uri] = entity

    def add_mock_project(self, name: str, path: str, description: str = ""):
        """Add a mock project to the external service."""
        self.projects[name] = Project(name=name, path=path, description=description)
