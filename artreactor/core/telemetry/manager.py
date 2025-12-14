import asyncio
import threading
from typing import Any, Dict, List, Optional
from artreactor.core.telemetry.types import TelemetryEvent, MetricType
from artreactor.core.telemetry.interface import TelemetryProvider


class TelemetryManager:
    """
    Central manager for telemetry collection and provider registration.
    Handles dispatching telemetry events to registered providers.
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._providers: List[TelemetryProvider] = []

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    async def initialize(self):
        """Initialize all registered telemetry providers."""
        for provider in self._providers:
            await provider.initialize()

    async def shutdown(self):
        """Shutdown all registered telemetry providers."""
        for provider in self._providers:
            await provider.shutdown()

    def register_provider(self, provider: TelemetryProvider):
        """Register a new telemetry provider."""
        self._providers.append(provider)

    def clear_providers(self):
        """Clear all registered providers (for testing purposes)."""
        self._providers.clear()

    async def record(self, event: TelemetryEvent):
        """
        Record a telemetry event by dispatching to all registered providers.
        """
        # Dispatch to all providers in parallel (non-blocking)
        await asyncio.gather(
            *[provider.record(event) for provider in self._providers],
            return_exceptions=True,
        )

    async def record_counter(
        self,
        name: str,
        value: float = 1.0,
        tags: Optional[Dict[str, str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Convenience method to record a counter metric."""
        event = TelemetryEvent(
            metric_name=name,
            metric_type=MetricType.COUNTER,
            value=value,
            tags=tags or {},
            context=context or {},
        )
        await self.record(event)

    async def record_gauge(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Convenience method to record a gauge metric."""
        event = TelemetryEvent(
            metric_name=name,
            metric_type=MetricType.GAUGE,
            value=value,
            tags=tags or {},
            context=context or {},
        )
        await self.record(event)

    async def record_histogram(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Convenience method to record a histogram metric."""
        event = TelemetryEvent(
            metric_name=name,
            metric_type=MetricType.HISTOGRAM,
            value=value,
            tags=tags or {},
            context=context or {},
        )
        await self.record(event)

    async def record_timer(
        self,
        name: str,
        duration: float,
        tags: Optional[Dict[str, str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Convenience method to record a timer metric."""
        event = TelemetryEvent(
            metric_name=name,
            metric_type=MetricType.TIMER,
            value=duration,
            tags=tags or {},
            context=context or {},
        )
        await self.record(event)

    async def flush(self):
        """Force flush all providers."""
        await asyncio.gather(
            *[provider.flush() for provider in self._providers],
            return_exceptions=True,
        )
