from abc import ABC, abstractmethod
from artreactor.core.telemetry.types import TelemetryEvent


class TelemetryProvider(ABC):
    """
    Abstract base class for telemetry providers.
    Plugins can implement this interface to provide custom telemetry backends
    (e.g., Sentry, Grafana, Prometheus, custom analytics).
    """

    @abstractmethod
    async def record(self, event: TelemetryEvent) -> None:
        """
        Record a telemetry event.
        """
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the telemetry provider (e.g., connect to remote service).
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Shutdown the telemetry provider (e.g., flush buffers, close connections).
        """
        pass

    @abstractmethod
    async def flush(self) -> None:
        """
        Force flush any buffered telemetry data.
        """
        pass
