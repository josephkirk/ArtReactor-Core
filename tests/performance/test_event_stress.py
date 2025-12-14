import pytest
import time
from artreactor.core.events import EventManager, event, on


@pytest.fixture(autouse=True)
def reset_event_manager():
    EventManager._instance = None
    yield
    EventManager._instance = None
    # Ensure emit_logging is reset for next test
    if EventManager._instance:
        EventManager._instance.emit_logging = False


@pytest.mark.asyncio
async def test_stress_many_listeners_async():
    """
    Test 1 event with 1000 async listeners.
    """
    LISTENER_COUNT = 1000

    @event("stress.many_listeners")
    async def trigger():
        return "fire"

    counter = 0

    async def listener(val):
        nonlocal counter
        counter += 1

    # Register many listeners
    for _ in range(LISTENER_COUNT):
        on("stress.many_listeners")(listener)

    start_time = time.time()
    await trigger()
    end_time = time.time()

    duration = end_time - start_time
    print(f"\n[Async] 1 Trigger -> {LISTENER_COUNT} Listeners took {duration:.4f}s")

    assert counter == LISTENER_COUNT
    # Just a sanity check that it's reasonably fast (e.g., < 1s for 1000 simple async listeners)
    assert duration < 2.0


@pytest.mark.asyncio
async def test_stress_many_emits_async():
    """
    Test emit 1000 times with 1 async listener.
    """
    EMIT_COUNT = 1000

    @event("stress.many_emits")
    async def trigger():
        return "fire"

    counter = 0

    @on("stress.many_emits")
    async def listener(val):
        nonlocal counter
        counter += 1

    start_time = time.time()
    for _ in range(EMIT_COUNT):
        await trigger()
    end_time = time.time()

    duration = end_time - start_time
    print(f"\n[Async] {EMIT_COUNT} Triggers -> 1 Listener took {duration:.4f}s")

    assert counter == EMIT_COUNT
    assert duration < 2.0


@pytest.mark.asyncio
async def test_stress_sync_threaded_overhead():
    """
    Test overhead of running 1000 sync listeners (which will spin up tasks/threads).
    """
    LISTENER_COUNT = 100

    @event("stress.sync")
    async def trigger():
        return "fire"

    counter = 0

    def listener(val):
        nonlocal counter
        counter += 1

    # Register listeners
    for _ in range(LISTENER_COUNT):
        on("stress.sync")(listener)

    start_time = time.time()
    await trigger()
    end_time = time.time()

    duration = end_time - start_time
    print(
        f"\n[Sync/Threaded] 1 Trigger -> {LISTENER_COUNT} Listeners took {duration:.4f}s"
    )

    assert counter == LISTENER_COUNT
    # Thread overhead is higher, so be lenient
    assert duration < 2.0


@pytest.mark.asyncio
async def test_extreme_scale():
    """
    Extreme Scale Test:
    - Register 1,000,000 listeners (simulated by creating unique event names to avoid huge list overhead on single event).
    - Emit 100,000 events.
    """
    # Ensure emit_logging is disabled for performance
    EventManager().emit_logging = False

    TOTAL_LISTENERS = 1_000_000
    TOTAL_EMITS = 100_000

    # To simulate 1M bindings efficiently without creating 1M function objects (which would test Python memory more than our system),
    # we can use a smaller number of listener functions reused across many event names.
    # But to test the EventManager's dictionary lookup speed, we need 1M unique keys.

    # 1. Register 1M events
    # We will register 1 listener for each of 1,000,000 unique event names.
    print(f"\n[Extreme] Registering {TOTAL_LISTENERS} listeners...")
    start_time = time.time()

    async def common_listener(val):
        pass

    # Batch registration to avoid huge loop overhead in test logic itself?
    # Just loop. Python loop for 1M is fast enough (~0.1s).
    for i in range(TOTAL_LISTENERS):
        event_name = f"extreme.{i}"
        # We access the internal dict directly for setup speed if needed, but using public API is more realistic.
        # But `on` decorator overhead might be slow for 1M calls in a test.
        # Let's use `on` directly.
        # event_manager.on(event_name, common_listener)
        # Using the direct method call is faster than the decorator wrapper logic which calls decorators.on -> manager.on
        # Wait, decorators.on is:
        # def on(name):
        #     def decorator(func):
        #         event_manager.on(name, func)
        #         return func
        #     return decorator

        # We should call event_manager.on directly.
        EventManager().on(event_name, common_listener)

    reg_duration = time.time() - start_time
    print(f"[Extreme] Registration took {reg_duration:.4f}s")

    # Pre-compute event names to isolate emit performance from string formatting
    event_names = [f"extreme.{i}" for i in range(TOTAL_EMITS)]

    # 2. Emit 100k events
    print(f"[Extreme] Emitting {TOTAL_EMITS} events...")
    start_time = time.time()

    # Cache instance to avoid singleton lookup overhead per emit
    manager = EventManager()
    for event_name in event_names:
        await manager.emit(event_name, "fire")

    emit_duration = time.time() - start_time
    print(f"[Extreme] Emission took {emit_duration:.4f}s")

    assert (
        emit_duration < 10.0
    )  # Benchmark: should be reasonably fast, around 6s for high-end system, 10s for low-end system or docker container
