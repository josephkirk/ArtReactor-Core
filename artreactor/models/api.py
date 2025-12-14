"""API request and response models for ArtReactor Core.

This module contains Pydantic models used for API endpoints,
including request payloads and response schemas.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel

from .domain import SecretScope


class ChatRequest(BaseModel):
    """Request model for agent chat endpoint."""

    prompt: str
    context: Optional[Dict[str, str]] = None


class ChatResponse(BaseModel):
    """Response model for agent chat endpoint."""

    response: str
    steps: List[str] = []


class CreateProjectRequest(BaseModel):
    """Request model for creating a new project."""

    name: str
    path: str
    description: str = ""


class SecretSetRequest(BaseModel):
    """Request model for setting a secret."""

    key: str
    value: str
    scope: SecretScope
    project: Optional[str] = None
