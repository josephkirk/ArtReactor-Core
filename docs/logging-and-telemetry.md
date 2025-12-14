# Unified Logging and Telemetry System

artreactor Core now features a robust, unified logging and telemetry system that provides consistent logging across all components and automatic metrics collection.

## Architecture Overview

The system consists of three main components:

1. **LogManager** - Central logging coordinator
2. **TelemetryManager** - Metrics and telemetry coordinator
3. **TelemetryCollector** - Bridge between logging and telemetry

## Features

### Application Telemetry

The application automatically tracks key performance metrics:

- **Startup Time**: Time taken to initialize all components and start the application
- **Shutdown Time**: Time taken to gracefully shut down all components
- **Request Metrics**: Automatic tracking via middleware (when using `@auto_log_route`)

These metrics are automatically recorded and available through registered telemetry providers.

### Unified Logging

All components in the system (core, API routes, event manager, etc.) use the same LogManager for consistent logging.

```python
from artreactor.core.logging import LogManager

log_manager = LogManager.get_instance()
await log_manager.info("User logged in", source="auth.service", user_id="123")
```

### Multiple Log Providers

You can register multiple log providers that will all receive log events:

```python
from artreactor.core.logging import LogManager
from artreactor.core.logging.providers.console import ConsoleLogProvider

log_manager = LogManager.get_instance()

# Register multiple providers
log_manager.register_provider(ConsoleLogProvider())
log_manager.register_provider(FileLogProvider("/var/log/app.log"))
log_manager.register_provider(SentryLogProvider())

await log_manager.initialize()
```

### Log Subscribers

You can subscribe to log events for custom processing:

```python
async def my_log_handler(entry: LogEntry):
    if entry.level == LogLevel.ERROR:
        # Send alert
        await send_alert(entry.message)

log_manager.subscribe(my_log_handler)
```

### Auto-logging for API Routes

Use the `@auto_log_route` decorator to automatically log API route entry, exit, duration, and errors:

```python
from fastapi import APIRouter
from artreactor.api.decorators import auto_log_route
from artreactor.core.logging.types import LogLevel

router = APIRouter()

@router.get("/users/{user_id}")
@auto_log_route(level=LogLevel.INFO, source_prefix="api.users")
async def get_user(user_id: str):
    return {"user_id": user_id}
```

This automatically:
- Logs when the route is called
- Logs when it completes with duration
- Logs errors if they occur
- Records telemetry metrics

### Execution Time Tracking Decorator

Use the `@track_execution_time` decorator to track execution time for any function:

```python
from artreactor.api.decorators import track_execution_time

# For async functions
@track_execution_time(metric_name="process_data.duration", tags={"env": "prod"})
async def process_data(data):
    # Process data
    return result

# For sync functions (works in async context)
@track_execution_time()
def calculate_score(value):
    # Metric name defaults to "function.calculate_score.duration"
    return value * 2

# With custom tags
@track_execution_time(
    metric_name="database.query.duration",
    tags={"table": "users", "operation": "select"}
)
async def query_users():
    return await db.query("SELECT * FROM users")
```

The decorator:
- Works with both sync and async functions
- Automatically records execution time as telemetry
- Tracks success/error status
- Supports custom metric names and tags
- Defaults to `function.{function_name}.duration` if no metric name provided

### Event Manager Auto-logging

The EventManager now uses the unified LogManager for all its logging:

```python
from artreactor.core.events.manager import event_manager

# Event emissions are automatically logged
await event_manager.emit("user.created", user_data)
```

### Function Call Tracking

Use the `@track_call` decorator to log function entry/exit:

```python
from artreactor.core.logging.decorators import track_call
from artreactor.core.logging.types import LogLevel

@track_call(level=LogLevel.DEBUG, source="service.user")
async def create_user(name: str):
    # Function automatically logged
    return User(name=name)
```

## Telemetry System

### Automatic Metrics from Logs

The TelemetryCollector automatically generates metrics from log events:

- **Log counts by level**: `log.count.info`, `log.count.error`, etc.
- **Log counts by source**: `log.source.api.users`, etc.
- **Error counts**: `log.errors.total`
- **Operation durations**: Extracted from log context

### Manual Metrics Recording

Record custom metrics directly:

```python
from artreactor.core.telemetry import TelemetryManager

telemetry = TelemetryManager.get_instance()

# Counter
await telemetry.record_counter("api.requests", value=1.0, tags={"endpoint": "/users"})

# Gauge
await telemetry.record_gauge("cache.size", value=1024.0)

# Histogram
await telemetry.record_histogram("request.size", value=512.0)

# Timer
await telemetry.record_timer("database.query", duration=0.123)
```

### Telemetry Providers

Register multiple telemetry providers:

```python
from artreactor.core.telemetry import TelemetryManager
from artreactor.core.telemetry.providers.memory import InMemoryTelemetryProvider

telemetry = TelemetryManager.get_instance()
telemetry.register_provider(InMemoryTelemetryProvider())
await telemetry.initialize()
```

### Plugin Integration

Create custom telemetry providers as plugins:

```python
from artreactor.core.interfaces.telemetry_plugin import TelemetryPlugin
from artreactor.core.telemetry.interface import TelemetryProvider

class MyTelemetryPlugin(TelemetryPlugin):
    def get_provider(self) -> TelemetryProvider:
        return GrafanaProvider(api_key="...")
```

## Context Propagation

Set trace context for distributed tracing:

```python
log_manager = LogManager.get_instance()
log_manager.set_context(trace_id="abc-123", span_id="span-456")

# All subsequent logs will include this context
await log_manager.info("Processing request", source="api")
```

## Best Practices

1. **Use consistent source identifiers**: Use dot notation like `api.users`, `service.auth`
2. **Include context in logs**: Pass relevant data as kwargs
3. **Let errors bubble**: The auto-logging will capture them
4. **Use appropriate log levels**: DEBUG for dev, INFO for important events, ERROR for failures
5. **Register providers early**: During application startup
6. **Don't log sensitive data**: Avoid passwords, tokens, etc.

## Example: Complete Setup

```python
from artreactor.core.logging import LogManager
from artreactor.core.logging.providers.console import ConsoleLogProvider
from artreactor.core.telemetry import TelemetryManager, TelemetryCollector
from artreactor.core.telemetry.providers.memory import InMemoryTelemetryProvider

# Initialize logging
log_manager = LogManager.get_instance()
log_manager.register_provider(ConsoleLogProvider())
await log_manager.initialize()

# Initialize telemetry
telemetry_manager = TelemetryManager.get_instance()
telemetry_manager.register_provider(InMemoryTelemetryProvider())
await telemetry_manager.initialize()

# Wire up collector to subscribe to logs
collector = TelemetryCollector.get_instance()
log_manager.subscribe(collector.on_log_entry)

# Now all logging automatically generates telemetry!
await log_manager.info("Application started", source="app")
```

## Plugin Development

### Custom Log Provider

```python
from artreactor.core.logging.interface import LogProvider
from artreactor.core.logging.types import LogEntry

class MyLogProvider(LogProvider):
    async def log(self, entry: LogEntry) -> None:
        # Send to external service
        await send_to_service(entry)
    
    async def initialize(self) -> None:
        # Setup connections
        pass
    
    async def shutdown(self) -> None:
        # Cleanup
        pass
```

### Custom Telemetry Provider

```python
from artreactor.core.telemetry.interface import TelemetryProvider
from artreactor.core.telemetry.types import TelemetryEvent

class SentryTelemetryProvider(TelemetryProvider):
    async def record(self, event: TelemetryEvent) -> None:
        # Send to Sentry
        await sentry_client.send_metric(event)
    
    async def initialize(self) -> None:
        # Initialize Sentry client
        pass
    
    async def shutdown(self) -> None:
        # Flush and close
        pass
    
    async def flush(self) -> None:
        # Force flush
        pass
```

## Migration Guide

### From Python's `logging` module

Replace:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("message")
```

With:
```python
from artreactor.core.logging import LogManager
log_manager = LogManager.get_instance()
await log_manager.info("message", source=__name__)
```

### Adding to Existing Routes

Simply add the decorator:
```python
@router.get("/endpoint")
@auto_log_route()  # Add this line
async def my_endpoint():
    pass
```

## Performance Considerations

- Log providers are called in parallel (non-blocking)
- Telemetry collection doesn't block logging
- Use fire-and-forget pattern for non-critical logs
- Subscribers fail silently to prevent crashes

## Security Notes

- Never log passwords, API keys, or tokens
- Sanitize user input before logging
- Use appropriate log levels for sensitive operations
- Consider log retention policies
- Implement log rotation for file-based providers
