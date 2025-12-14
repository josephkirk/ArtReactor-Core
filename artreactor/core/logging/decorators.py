import functools
import inspect
import time
from typing import Callable, Any, Optional
from artreactor.core.logging.manager import LogManager, LogLevel


def track_call(level: LogLevel = LogLevel.DEBUG, source: Optional[str] = None):
    """
    Decorator to track function entry and exit logs.

    Args:
        level: Log level to use for the entry/exit logs.
        source: Custom source identifier. Defaults to module.function.
    """

    def decorator(func: Callable) -> Callable:
        # Determine source name once
        nonlocal source
        if not source:
            source = f"{func.__module__}.{func.__qualname__}"

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            logger = LogManager.get_instance()
            start_time = time.perf_counter()

            # Log Entry
            await logger.log(
                level=level,
                message=f"Entering {func.__name__}",
                source=source,
                context={"args": str(args), "kwargs": str(kwargs)},
            )

            try:
                result = await func(*args, **kwargs)
                duration = time.perf_counter() - start_time

                # Log Success
                await logger.log(
                    level=level,
                    message=f"Exiting {func.__name__} (Duration: {duration:.4f}s)",
                    source=source,
                    context={"result": str(result), "duration": duration},
                )
                return result
            except Exception as e:
                duration = time.perf_counter() - start_time
                # Log Exception
                await logger.log(
                    level=LogLevel.ERROR,
                    message=f"Exception in {func.__name__}: {str(e)}",
                    source=source,
                    context={"error": str(e), "duration": duration},
                )
                raise e

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # For sync functions, we can't await logger.log
            # We schedule it on the loop if possible, or force it?
            # LogManager.log is async. Mixing sync/async logging is tricky.
            # But since ArtReactor is async-first (FastAPI), typically we run in loop.
            # If called from sync context without loop, this will fail.
            # "The system... relies on heavy use of async/await".
            # For sync wrapper, we might need a sync version of log or run_until_complete?
            # Or just assume it runs in a thread where we can access loop?

            # Simplified approach: Only support async logging for now or skip sync logging
            # to avoid blocking. Or use fire-and-forget on existing loop.

            # Checking if there's a running loop
            # This is a common pitfall.
            # Given requirement "Dev can optin... via decorator", it implies usage in general code.
            # But the system is "async heavy".
            # Let's assume most tracked calls are async.
            # If sync, we try to get loop and create task.

            try:
                import asyncio

                loop = asyncio.get_running_loop()
                # Fire and forget
                # We can't await here.
                # Construction of LogEntry is sync, but log() is async.

                logger = LogManager.get_instance()
                start_time = time.perf_counter()

                loop.create_task(
                    logger.log(
                        level=level,
                        message=f"Entering {func.__name__}",
                        source=source,
                        context={"args": str(args), "kwargs": str(kwargs)},
                    )
                )

                try:
                    result = func(*args, **kwargs)
                    duration = time.perf_counter() - start_time
                    loop.create_task(
                        logger.log(
                            level=level,
                            message=f"Exiting {func.__name__} (Duration: {duration:.4f}s)",
                            source=source,
                            context={"result": str(result), "duration": duration},
                        )
                    )
                    return result
                except Exception as e:
                    duration = time.perf_counter() - start_time
                    loop.create_task(
                        logger.log(
                            level=LogLevel.ERROR,
                            message=f"Exception in {func.__name__}: {str(e)}",
                            source=source,
                            context={"error": str(e), "duration": duration},
                        )
                    )
                    raise e
            except RuntimeError:
                # No running loop (e.g. script start). Fallback to print or ignore?
                # Safe to ignore for now or print to stderr.
                return func(*args, **kwargs)

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
