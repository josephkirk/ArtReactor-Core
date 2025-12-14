"""Integration tests for router auto-logging decorator."""

import pytest
import pytest_asyncio
from fastapi import FastAPI, APIRouter
from fastapi.testclient import TestClient
from artreactor.api.decorators import auto_log_route
from artreactor.core.logging.manager import LogManager, LogLevel
from artreactor.core.logging.interface import LogProvider
from artreactor.core.logging.types import LogEntry
from artreactor.core.telemetry.manager import TelemetryManager
from artreactor.core.telemetry.providers.memory import InMemoryTelemetryProvider


class MockLogProvider(LogProvider):
    """Mock log provider for testing."""

    def __init__(self):
        self.logs = []

    async def log(self, entry: LogEntry):
        self.logs.append(entry)

    async def initialize(self):
        pass

    async def shutdown(self):
        pass


@pytest_asyncio.fixture
async def app_with_auto_logging():
    """Setup FastAPI app with auto-logging decorator."""
    app = FastAPI()
    router = APIRouter()

    # Setup logging using singletons (as the decorator does)
    log_manager = LogManager.get_instance()
    log_manager.clear_providers()
    log_manager.clear_subscribers()
    log_provider = MockLogProvider()
    log_manager.register_provider(log_provider)

    # Setup telemetry using singletons (as the decorator does)
    telemetry_manager = TelemetryManager.get_instance()
    telemetry_manager.clear_providers()
    telemetry_provider = InMemoryTelemetryProvider()
    telemetry_manager.register_provider(telemetry_provider)

    @router.get("/test/{item_id}")
    @auto_log_route(level=LogLevel.INFO, source_prefix="api.test")
    async def get_item(item_id: str):
        return {"item_id": item_id}

    @router.post("/items")
    @auto_log_route(level=LogLevel.DEBUG, source_prefix="api.items")
    async def create_item(name: str):
        return {"name": name, "status": "created"}

    @router.get("/error")
    @auto_log_route(level=LogLevel.INFO, source_prefix="api.test")
    async def error_endpoint():
        raise ValueError("Test error")

    app.include_router(router)

    return app, log_provider, telemetry_provider


@pytest.mark.asyncio
async def test_route_entry_exit_logging(app_with_auto_logging):
    """Test that routes log entry and exit."""
    app, log_provider, telemetry_provider = app_with_auto_logging
    client = TestClient(app)

    response = client.get("/test/123")
    assert response.status_code == 200

    # Should have entry and exit logs
    logs = [log for log in log_provider.logs if log.source.startswith("api.test")]
    assert len(logs) >= 2

    entry_log = logs[0]
    assert "called" in entry_log.message.lower()
    assert entry_log.source == "api.test.get_item"

    exit_log = logs[1]
    assert "completed" in exit_log.message.lower()
    assert "duration" in exit_log.context


@pytest.mark.asyncio
async def test_route_error_logging(app_with_auto_logging):
    """Test that route errors are logged."""
    app, log_provider, telemetry_provider = app_with_auto_logging
    client = TestClient(app)

    with pytest.raises(ValueError):
        client.get("/error")

    # Should have entry and error logs
    error_logs = [
        log
        for log in log_provider.logs
        if log.level == LogLevel.ERROR and log.source.startswith("api.test")
    ]
    assert len(error_logs) >= 1

    error_log = error_logs[0]
    assert "failed" in error_log.message.lower()
    assert "Test error" in error_log.message
    assert error_log.source == "api.test.error_endpoint"
    assert "error" in error_log.context
    assert "duration" in error_log.context


@pytest.mark.asyncio
async def test_route_telemetry_integration(app_with_auto_logging):
    """Test that routes generate telemetry metrics."""
    app, log_provider, telemetry_provider = app_with_auto_logging
    client = TestClient(app)

    response = client.get("/test/123")
    assert response.status_code == 200

    # Check telemetry counters
    counter_value = telemetry_provider.get_counter("route.calls.get_item")
    assert counter_value == 1.0

    # Check telemetry timers
    timers = telemetry_provider.get_timers("route.duration.get_item")
    assert len(timers) == 1
    assert timers[0] > 0  # Should have some duration


@pytest.mark.asyncio
async def test_route_error_telemetry(app_with_auto_logging):
    """Test that route errors generate error telemetry."""
    app, log_provider, telemetry_provider = app_with_auto_logging
    client = TestClient(app)

    with pytest.raises(ValueError):
        client.get("/error")

    # Check error counter
    error_counter = telemetry_provider.get_counter("route.errors.total")
    assert error_counter == 1.0


@pytest.mark.asyncio
async def test_multiple_route_calls(app_with_auto_logging):
    """Test that multiple route calls accumulate metrics correctly."""
    app, log_provider, telemetry_provider = app_with_auto_logging
    client = TestClient(app)

    # Make multiple calls
    for i in range(5):
        response = client.get(f"/test/{i}")
        assert response.status_code == 200

    # Check that counter accumulated
    counter_value = telemetry_provider.get_counter("route.calls.get_item")
    assert counter_value == 5.0

    # Check that we have 5 timing entries
    timers = telemetry_provider.get_timers("route.duration.get_item")
    assert len(timers) == 5
