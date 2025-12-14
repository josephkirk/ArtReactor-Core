"""Logging models for ArtReactor Core.

This module contains models related to structured logging,
including log levels and log entry structures.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class LogLevel(str, Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEntry(BaseModel):
    """Structured log entry event."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    level: LogLevel
    message: str
    source: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True)
