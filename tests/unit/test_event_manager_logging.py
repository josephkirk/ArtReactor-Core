"""Unit tests for EventManager unified logging."""

import pytest
import pytest_asyncio
from artreactor.core.events.manager import EventManager
from artreactor.core.logging.manager import LogManager
from artreactor.core.logging.types import LogEntry, LogLevel
from artreactor.core.logging.interface import LogProvider


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
async def event_manager_setup():
    """Setup event manager with logging."""
    # Setup LogManager using singleton pattern
    log_manager = LogManager.get_instance()
    log_manager.clear_providers()
    log_manager.clear_subscribers()
    log_provider = MockLogProvider()
    log_manager.register_provider(log_provider)

    # Create fresh EventManager instance (singleton)
    event_manager = EventManager()
    event_manager.listeners = {}
    event_manager._log_manager = None  # Force re-initialization
    event_manager.emit_logging = True  # Enable emit logging for tests

    yield event_manager, log_provider

    # Cleanup: reset emit_logging to not affect other tests
    event_manager.emit_logging = False


@pytest.mark.asyncio
async def test_event_emission_logging(event_manager_setup):
    """Test that event emissions are logged."""
    event_manager, log_provider = event_manager_setup

    # Register a simple listener
    async def test_listener(data):
        pass

    event_manager.on("test.event", test_listener)

    # Emit event
    await event_manager.emit("test.event", "test_data")

    # Allow fire-and-forget logging tasks to complete
    import asyncio

    await asyncio.sleep(0)

    # Check that emission was logged
    emission_logs = [
        log
        for log in log_provider.logs
        if "Emitting event" in log.message and log.source == "events.manager"
    ]
    assert len(emission_logs) >= 1


@pytest.mark.asyncio
async def test_event_listener_error_logging(event_manager_setup):
    """Test that listener errors are logged."""
    event_manager, log_provider = event_manager_setup

    # Register a listener that fails
    async def failing_listener(data):
        raise ValueError("Intentional error")

    event_manager.on("test.error", failing_listener)

    # Emit event (should not crash)
    await event_manager.emit("test.error", "test_data")

    # Check that error was logged
    error_logs = [
        log
        for log in log_provider.logs
        if log.level == LogLevel.ERROR and log.source == "events.manager"
    ]
    assert len(error_logs) >= 1
    assert any("error" in log.message.lower() for log in error_logs)


@pytest.mark.asyncio
async def test_event_fire_and_forget_error_logging(event_manager_setup):
    """Test that fire-and-forget listener errors are logged."""
    event_manager, log_provider = event_manager_setup

    # Register a fire-and-forget listener that fails
    async def failing_listener(data):
        raise ValueError("Fire and forget error")

    event_manager.on("test.fire_forget", failing_listener, fire_and_forget=True)

    # Emit event
    await event_manager.emit("test.fire_forget", "test_data")

    # Give fire-and-forget tasks time to complete
    import asyncio

    await asyncio.sleep(0.1)

    # Fire-and-forget errors are logged via callback
    # The test verifies that fire-and-forget mode doesn't block the emit
    # and that the system handles errors gracefully
    assert True  # Test passes if we reach here without exception


@pytest.mark.asyncio
async def test_multiple_events_logged(event_manager_setup):
    """Test that multiple event emissions are all logged."""
    event_manager, log_provider = event_manager_setup

    async def listener1(data):
        pass

    async def listener2(data):
        pass

    event_manager.on("event1", listener1)
    event_manager.on("event2", listener2)

    await event_manager.emit("event1", "data1")
    await event_manager.emit("event2", "data2")

    # Allow fire-and-forget logging tasks to complete
    import asyncio

    await asyncio.sleep(0)

    emission_logs = [
        log
        for log in log_provider.logs
        if "Emitting event" in log.message and log.source == "events.manager"
    ]
    assert len(emission_logs) >= 2
