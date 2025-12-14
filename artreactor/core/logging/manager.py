import asyncio
import threading
from typing import List, Callable, Awaitable, Dict, Any, Optional
from artreactor.core.logging.types import LogEntry, LogLevel
from artreactor.core.logging.interface import LogProvider
from contextvars import ContextVar

# Context variables for tracing
_trace_id_ctx = ContextVar("trace_id", default=None)
_span_id_ctx = ContextVar("span_id", default=None)


class LogManager:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._providers: List[LogProvider] = []
        self._subscribers: List[Callable[[LogEntry], Awaitable[None]]] = []

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    async def initialize(self):
        for provider in self._providers:
            await provider.initialize()

    async def shutdown(self):
        for provider in self._providers:
            await provider.shutdown()

    def register_provider(self, provider: LogProvider):
        self._providers.append(provider)

    def subscribe(self, callback: Callable[[LogEntry], Awaitable[None]]):
        self._subscribers.append(callback)

    def clear_providers(self):
        """Clear all registered providers (for testing purposes)."""
        self._providers.clear()

    def clear_subscribers(self):
        """Clear all subscribers (for testing purposes)."""
        self._subscribers.clear()

    def set_context(self, trace_id: str, span_id: Optional[str] = None):
        _trace_id_ctx.set(trace_id)
        if span_id:
            _span_id_ctx.set(span_id)

    def get_context(self) -> Dict[str, Optional[str]]:
        return {"trace_id": _trace_id_ctx.get(), "span_id": _span_id_ctx.get()}

    async def log(
        self, level: LogLevel, message: str, source: str, context: Dict[str, Any] = None
    ):
        entry = LogEntry(
            level=level,
            message=message,
            source=source,
            trace_id=_trace_id_ctx.get(),
            span_id=_span_id_ctx.get(),
            context=context or {},
        )

        # Dispatch to providers
        await asyncio.gather(
            *[provider.log(entry) for provider in self._providers],
            return_exceptions=True,
        )

        # Dispatch to subscribers (fire and forget pattern for now to avoid blocking)
        # We use create_task to ensure subscribers don't block the main flow if they are slow
        # But for strictly bounded logging we might want to await.
        # Given the requirement "mandatory track", awaiting providers is safer.
        # Subscribers can be async.

        for subscriber in self._subscribers:
            try:
                await subscriber(entry)
            except Exception:
                # Prevent subscriber errors from crashing the app
                pass

    # Convenience methods
    async def debug(self, message: str, source: str, **kwargs):
        await self.log(LogLevel.DEBUG, message, source, kwargs)

    async def info(self, message: str, source: str, **kwargs):
        await self.log(LogLevel.INFO, message, source, kwargs)

    async def warning(self, message: str, source: str, **kwargs):
        await self.log(LogLevel.WARNING, message, source, kwargs)

    async def error(self, message: str, source: str, **kwargs):
        await self.log(LogLevel.ERROR, message, source, kwargs)

    async def critical(self, message: str, source: str, **kwargs):
        await self.log(LogLevel.CRITICAL, message, source, kwargs)
