import pytest
import pytest_asyncio
from typing import List
from artreactor.core.logging.manager import LogManager, LogLevel, LogEntry, LogProvider
from artreactor.core.logging.decorators import track_call
from artreactor.core.logging.providers.console import ConsoleLogProvider


# Mock Provider
class MockLogProvider(LogProvider):
    def __init__(self):
        self.logs: List[LogEntry] = []

    async def initialize(self):
        pass

    async def shutdown(self):
        pass

    async def log(self, entry: LogEntry):
        self.logs.append(entry)


@pytest_asyncio.fixture
async def log_manager():
    # Reset singleton provided it's just a class instance in tests if we didn't enforce strict singleton
    # But LogManager is a singleton.
    # We should clear providers between tests.
    manager = LogManager.get_instance()
    manager._providers = []
    manager._subscribers = []
    return manager


@pytest.mark.asyncio
async def test_log_manager_singleton():
    m1 = LogManager.get_instance()
    m2 = LogManager.get_instance()
    assert m1 is m2


@pytest.mark.asyncio
async def test_log_flow(log_manager):
    mock_provider = MockLogProvider()
    log_manager.register_provider(mock_provider)

    await log_manager.info("Test message", "test.source")

    assert len(mock_provider.logs) == 1
    entry = mock_provider.logs[0]
    assert entry.message == "Test message"
    assert entry.level == LogLevel.INFO
    assert entry.source == "test.source"


@pytest.mark.asyncio
async def test_pub_sub(log_manager):
    received_entries = []

    async def subscriber(entry: LogEntry):
        received_entries.append(entry)

    log_manager.subscribe(subscriber)

    await log_manager.warning("Warning msg", "test.pubsub")

    # Since pub/sub is fire-and-forget in implementation, need to yield to loop
    # or ensure it ran.
    # In my implementation:
    # for subscriber in self._subscribers: await subscriber(entry)
    # So it IS awaited (with try/except).

    assert len(received_entries) == 1
    assert received_entries[0].message == "Warning msg"


@pytest.mark.asyncio
async def test_decorator(log_manager):
    mock_provider = MockLogProvider()
    log_manager.register_provider(mock_provider)

    @track_call(level=LogLevel.DEBUG, source="test.func")
    async def decorated_func(x: int):
        return x * 2

    result = await decorated_func(5)

    assert result == 10

    # Should have Entry and Exit logs
    # Since we used create_task for decorator logic, we might need to wait a bit
    # Wait, in the implementation I wrote:
    # "await logger.log(..." inside async_wrapper.
    # So for async functions it IS awaited.

    assert len(mock_provider.logs) == 2
    assert "Entering decorated_func" in mock_provider.logs[0].message
    assert "Exiting decorated_func" in mock_provider.logs[1].message
    assert mock_provider.logs[0].source == "test.func"


@pytest.mark.asyncio
async def test_context_vars(log_manager):
    mock_provider = MockLogProvider()
    log_manager.register_provider(mock_provider)

    log_manager.set_context("trace-123", "span-456")

    await log_manager.info("Context test", "ctx")

    entry = mock_provider.logs[0]
    assert entry.trace_id == "trace-123"
    assert entry.span_id == "span-456"


@pytest.mark.asyncio
async def test_console_provider():
    # Just ensure it doesn't crash
    provider = ConsoleLogProvider()
    entry = LogEntry(level=LogLevel.INFO, message="Console test", source="test.console")
    await provider.log(entry)
