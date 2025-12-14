"""Domain models for ArtReactor Core.

This module contains the core domain models used throughout the application.
These models represent business entities and their relationships.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SecretScope(str, Enum):
    """Scope of a secret (USER or PROJECT level)."""

    USER = "USER"
    PROJECT = "PROJECT"


class Secret(BaseModel):
    """A secret value with its scope and metadata."""

    key: str
    value: str
    scope: SecretScope
    project: Optional[str] = None


class Project(BaseModel):
    """A project entity with metadata and workflows."""

    name: str
    path: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    workflows: List[Dict[str, Any]] = []


class EntityType:
    """Common entity types in the pipeline.

    These are predefined constants for convenience, but any string value
    can be used as an entity type without modifying this code.
    """

    ASSET = "asset"
    SHOT = "shot"
    SEQUENCE = "sequence"
    LEVEL = "level"


class VersionControlInfo(BaseModel):
    """Version control information for an entity version."""

    method: str  # git, svn, perforce, etc.
    repository: Optional[str] = None
    commit: Optional[str] = None
    branch: Optional[str] = None
    tag: Optional[str] = None


class SoftwareInfo(BaseModel):
    """Software requirements for an entity version."""

    name: str
    version: str


class ProjectManagerLink(BaseModel):
    """Link to a project management provider for an entity version.

    Tracks the relationship between a local entity version and its
    representation in an external project management system.
    """

    provider: str  # Provider name/type (e.g., "kitsu", "ftrack", "shotgrid")
    provider_id: str  # Version ID in the external provider
    metadata: Dict[str, Any] = Field(
        default_factory=dict
    )  # Additional provider-specific data


class Version(BaseModel):
    """A version of an entity with its metadata and dependencies."""

    id: str
    version_control: Optional[VersionControlInfo] = None
    software: Optional[SoftwareInfo] = None
    env_vars: Dict[str, str] = Field(default_factory=dict)
    dependencies: Dict[str, str] = Field(
        default_factory=dict
    )  # Entity URI -> Version ID
    project_manager_links: List["ProjectManagerLink"] = Field(
        default_factory=list
    )  # Links to external project management systems


class Entity(BaseModel):
    """An entity in the pipeline (asset, shot, sequence, etc.)."""

    uri: str
    name: str
    project_name: str
    type: str  # Entity type (e.g., "asset", "shot", "sequence", "level", or any custom type)
    description: Optional[str] = None
    versions: List[Version] = Field(default_factory=list)
