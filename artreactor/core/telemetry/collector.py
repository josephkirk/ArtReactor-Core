"""
TelemetryCollector bridges logging and telemetry systems.
It subscribes to log events and automatically generates telemetry metrics.

Note: LogEntry.level is a string due to Pydantic's use_enum_values=True configuration.
"""

import threading
from artreactor.core.logging.types import LogEntry, LogLevel
from artreactor.core.telemetry.manager import TelemetryManager


class TelemetryCollector:
    """
    Collector that subscribes to log events and generates telemetry metrics.
    This provides automatic metric collection from the logging system.
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._telemetry_manager = TelemetryManager.get_instance()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    async def on_log_entry(self, entry: LogEntry):
        """
        Callback for log entry events. Generates telemetry metrics from log data.

        This method is designed to be registered as a subscriber to LogManager.
        """
        try:
            # Count log events by level
            level_key = f"log.count.{entry.level.lower()}"
            await self._telemetry_manager.record_counter(
                name=level_key,
                value=1.0,
                tags={"source": entry.source, "level": entry.level},
                context={"trace_id": entry.trace_id} if entry.trace_id else {},
            )

            # Count log events by source
            source_key = f"log.source.{entry.source}"
            await self._telemetry_manager.record_counter(
                name=source_key,
                value=1.0,
                tags={"source": entry.source, "level": entry.level},
            )

            # For error/critical logs, record additional details (using set for O(1) lookup)
            if entry.level in {LogLevel.ERROR.value, LogLevel.CRITICAL.value}:
                await self._telemetry_manager.record_counter(
                    name="log.errors.total",
                    value=1.0,
                    tags={"source": entry.source, "level": entry.level},
                    context={"message": entry.message[:100]},  # Truncate long messages
                )

            # Extract duration from context if available (for performance tracking)
            if "duration" in entry.context:
                await self._telemetry_manager.record_timer(
                    name=f"operation.duration.{entry.source}",
                    duration=entry.context["duration"],
                    tags={"source": entry.source},
                )

        except Exception as e:
            # Log telemetry errors to stderr to aid debugging without causing recursion
            import sys

            print(
                f"[TelemetryCollector] Error processing log entry: {e}", file=sys.stderr
            )
