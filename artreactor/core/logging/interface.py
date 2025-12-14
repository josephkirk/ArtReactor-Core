from abc import ABC, abstractmethod
from artreactor.core.logging.types import LogEntry


class LogProvider(ABC):
    """
    Abstract base class for logging providers.
    Plugins can implement this interface to provide custom logging backends.
    """

    @abstractmethod
    async def log(self, entry: LogEntry) -> None:
        """
        Emit a log entry.
        """
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the log provider (e.g., open files, connect to remote).
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Shutdown the log provider (e.g., flush buffers, close connections).
        """
        pass
