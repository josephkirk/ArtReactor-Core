import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from artreactor.core.interfaces.project_manager_provider import ProjectManagerProvider
from artreactor.core.utils.uri_parser import get_entity_cache_key
from artreactor.models.domain import Project

logger = logging.getLogger(__name__)

# Re-export models for backward compatibility
__all__ = [
    "Project",
    "ProjectManager",
]


class ProjectManager:
    """Project Manager with database caching.

    This manager uses a database for caching project data fetched from
    external services (Kitsu, Shotgrid, Ftrack). Each query to the external
    service is automatically cached in the database for faster subsequent access.

    If no external provider is configured, it operates in local-only mode
    using the database as the source of truth.
    """

    CACHE_COLLECTION = "projects_cache"

    def __init__(
        self, database_manager, provider: Optional[ProjectManagerProvider] = None
    ):
        """Initialize the project manager.

        Args:
            database_manager: DatabaseManager instance for caching
            provider: Optional external service provider (Kitsu, Shotgrid, etc.)
        """
        self.db = database_manager
        self.provider = provider

    def _cache_entities(self, entities: List[Any]):
        """Cache pre-fetched entities directly to the database.

        This uses the shared entity cache collection and key generation logic
        to avoid duplication. Since EntityManager is not available here (to avoid
        circular dependency), we import the constant directly.

        Note: This is an optimization to pre-populate the cache when fetching projects.
        """
        if not entities:
            return

        # Import here to avoid circular dependency at module level
        from artreactor.core.managers.entity_manager import EntityManager

        for entity in entities:
            # Use shared cache key generation utility
            base_uri = get_entity_cache_key(entity.uri)

            # Store in the entity cache collection used by EntityManager
            self.db.set(EntityManager.CACHE_COLLECTION, base_uri, entity.model_dump())

    def get_project(self, name: str) -> Optional[Project]:
        """Get a project by name, using cache or fetching from external service.

        Args:
            name: Project name

        Returns:
            Project if found, None otherwise
        """
        # Try cache first
        cached = self.db.get(self.CACHE_COLLECTION, name)
        if cached:
            return Project(**cached)

        # If provider exists, fetch from external service and cache
        if self.provider:
            project = self.provider.fetch_project(name)
            if project:
                self._cache_project(project)

                # Prefetch entities for this project
                try:
                    entities = self.provider.prefetch_entities_for_project(name)
                    self._cache_entities(entities)
                except (AttributeError, Exception) as e:
                    # Don't let entity prefetch failure block project loading
                    logger.warning(
                        f"Failed to prefetch entities for project '{name}': {e}"
                    )

                return project

        return None

    def list_projects(self) -> List[Project]:
        """List all projects, fetching from external service if provider exists.

        Returns:
            List of all projects (cached and/or from external service)
        """
        # If provider exists, fetch from external service and update cache
        if self.provider:
            projects = self.provider.fetch_projects()
            for project in projects:
                self._cache_project(project)
            return projects

        # Otherwise return all cached projects (optimized bulk retrieval)
        cached_data = self.db.get_all(self.CACHE_COLLECTION)
        projects = []
        for project_data in cached_data.values():
            projects.append(Project(**project_data))
        return projects

    def create_project(self, name: str, path: str, description: str = "") -> Project:
        """Create a new project in the cache.

        Note: If an external provider is configured, this only creates in cache.
        You may need to create the project in the external service separately.

        Args:
            name: Project name
            path: Project path
            description: Project description

        Returns:
            Created project

        Raises:
            ValueError: If project already exists
        """
        # Check if exists
        existing = self.db.get(self.CACHE_COLLECTION, name)
        if existing:
            raise ValueError(f"Project {name} already exists")

        project = Project(name=name, path=path, description=description)
        self._cache_project(project)
        return project

    def delete_project(self, name: str):
        """Delete a project from the cache.

        Note: This only removes from cache, not from the external service.

        Args:
            name: Project name
        """
        self.db.remove(self.CACHE_COLLECTION, name)

    def clear_cache(self):
        """Clear all cached project data.

        Useful when you want to force a refresh from the external service.
        """
        self.db.clear_collection(self.CACHE_COLLECTION)

    def _cache_project(self, project: Project):
        """Store project in cache.

        Args:
            project: Project to cache
        """
        # Use mode='json' to ensure datetime objects are serialized properly
        self.db.set(
            self.CACHE_COLLECTION, project.name, project.model_dump(mode="json")
        )

    def get_workflows(self, project_name: str) -> List[Dict[str, Any]]:
        project = self.get_project(project_name)
        if not project:
            return []

        path = Path(project.path)
        if not path.exists():
            return []

        workflows = []
        # Basic workflow scanning (simplified for POC)
        # Assumes workflows are python files in the project root or a 'workflows' subdir
        # For now, scan root
        for file in path.glob("*.py"):
            if file.name.startswith("_"):
                continue
            workflows.append({"name": file.stem, "path": str(file)})

        return workflows
