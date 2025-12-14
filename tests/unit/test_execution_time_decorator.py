"""Unit tests for execution time tracking decorator."""

import pytest
import pytest_asyncio
import asyncio
from artreactor.api.decorators import track_execution_time
from artreactor.core.telemetry.manager import TelemetryManager
from artreactor.core.telemetry.providers.memory import InMemoryTelemetryProvider


@pytest_asyncio.fixture
async def telemetry_setup():
    """Setup telemetry manager with in-memory provider."""
    manager = TelemetryManager.get_instance()
    manager.clear_providers()
    provider = InMemoryTelemetryProvider()
    manager.register_provider(provider)
    await manager.initialize()
    return manager, provider


@pytest.mark.asyncio
async def test_track_execution_time_async_success(telemetry_setup):
    """Test that async function execution time is tracked."""
    manager, provider = telemetry_setup

    @track_execution_time(metric_name="test.async.duration")
    async def async_function():
        await asyncio.sleep(0.01)
        return "result"

    result = await async_function()

    assert result == "result"

    # Check that telemetry was recorded
    timers = provider.get_timers("test.async.duration")
    assert len(timers) == 1
    assert timers[0] >= 0.01  # Should take at least 10ms


@pytest.mark.asyncio
async def test_track_execution_time_async_with_tags(telemetry_setup):
    """Test that tags are properly attached to telemetry."""
    manager, provider = telemetry_setup

    @track_execution_time(
        metric_name="test.tagged.duration", tags={"env": "test", "version": "1.0"}
    )
    async def async_function():
        return "result"

    await async_function()

    # Check that telemetry was recorded with tags
    events = [e for e in provider.events if e.metric_name == "test.tagged.duration"]
    assert len(events) == 1
    assert events[0].tags["env"] == "test"
    assert events[0].tags["version"] == "1.0"
    assert events[0].tags["function"] == "async_function"
    assert events[0].tags["status"] == "success"


@pytest.mark.asyncio
async def test_track_execution_time_async_error(telemetry_setup):
    """Test that errors are tracked with error status."""
    manager, provider = telemetry_setup

    @track_execution_time(metric_name="test.error.duration")
    async def failing_function():
        raise ValueError("Test error")

    with pytest.raises(ValueError):
        await failing_function()

    # Check that telemetry was recorded with error status
    events = [e for e in provider.events if e.metric_name == "test.error.duration"]
    assert len(events) == 1
    assert events[0].tags["status"] == "error"


@pytest.mark.asyncio
async def test_track_execution_time_default_metric_name(telemetry_setup):
    """Test that default metric name is generated from function name."""
    manager, provider = telemetry_setup

    @track_execution_time()
    async def my_custom_function():
        return "result"

    await my_custom_function()

    # Check that default metric name was used
    timers = provider.get_timers("function.my_custom_function.duration")
    assert len(timers) == 1


@pytest.mark.asyncio
async def test_track_execution_time_sync_with_loop():
    """Test that sync function execution time is tracked when running in async context."""
    manager = TelemetryManager.get_instance()
    manager.clear_providers()
    provider = InMemoryTelemetryProvider()
    manager.register_provider(provider)

    @track_execution_time(metric_name="test.sync.duration")
    def sync_function():
        import time

        time.sleep(0.01)
        return "result"

    # Call sync function from async context
    result = sync_function()

    assert result == "result"

    # Give the fire-and-forget task time to complete
    await asyncio.sleep(0.1)

    # Check that telemetry was recorded
    timers = provider.get_timers("test.sync.duration")
    assert len(timers) == 1
    assert timers[0] >= 0.01


def test_track_execution_time_sync_without_loop():
    """Test that sync function works without async loop (telemetry skipped)."""

    @track_execution_time(metric_name="test.noop.duration")
    def sync_function():
        return "result"

    # This should work without crashing even though there's no loop
    result = sync_function()
    assert result == "result"
