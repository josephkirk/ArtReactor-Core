"""Unit tests for telemetry system."""

import pytest
import pytest_asyncio
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
async def test_telemetry_counter(telemetry_setup):
    """Test counter metric recording."""
    manager, provider = telemetry_setup

    await manager.record_counter("test.counter", value=5.0, tags={"env": "test"})
    await manager.record_counter("test.counter", value=3.0, tags={"env": "test"})

    assert provider.get_counter("test.counter") == 8.0
    assert len(provider.events) == 2


@pytest.mark.asyncio
async def test_telemetry_gauge(telemetry_setup):
    """Test gauge metric recording."""
    manager, provider = telemetry_setup

    await manager.record_gauge("test.gauge", value=42.0)
    assert provider.get_gauge("test.gauge") == 42.0

    await manager.record_gauge("test.gauge", value=100.0)
    assert provider.get_gauge("test.gauge") == 100.0  # Gauge is point-in-time


@pytest.mark.asyncio
async def test_telemetry_histogram(telemetry_setup):
    """Test histogram metric recording."""
    manager, provider = telemetry_setup

    await manager.record_histogram("test.histogram", value=10.0)
    await manager.record_histogram("test.histogram", value=20.0)
    await manager.record_histogram("test.histogram", value=30.0)

    histogram_values = provider.get_histogram("test.histogram")
    assert len(histogram_values) == 3
    assert histogram_values == [10.0, 20.0, 30.0]


@pytest.mark.asyncio
async def test_telemetry_timer(telemetry_setup):
    """Test timer metric recording."""
    manager, provider = telemetry_setup

    await manager.record_timer("test.operation", duration=1.5)
    await manager.record_timer("test.operation", duration=2.3)

    timer_values = provider.get_timers("test.operation")
    assert len(timer_values) == 2
    assert timer_values == [1.5, 2.3]


@pytest.mark.asyncio
async def test_multiple_telemetry_providers():
    """Test that multiple providers can be registered and receive events."""
    manager = TelemetryManager.get_instance()
    manager.clear_providers()

    provider1 = InMemoryTelemetryProvider(name="provider1")
    provider2 = InMemoryTelemetryProvider(name="provider2")

    manager.register_provider(provider1)
    manager.register_provider(provider2)

    await manager.record_counter("test.multi", value=1.0)

    # Both providers should have received the event
    assert provider1.get_counter("test.multi") == 1.0
    assert provider2.get_counter("test.multi") == 1.0


@pytest.mark.asyncio
async def test_telemetry_tags_and_context(telemetry_setup):
    """Test that tags and context are properly stored."""
    manager, provider = telemetry_setup

    await manager.record_counter(
        "test.tagged",
        value=1.0,
        tags={"environment": "prod", "service": "api"},
        context={"user_id": "123", "request_id": "abc"},
    )

    event = provider.events[0]
    assert event.tags["environment"] == "prod"
    assert event.tags["service"] == "api"
    assert event.context["user_id"] == "123"
    assert event.context["request_id"] == "abc"
