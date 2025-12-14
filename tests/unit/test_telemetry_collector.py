"""Unit tests for telemetry collector integration with logging."""

import pytest
import pytest_asyncio
from artreactor.core.logging.manager import LogManager

from artreactor.core.telemetry.manager import TelemetryManager
from artreactor.core.telemetry.collector import TelemetryCollector
from artreactor.core.telemetry.providers.memory import InMemoryTelemetryProvider


@pytest_asyncio.fixture
async def log_telemetry_integration():
    """Setup integrated logging and telemetry."""
    # Setup LogManager using singleton
    log_manager = LogManager.get_instance()
    log_manager.clear_providers()
    log_manager.clear_subscribers()

    # Setup TelemetryManager using singleton
    telemetry_manager = TelemetryManager.get_instance()
    telemetry_manager.clear_providers()

    # Create and register provider
    telemetry_provider = InMemoryTelemetryProvider()
    telemetry_manager.register_provider(telemetry_provider)

    # Setup TelemetryCollector using singleton (will use the same TelemetryManager)
    collector = TelemetryCollector.get_instance()

    # Ensure collector has fresh reference to telemetry manager
    # (in case it was created before and cached a different instance)
    collector._telemetry_manager = telemetry_manager

    # Wire up collector to log manager
    log_manager.subscribe(collector.on_log_entry)

    return log_manager, telemetry_manager, telemetry_provider, collector


@pytest.mark.asyncio
async def test_log_event_generates_telemetry(log_telemetry_integration):
    """Test that log events automatically generate telemetry metrics."""
    log_manager, telemetry_manager, telemetry_provider, collector = (
        log_telemetry_integration
    )

    await log_manager.info("Test message", source="test.source")

    # Check that telemetry was recorded
    assert len(telemetry_provider.events) > 0

    # Check counter for log level
    assert telemetry_provider.get_counter("log.count.info") == 1.0

    # Check counter for source
    assert telemetry_provider.get_counter("log.source.test.source") == 1.0


@pytest.mark.asyncio
async def test_error_logs_generate_extra_telemetry(log_telemetry_integration):
    """Test that error logs generate additional telemetry metrics."""
    log_manager, telemetry_manager, telemetry_provider, collector = (
        log_telemetry_integration
    )

    await log_manager.error("Error message", source="test.error")

    # Check error-specific counter
    assert telemetry_provider.get_counter("log.errors.total") == 1.0
    assert telemetry_provider.get_counter("log.count.error") == 1.0


@pytest.mark.asyncio
async def test_duration_context_generates_timer(log_telemetry_integration):
    """Test that log entries with duration context generate timer metrics."""
    log_manager, telemetry_manager, telemetry_provider, collector = (
        log_telemetry_integration
    )

    await log_manager.info("Operation completed", source="test.operation", duration=2.5)

    # Check that duration was recorded as a timer
    timers = telemetry_provider.get_timers("operation.duration.test.operation")
    assert len(timers) == 1
    assert timers[0] == 2.5


@pytest.mark.asyncio
async def test_multiple_log_levels_counted_separately(log_telemetry_integration):
    """Test that different log levels are counted separately."""
    log_manager, telemetry_manager, telemetry_provider, collector = (
        log_telemetry_integration
    )

    await log_manager.debug("Debug message", source="test")
    await log_manager.info("Info message", source="test")
    await log_manager.warning("Warning message", source="test")
    await log_manager.error("Error message", source="test")

    assert telemetry_provider.get_counter("log.count.debug") == 1.0
    assert telemetry_provider.get_counter("log.count.info") == 1.0
    assert telemetry_provider.get_counter("log.count.warning") == 1.0
    assert telemetry_provider.get_counter("log.count.error") == 1.0


@pytest.mark.asyncio
async def test_telemetry_collector_resilience(log_telemetry_integration):
    """Test that telemetry collector doesn't crash on errors."""
    log_manager, telemetry_manager, telemetry_provider, collector = (
        log_telemetry_integration
    )

    # Create a broken telemetry manager that raises exceptions
    class BrokenTelemetryManager:
        async def record_counter(self, *args, **kwargs):
            raise ValueError("Intentional error")

        async def record_timer(self, *args, **kwargs):
            raise ValueError("Intentional error")

    collector._telemetry_manager = BrokenTelemetryManager()

    # This should not raise an exception - the error should be caught and printed to stderr
    try:
        await log_manager.info("Test message", source="test")
        # If we reach here without exception, test passes
        assert True
    except Exception as e:
        pytest.fail(f"Telemetry errors should not propagate: {e}")
