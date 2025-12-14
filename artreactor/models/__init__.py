"""Models package for ArtReactor Core.

This package contains all data models used throughout the application,
organized by domain and purpose.
"""

# Domain models
from .domain import Project, Secret, SecretScope

# API models
from .api import (
    ChatRequest,
    ChatResponse,
    CreateProjectRequest,
    SecretSetRequest,
)

# Logging models
from .logging import LogEntry, LogLevel

# Telemetry models
from .telemetry import TelemetryEvent, MetricType

# Plugin models
from .plugin import PluginManifest, PluginTiming, PluginType

__all__ = [
    # Domain models
    "Project",
    "Secret",
    "SecretScope",
    # API models
    "ChatRequest",
    "ChatResponse",
    "CreateProjectRequest",
    "SecretSetRequest",
    # Logging models
    "LogEntry",
    "LogLevel",
    # Telemetry models
    "TelemetryEvent",
    "MetricType",
    # Plugin models
    "PluginManifest",
    "PluginTiming",
    "PluginType",
]
