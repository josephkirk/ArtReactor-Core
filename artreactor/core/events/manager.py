import asyncio
import inspect
from typing import Dict, List, Callable


class EventManager:
    """
    Central manager for event registration and emission.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventManager, cls).__new__(cls)
            cls._instance.listeners = {}
        return cls._instance

    class Listener:
        __slots__ = ("func", "fire_and_forget", "is_async")

        def __init__(self, func: Callable, fire_and_forget: bool = False):
            self.func = func
            self.fire_and_forget = fire_and_forget
            # Cache coroutine check at registration to avoid per-emit overhead
            self.is_async = inspect.iscoroutinefunction(func)

    def __init__(self):
        # Listeners: event_name -> list of Listener objects
        if not hasattr(self, "listeners"):
            self.listeners: Dict[str, List["EventManager.Listener"]] = {}
        # Lazy init to avoid circular import with LogManager
        self._log_manager = None

    def _get_logger(self):
        """Return the LogManager instance, importing it lazily."""
        if self._log_manager is None:
            from artreactor.core.logging.manager import LogManager

            self._log_manager = LogManager.get_instance()
        return self._log_manager

    def on(self, event_name: str, handler: Callable, fire_and_forget: bool = False):
        """
        Register a listener for an event.
        """
        if event_name not in self.listeners:
            self.listeners[event_name] = []

        # Check if already registered (by function identity)
        for listener in self.listeners[event_name]:
            if listener.func == handler:
                # Update options? Or allow duplicates?
                # Let's simple allow duplicates or just return.
                # For now, let's append as new to support different options if needed, though rare.
                pass

        self.listeners[event_name].append(self.Listener(handler, fire_and_forget))
        # Log asynchronously in background (fire and forget)
        log_manager = self._get_logger()
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                log_manager.debug(
                    f"Registered listener {handler.__name__} for event {event_name} (f&f={fire_and_forget})",
                    source="events.manager",
                )
            )
        except RuntimeError:
            # No running loop, skip logging
            pass

    def off(self, event_name: str, handler: Callable):
        """
        Unregister a listener for an event.
        """
        if event_name in self.listeners:
            initial_count = len(self.listeners[event_name])
            self.listeners[event_name] = [
                listener
                for listener in self.listeners[event_name]
                if listener.func != handler
            ]

            # Log asynchronously in background (fire and forget)
            log_manager = self._get_logger()
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No running loop, cannot log asynchronously
                return
            if len(self.listeners[event_name]) < initial_count:
                loop.create_task(
                    log_manager.debug(
                        f"Unregistered listener {handler.__name__} for event {event_name}",
                        source="events.manager",
                    )
                )
            else:
                loop.create_task(
                    log_manager.warning(
                        f"Listener {handler.__name__} not found for event {event_name}",
                        source="events.manager",
                    )
                )

    async def emit(self, event_name: str, *args, **kwargs):
        """
        Emit an event, calling all registered listeners.
        Optimized for high-throughput scenarios.
        """
        # Fast path: use .get() to avoid double lookup
        listeners = self.listeners.get(event_name)
        if not listeners:
            return

        # Optional emit logging (disabled by default for performance)
        # Enable via EventManager().emit_logging = True for debugging
        if getattr(self, "emit_logging", False):
            log_manager = self._get_logger()
            asyncio.create_task(
                log_manager.debug(
                    f"Emitting event {event_name} to {len(listeners)} listeners",
                    source="events.manager",
                    event_name=event_name,
                    listener_count=len(listeners),
                )
            )

        awaitable_tasks = []
        handler_names = []
        log_manager = None  # Lazy init for error logging only

        for listener in listeners:
            handler = listener.func
            try:
                if listener.is_async:
                    coro = handler(*args, **kwargs)
                    if listener.fire_and_forget:
                        asyncio.create_task(coro)
                    else:
                        awaitable_tasks.append(coro)
                        handler_names.append(handler.__name__)
                else:
                    # Run synchronous handlers in a separate thread
                    coro = asyncio.to_thread(handler, *args, **kwargs)
                    if listener.fire_and_forget:
                        asyncio.create_task(coro)
                    else:
                        awaitable_tasks.append(coro)
                        handler_names.append(handler.__name__)

            except Exception as e:
                # Catch errors during task creation/dispatch
                if log_manager is None:
                    log_manager = self._get_logger()
                await log_manager.error(
                    f"Error preparing listener {handler.__name__} for event {event_name}: {e}",
                    source="events.manager",
                    event_name=event_name,
                    handler=handler.__name__,
                    error=str(e),
                )

        if awaitable_tasks:
            results = await asyncio.gather(*awaitable_tasks, return_exceptions=True)

            # Log exceptions raised during execution for awaited tasks
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    if log_manager is None:
                        log_manager = self._get_logger()
                    name = handler_names[i] if i < len(handler_names) else "unknown"
                    await log_manager.error(
                        f"Error in listener {name} for event {event_name}: {result}",
                        source="events.manager",
                        event_name=event_name,
                        handler=name,
                        error=str(result),
                    )


# Global instances
event_manager = EventManager()
