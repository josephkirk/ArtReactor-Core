import pytest
import asyncio
from artreactor.core.events import EventManager, event, on


# Reset singleton for tests
@pytest.fixture(autouse=True)
def reset_event_manager():
    EventManager._instance = None
    yield
    EventManager._instance = None


@pytest.mark.asyncio
async def test_event_registration_and_emission():
    received_data = []

    @event("test.event")
    async def trigger(data):
        return data

    @on("test.event")
    async def listener(data):
        received_data.append(data)

    await trigger("hello")

    assert len(received_data) == 1
    assert received_data[0] == "hello"


@pytest.mark.asyncio
async def test_multiple_listeners():
    count = 0

    @event("test.multi")
    async def trigger():
        return "trigger"

    @on("test.multi")
    async def listener_one(val):
        nonlocal count
        if val == "trigger":
            count += 1

    @on("test.multi")
    def listener_two(val):
        nonlocal count
        if val == "trigger":
            count += 1

    await trigger()

    assert count == 2


@pytest.mark.asyncio
async def test_sync_listener():
    result = []

    @event("test.sync")
    async def trigger(val):
        return val

    @on("test.sync")
    def listener(val):
        result.append(val)

    await trigger(42)
    assert result == [42]


@pytest.mark.asyncio
async def test_error_handling():
    # Should not crash
    @event("test.error")
    async def trigger():
        return "data"

    @on("test.error")
    async def bad_listener(data):
        raise ValueError("Oops")

    @on("test.error")
    async def good_listener(data):
        return "ok"

    await trigger()
    # If we reached here, exception was caught


@pytest.mark.asyncio
async def test_sync_listener_exception():
    # Should catch exception from threaded sync listener
    @event("test.sync_error")
    async def trigger():
        return "data"

    @on("test.sync_error")
    def bad_listener(data):
        raise ValueError("Sync Oops")

    await trigger()
    # Should not raise


@pytest.mark.asyncio
async def test_unbind():
    from artreactor.core.events import off

    received = []

    @event("test.unbind")
    async def trigger():
        return "ping"

    @on("test.unbind")
    def listener(val):
        received.append(val)

    # First trigger
    await trigger()
    assert len(received) == 1

    # Unbind
    off("test.unbind", listener)

    # Second trigger
    await trigger()
    assert len(received) == 1  # Should not increase


@pytest.mark.asyncio
async def test_fire_and_forget_async():
    completed = []

    @event("test.ff_async")
    async def trigger():
        return "go"

    @on("test.ff_async", fire_and_forget=True)
    async def slow_listener(val):
        await asyncio.sleep(0.1)
        completed.append(val)

    start = asyncio.get_running_loop().time()
    await trigger()
    end = asyncio.get_running_loop().time()

    # Should return immediately (much faster than 0.1s)
    assert end - start < 0.05
    assert len(completed) == 0

    # Wait for background task
    await asyncio.sleep(0.2)
    assert len(completed) == 1
    assert completed[0] == "go"


@pytest.mark.asyncio
async def test_fire_and_forget_sync():
    completed = []
    import time

    @event("test.ff_sync")
    async def trigger():
        return "go"

    @on("test.ff_sync", fire_and_forget=True)
    def slow_listener(val):
        time.sleep(0.1)
        completed.append(val)

    start = time.time()
    await trigger()
    end = time.time()

    # Should return immediately
    assert end - start < 0.05
    assert len(completed) == 0

    # Wait for thread
    await asyncio.sleep(0.2)
    assert len(completed) == 1
    assert completed[0] == "go"
