"""Telemetry models for ArtReactor Core.

This module contains models related to telemetry and metrics collection,
including metric types and telemetry event structures.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field


class MetricType(str, Enum):
    """Metric type enumeration."""

    COUNTER = "COUNTER"  # Incrementing count
    GAUGE = "GAUGE"  # Point-in-time value
    HISTOGRAM = "HISTOGRAM"  # Distribution of values
    TIMER = "TIMER"  # Duration measurement


class TelemetryEvent(BaseModel):
    """Structured telemetry event for metrics collection."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metric_name: str
    metric_type: MetricType
    value: float
    tags: Dict[str, str] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True)
