from abc import abstractmethod
from artreactor.core.interfaces.plugin import Plugin
from artreactor.core.telemetry.interface import TelemetryProvider


class TelemetryPlugin(Plugin):
    """
    Plugin for registering a new telemetry provider.
    Allows plugins to contribute custom telemetry backends (Sentry, Grafana, etc.)
    """

    @abstractmethod
    def get_provider(self) -> TelemetryProvider:
        """Returns the instantiated telemetry provider."""
        pass
