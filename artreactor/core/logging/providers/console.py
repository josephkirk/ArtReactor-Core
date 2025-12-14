import logging
import sys
from artreactor.core.logging.interface import LogProvider
from artreactor.core.logging.types import LogEntry, LogLevel


class ConsoleLogProvider(LogProvider):
    def __init__(self, name: str = "console"):
        self.name = name
        self._logger = logging.getLogger(f"artreactor.{name}")
        self._logger.setLevel(logging.DEBUG)

        # Avoid adding multiple handlers if re-initialized
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    async def initialize(self) -> None:
        # Standard logging is already synchronous and lazy-inited
        pass

    async def shutdown(self) -> None:
        pass

    async def log(self, entry: LogEntry) -> None:
        # Map our LogLevel to python logging levels
        level_map = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL,
        }

        py_level = level_map.get(entry.level, logging.INFO)

        # Format message with trace context if available
        msg = f"[{entry.source}] {entry.message}"
        if entry.trace_id:
            msg = f"[TraceID:{entry.trace_id}] {msg}"

        self._logger.log(py_level, msg)
