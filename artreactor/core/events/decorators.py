import functools
import inspect
from typing import Callable, TypeVar, Awaitable, Union, cast
from .manager import event_manager

try:
    from typing import ParamSpec
except ImportError:
    from typing_extensions import ParamSpec

P = ParamSpec("P")
R = TypeVar("R")


def has_event(
    name: str,
) -> Callable[[Callable[P, Union[R, Awaitable[R]]]], Callable[P, Awaitable[R]]]:
    """
    Decorator to define a function as an event emitter.
    """

    def decorator(
        func: Callable[P, Union[R, Awaitable[R]]],
    ) -> Callable[P, Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Execute the original function first (if it has logic)
            if inspect.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Emit the event
            # We pass the result of the function as the payload to listeners.
            await event_manager.emit(name, result)

            return cast(R, result)

        return wrapper

    return decorator


# Alias for clarity
event = has_event


def on(name: str, fire_and_forget: bool = False):
    """
    Decorator to register a function as a listener for an event.
    """

    def decorator(func: Callable):
        event_manager.on(name, func, fire_and_forget=fire_and_forget)
        return func

    return decorator
