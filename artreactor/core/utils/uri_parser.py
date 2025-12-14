"""URI Parser for Entity URIs.

This module provides utilities to parse and construct entity:// URIs.
"""

from typing import Optional
from urllib.parse import parse_qs, urlparse


class EntityURI:
    """Represents a parsed entity:// URI."""

    def __init__(
        self,
        project: str,
        entity_type: str,
        path: str,
        version: Optional[str] = None,
    ):
        """Initialize an EntityURI.

        Args:
            project: The project name
            entity_type: The entity type (asset, shot, sequence, etc.)
            path: The hierarchical path to the entity
            version: Optional version identifier
        """
        self.project = project
        self.entity_type = entity_type
        self.path = path
        self.version = version

    def __str__(self) -> str:
        """Convert the EntityURI back to a string."""
        uri = f"entity://{self.project}/{self.entity_type}/{self.path}"
        if self.version:
            uri += f"?version={self.version}"
        return uri

    def __repr__(self) -> str:
        """Represent the EntityURI for debugging."""
        return (
            f"EntityURI(project={self.project!r}, entity_type={self.entity_type!r}, "
            f"path={self.path!r}, version={self.version!r})"
        )


def parse_entity_uri(uri: str) -> EntityURI:
    """Parse an entity:// URI into its components.

    Args:
        uri: The URI to parse (e.g., "entity://projectA/asset/characters/hero?version=v001")

    Returns:
        EntityURI object with parsed components

    Raises:
        ValueError: If the URI format is invalid
    """
    parsed = urlparse(uri)

    if parsed.scheme != "entity":
        raise ValueError(f"Invalid URI scheme: {parsed.scheme}. Expected 'entity'")

    # Check if netloc (project) is provided
    if not parsed.netloc:
        raise ValueError(f"Invalid URI: missing project in {uri}")

    project = parsed.netloc

    # Parse path after the netloc
    full_path = parsed.path.lstrip("/")
    if not full_path:
        raise ValueError(f"Invalid URI: missing entity type and path in {uri}")

    path_components = full_path.split("/", 1)
    if len(path_components) < 2:
        raise ValueError(f"Invalid URI: missing entity path in {uri}")

    entity_type = path_components[0]
    entity_path = path_components[1]

    # Parse query parameters for version
    version = None
    if parsed.query:
        query_params = parse_qs(parsed.query)
        if "version" in query_params:
            version = query_params["version"][0]

    return EntityURI(
        project=project,
        entity_type=entity_type,
        path=entity_path,
        version=version,
    )


def build_entity_uri(
    project: str,
    entity_type: str,
    path: str,
    version: Optional[str] = None,
) -> str:
    """Build an entity:// URI from components.

    Args:
        project: The project name
        entity_type: The entity type (asset, shot, sequence, etc.)
        path: The hierarchical path to the entity
        version: Optional version identifier

    Returns:
        The constructed URI string
    """
    uri = f"entity://{project}/{entity_type}/{path}"
    if version:
        uri += f"?version={version}"
    return uri


def get_entity_cache_key(uri: str) -> str:
    """Get the cache key for an entity URI.

    This function extracts the base URI (without version parameter) to use as a cache key.
    All versions of an entity are stored under the same cache key.

    Args:
        uri: The entity URI (may include version parameter)

    Returns:
        The base URI to use as cache key (without version parameter)

    Example:
        >>> get_entity_cache_key("entity://projectA/asset/characters/hero?version=v001")
        'entity://projectA/asset/characters/hero'
    """
    parsed = parse_entity_uri(uri)
    return f"entity://{parsed.project}/{parsed.entity_type}/{parsed.path}"
