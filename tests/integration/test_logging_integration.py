import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from artreactor.api.middleware import RequestLoggingMiddleware
from artreactor.core.logging.manager import LogManager, LogEntry, LogProvider, LogLevel


class MockLogProvider(LogProvider):
    def __init__(self):
        self.logs = []

    async def log(self, entry: LogEntry):
        self.logs.append(entry)

    async def initialize(self):
        pass

    async def shutdown(self):
        pass


@pytest_asyncio.fixture
async def app_with_logging():
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    @app.get("/error")
    async def error_endpoint():
        raise ValueError("Oops")

    return app


@pytest_asyncio.fixture
async def log_manager_setup():
    manager = LogManager.get_instance()
    manager._providers = []
    # Add mock provider
    mock_provider = MockLogProvider()
    manager.register_provider(mock_provider)
    return manager, mock_provider


@pytest.mark.asyncio
async def test_middleware_logging(app_with_logging, log_manager_setup):
    manager, mock_provider = log_manager_setup

    client = TestClient(app_with_logging)

    # Success case
    response = client.get("/test")
    assert response.status_code == 200

    # Wait/Check logs
    # Middleware log calls are async and pushed to LogManager.
    # TestClient is synchronous but the app execution inside is managed.
    # However, LogManager.log waits for providers.
    # So logs should be populated.

    # We expect 2 logs: Request and Response
    logs = [entry for entry in mock_provider.logs if entry.source.startswith("api.")]
    assert len(logs) >= 2

    req_log = logs[0]
    assert "Request: GET /test" in req_log.message
    assert req_log.level == LogLevel.INFO

    res_log = logs[1]
    assert "Response: 200" in res_log.message
    assert res_log.context["status_code"] == 200

    # Headers check
    assert "X-Trace-ID" in response.headers
    trace_id = response.headers["X-Trace-ID"]
    assert req_log.trace_id == trace_id


@pytest.mark.asyncio
async def test_middleware_error_logging(app_with_logging, log_manager_setup):
    manager, mock_provider = log_manager_setup
    client = TestClient(app_with_logging)

    # Error case
    with pytest.raises(ValueError):
        client.get("/error")

    logs = [entry for entry in mock_provider.logs if entry.source == "api.error"]
    assert len(logs) == 1
    assert "Request Failed: Oops" in logs[0].message
    assert logs[0].level == LogLevel.ERROR
