from abc import abstractmethod
from artreactor.core.interfaces.plugin import Plugin
from artreactor.core.logging.interface import LogProvider


class LoggingPlugin(Plugin):
    """
    Plugin for registering a new logging provider.
    """

    @abstractmethod
    def get_provider(self) -> LogProvider:
        """Returns the instantiated log provider."""
        pass
