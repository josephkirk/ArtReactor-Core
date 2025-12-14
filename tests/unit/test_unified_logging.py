"""Unit tests for unified logging across components."""

import pytest
import pytest_asyncio
from artreactor.core.logging.manager import LogManager
from artreactor.core.logging.types import LogEntry, LogLevel
from artreactor.core.logging.interface import LogProvider


class MockLogProvider(LogProvider):
    """Mock log provider for testing."""

    def __init__(self, name="mock"):
        self.name = name
        self.logs = []
        self.initialized = False
        self.shutdown_called = False

    async def log(self, entry: LogEntry):
        self.logs.append(entry)

    async def initialize(self):
        self.initialized = True

    async def shutdown(self):
        self.shutdown_called = True


@pytest_asyncio.fixture
async def log_manager_setup():
    """Setup log manager with clean state."""
    manager = LogManager.get_instance()
    manager.clear_providers()
    manager.clear_subscribers()
    return manager


@pytest.mark.asyncio
async def test_multiple_log_providers(log_manager_setup):
    """Test that multiple log providers can be registered and receive logs."""
    manager = log_manager_setup

    provider1 = MockLogProvider(name="provider1")
    provider2 = MockLogProvider(name="provider2")
    provider3 = MockLogProvider(name="provider3")

    # Register multiple providers
    manager.register_provider(provider1)
    manager.register_provider(provider2)
    manager.register_provider(provider3)

    await manager.initialize()

    # Verify all providers initialized
    assert provider1.initialized
    assert provider2.initialized
    assert provider3.initialized

    # Log a message
    await manager.info("Test message", source="test.source")

    # All providers should receive the log
    assert len(provider1.logs) == 1
    assert len(provider2.logs) == 1
    assert len(provider3.logs) == 1

    # Verify log content
    for provider in [provider1, provider2, provider3]:
        log = provider.logs[0]
        assert log.message == "Test message"
        assert log.source == "test.source"
        assert log.level == LogLevel.INFO


@pytest.mark.asyncio
async def test_log_subscribers(log_manager_setup):
    """Test that log subscribers receive log events."""
    manager = log_manager_setup

    received_logs = []

    async def subscriber(entry: LogEntry):
        received_logs.append(entry)

    manager.subscribe(subscriber)

    await manager.info("Test message", source="test")

    assert len(received_logs) == 1
    assert received_logs[0].message == "Test message"


@pytest.mark.asyncio
async def test_multiple_subscribers(log_manager_setup):
    """Test that multiple subscribers all receive log events."""
    manager = log_manager_setup

    logs1 = []
    logs2 = []
    logs3 = []

    async def subscriber1(entry: LogEntry):
        logs1.append(entry)

    async def subscriber2(entry: LogEntry):
        logs2.append(entry)

    async def subscriber3(entry: LogEntry):
        logs3.append(entry)

    manager.subscribe(subscriber1)
    manager.subscribe(subscriber2)
    manager.subscribe(subscriber3)

    await manager.info("Test message", source="test")

    assert len(logs1) == 1
    assert len(logs2) == 1
    assert len(logs3) == 1


@pytest.mark.asyncio
async def test_subscriber_resilience(log_manager_setup):
    """Test that failing subscribers don't affect logging or other subscribers."""
    manager = log_manager_setup

    successful_logs = []

    async def failing_subscriber(entry: LogEntry):
        raise ValueError("Intentional error")

    async def successful_subscriber(entry: LogEntry):
        successful_logs.append(entry)

    provider = MockLogProvider()
    manager.register_provider(provider)
    manager.subscribe(failing_subscriber)
    manager.subscribe(successful_subscriber)

    # This should not raise an exception
    await manager.info("Test message", source="test")

    # Provider should still receive the log
    assert len(provider.logs) == 1

    # Successful subscriber should still receive the log
    assert len(successful_logs) == 1


@pytest.mark.asyncio
async def test_context_propagation(log_manager_setup):
    """Test that trace context is properly propagated."""
    manager = log_manager_setup
    provider = MockLogProvider()
    manager.register_provider(provider)

    trace_id = "trace-123"
    span_id = "span-456"

    manager.set_context(trace_id, span_id)

    await manager.info("Test message", source="test")

    log = provider.logs[0]
    assert log.trace_id == trace_id
    assert log.span_id == span_id


@pytest.mark.asyncio
async def test_log_levels(log_manager_setup):
    """Test all log levels."""
    manager = log_manager_setup
    provider = MockLogProvider()
    manager.register_provider(provider)

    await manager.debug("Debug", source="test")
    await manager.info("Info", source="test")
    await manager.warning("Warning", source="test")
    await manager.error("Error", source="test")
    await manager.critical("Critical", source="test")

    assert len(provider.logs) == 5
    assert provider.logs[0].level == LogLevel.DEBUG
    assert provider.logs[1].level == LogLevel.INFO
    assert provider.logs[2].level == LogLevel.WARNING
    assert provider.logs[3].level == LogLevel.ERROR
    assert provider.logs[4].level == LogLevel.CRITICAL


@pytest.mark.asyncio
async def test_shutdown(log_manager_setup):
    """Test that shutdown is called on all providers."""
    manager = log_manager_setup

    provider1 = MockLogProvider()
    provider2 = MockLogProvider()

    manager.register_provider(provider1)
    manager.register_provider(provider2)

    await manager.shutdown()

    assert provider1.shutdown_called
    assert provider2.shutdown_called
