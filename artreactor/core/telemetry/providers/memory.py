"""In-memory telemetry provider for testing and development."""

from collections import defaultdict
from typing import Dict, List
from artreactor.core.telemetry.interface import TelemetryProvider
from artreactor.core.telemetry.types import TelemetryEvent, MetricType


class InMemoryTelemetryProvider(TelemetryProvider):
    """
    In-memory telemetry provider that stores metrics in memory.
    Useful for testing, development, and debugging.
    """

    def __init__(self, name: str = "memory"):
        self.name = name
        self.events: List[TelemetryEvent] = []
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, List[float]] = defaultdict(list)

    async def initialize(self) -> None:
        """Initialize the provider (no-op for in-memory)."""
        pass

    async def shutdown(self) -> None:
        """Shutdown the provider (no-op for in-memory)."""
        pass

    async def flush(self) -> None:
        """Flush buffered data (no-op for in-memory)."""
        pass

    async def record(self, event: TelemetryEvent) -> None:
        """Record a telemetry event in memory."""
        self.events.append(event)

        # Update aggregated metrics based on type
        if event.metric_type == MetricType.COUNTER:
            self.counters[event.metric_name] += event.value
        elif event.metric_type == MetricType.GAUGE:
            self.gauges[event.metric_name] = event.value
        elif event.metric_type == MetricType.HISTOGRAM:
            self.histograms[event.metric_name].append(event.value)
        elif event.metric_type == MetricType.TIMER:
            self.timers[event.metric_name].append(event.value)

    def get_counter(self, name: str) -> float:
        """Get current value of a counter."""
        return self.counters.get(name, 0.0)

    def get_gauge(self, name: str) -> float:
        """Get current value of a gauge."""
        return self.gauges.get(name, 0.0)

    def get_histogram(self, name: str) -> List[float]:
        """Get all values for a histogram."""
        return self.histograms.get(name, [])

    def get_timers(self, name: str) -> List[float]:
        """Get all values for a timer."""
        return self.timers.get(name, [])

    def clear(self):
        """Clear all stored metrics (useful for testing)."""
        self.events.clear()
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.timers.clear()
