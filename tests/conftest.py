"""Pytest configuration for test ordering and shared fixtures."""


def pytest_collection_modifyitems(items):
    """Reorder tests to run performance tests first.

    Performance tests are sensitive to system state and run most accurately
    when executed before other tests that may pollute memory or async state.
    """
    performance_tests = []
    other_tests = []

    for item in items:
        if "performance" in str(item.fspath):
            performance_tests.append(item)
        else:
            other_tests.append(item)

    # Reorder: performance tests first, then others
    items[:] = performance_tests + other_tests
