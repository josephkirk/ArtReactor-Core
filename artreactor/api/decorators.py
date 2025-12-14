"""
API decorators for automatic logging and telemetry.
"""

import functools
import inspect
import time
from typing import Callable, Any, Optional
from artreactor.core.logging.manager import LogManager, LogLevel
from artreactor.core.telemetry.manager import TelemetryManager


def _sanitize_value(value: Any, max_length: int = 100) -> str:
    """Sanitize a value for logging, truncating if necessary."""
    str_value = str(value)
    if len(str_value) > max_length:
        return str_value[:max_length] + "..."
    return str_value


def track_execution_time(
    metric_name: Optional[str] = None,
    tags: Optional[dict] = None,
    log_result: bool = False,
):
    """
    Decorator to track execution time and record it as telemetry.

    This decorator works with both sync and async functions and automatically
    records the execution time as a timer metric. Optionally logs the result.

    Args:
        metric_name: Name for the telemetry metric. Defaults to "function.{func_name}.duration"
        tags: Additional tags to attach to the telemetry event
        log_result: Whether to log the function result (default: False)

    Example:
        @track_execution_time(metric_name="process_data.duration", tags={"env": "prod"})
        async def process_data(data):
            # Process data
            return result

        @track_execution_time()
        def sync_function():
            # Synchronous function
            return result
    """

    def decorator(func: Callable) -> Callable:
        # Determine metric name once
        nonlocal metric_name
        if not metric_name:
            metric_name = f"function.{func.__name__}.duration"

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                telemetry_manager = TelemetryManager.get_instance()
                start_time = time.perf_counter()

                try:
                    result = await func(*args, **kwargs)
                    duration = time.perf_counter() - start_time

                    # Record telemetry
                    metric_tags = {"function": func.__name__, "status": "success"}
                    if tags:
                        metric_tags.update(tags)

                    await telemetry_manager.record_timer(
                        name=metric_name,
                        duration=duration,
                        tags=metric_tags,
                    )

                    if log_result:
                        log_manager = LogManager.get_instance()
                        await log_manager.debug(
                            f"Function {func.__name__} completed in {duration:.4f}s",
                            source=f"decorator.{func.__name__}",
                            duration=duration,
                        )

                    return result

                except Exception:
                    duration = time.perf_counter() - start_time

                    # Record telemetry for failures
                    metric_tags = {"function": func.__name__, "status": "error"}
                    if tags:
                        metric_tags.update(tags)

                    await telemetry_manager.record_timer(
                        name=metric_name,
                        duration=duration,
                        tags=metric_tags,
                    )

                    raise

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                start_time = time.perf_counter()

                try:
                    result = func(*args, **kwargs)
                    duration = time.perf_counter() - start_time

                    # For sync functions, try to record telemetry if there's a running loop
                    try:
                        import asyncio

                        loop = asyncio.get_running_loop()
                        telemetry_manager = TelemetryManager.get_instance()

                        metric_tags = {"function": func.__name__, "status": "success"}
                        if tags:
                            metric_tags.update(tags)

                        # Fire and forget - don't block sync function
                        loop.create_task(
                            telemetry_manager.record_timer(
                                name=metric_name,
                                duration=duration,
                                tags=metric_tags,
                            )
                        )

                        if log_result:
                            log_manager = LogManager.get_instance()
                            loop.create_task(
                                log_manager.debug(
                                    f"Function {func.__name__} completed in {duration:.4f}s",
                                    source=f"decorator.{func.__name__}",
                                    duration=duration,
                                )
                            )
                    except RuntimeError:
                        # No running loop, skip telemetry recording
                        pass

                    return result

                except Exception:
                    duration = time.perf_counter() - start_time

                    # Try to record failure telemetry
                    try:
                        import asyncio

                        loop = asyncio.get_running_loop()
                        telemetry_manager = TelemetryManager.get_instance()

                        metric_tags = {"function": func.__name__, "status": "error"}
                        if tags:
                            metric_tags.update(tags)

                        loop.create_task(
                            telemetry_manager.record_timer(
                                name=metric_name,
                                duration=duration,
                                tags=metric_tags,
                            )
                        )
                    except RuntimeError:
                        pass

                    raise

            return sync_wrapper

    return decorator


def auto_log_route(level: LogLevel = LogLevel.INFO, source_prefix: str = "api.route"):
    """
    Decorator to automatically log FastAPI route entry and exit.

    This provides detailed logging for router endpoints including:
    - Route entry with parameters
    - Route exit with duration
    - Automatic error logging
    - Telemetry integration for performance tracking

    Note: This decorator only works with async functions.

    Args:
        level: Log level to use for entry/exit logs (default: INFO).
        source_prefix: Prefix for the source identifier.

    Example:
        @router.get("/users/{user_id}")
        @auto_log_route(level=LogLevel.INFO, source_prefix="api.users")
        async def get_user(user_id: str):
            return {"user_id": user_id}
    """

    def decorator(func: Callable) -> Callable:
        if not inspect.iscoroutinefunction(func):
            raise TypeError(
                f"@auto_log_route can only be applied to async functions. "
                f"Function '{func.__name__}' is not async."
            )

        source = f"{source_prefix}.{func.__name__}"

        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            log_manager = LogManager.get_instance()
            telemetry_manager = TelemetryManager.get_instance()
            start_time = time.perf_counter()

            # Log Entry (sanitize kwargs to avoid logging large objects or sensitive data)
            await log_manager.log(
                level=level,
                message=f"Route {func.__name__} called",
                source=source,
                context={"kwargs": {k: _sanitize_value(v) for k, v in kwargs.items()}},
            )

            try:
                result = await func(*args, **kwargs)
                duration = time.perf_counter() - start_time

                # Log Success
                await log_manager.log(
                    level=level,
                    message=f"Route {func.__name__} completed (Duration: {duration:.4f}s)",
                    source=source,
                    context={"duration": duration},
                )

                # Record telemetry
                await telemetry_manager.record_timer(
                    name=f"route.duration.{func.__name__}",
                    duration=duration,
                    tags={"route": func.__name__, "status": "success"},
                )
                await telemetry_manager.record_counter(
                    name=f"route.calls.{func.__name__}",
                    value=1.0,
                    tags={"route": func.__name__, "status": "success"},
                )

                return result

            except Exception as e:
                duration = time.perf_counter() - start_time

                # Log Exception
                await log_manager.log(
                    level=LogLevel.ERROR,
                    message=f"Route {func.__name__} failed: {str(e)}",
                    source=source,
                    context={"error": str(e), "duration": duration},
                )

                # Record telemetry for failures
                await telemetry_manager.record_counter(
                    name=f"route.calls.{func.__name__}",
                    value=1.0,
                    tags={"route": func.__name__, "status": "error"},
                )
                await telemetry_manager.record_counter(
                    name="route.errors.total",
                    value=1.0,
                    tags={"route": func.__name__},
                )

                raise

        return wrapper

    return decorator
