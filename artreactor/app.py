from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from artreactor.api.middleware import RequestLoggingMiddleware
from artreactor.api.routers import agent, plugins, projects, secrets, database
from artreactor.api.dependencies import get_database_manager
from artreactor.core.logging.manager import LogManager
from artreactor.core.logging.providers.console import ConsoleLogProvider
from artreactor.core.telemetry.manager import TelemetryManager
from artreactor.core.telemetry.collector import TelemetryCollector
from artreactor.core.managers.plugin_manager import PluginManager
from artreactor.core.managers.skill_manager import SkillManager
from artreactor.core.managers.source_control import SourceControlManager
from artreactor.models.plugin import PluginTiming, PluginType


@asynccontextmanager
async def lifespan(app: FastAPI):
    import time

    startup_start_time = time.perf_counter()

    # Initialize Logging
    log_manager = LogManager.get_instance()
    # Ensure at least console provider is active
    log_manager.register_provider(ConsoleLogProvider())

    # Initialize Telemetry BEFORE subscribing collector to ensure providers exist
    # This prevents silently losing telemetry data during early application startup
    telemetry_manager = TelemetryManager.get_instance()
    await telemetry_manager.initialize()

    # Wire up TelemetryCollector to subscribe to log events BEFORE log initialization
    # This ensures all logs (including from plugin loading) generate telemetry
    telemetry_collector = TelemetryCollector.get_instance()
    log_manager.subscribe(telemetry_collector.on_log_entry)

    await log_manager.initialize()

    # Initialize Managers
    import os

    app.state.source_control = SourceControlManager()
    app.state.skill_manager = SkillManager()
    # Use the shared database manager from dependencies
    app.state.database_manager = get_database_manager()
    config_path = os.environ.get("ARTE_CONFIG_PATH")
    app.state.plugin_manager = PluginManager(
        context=app, config_path=config_path, skill_manager=app.state.skill_manager
    )

    # Load Plugins
    await app.state.plugin_manager.load_plugins(PluginTiming.PRE_INIT)
    await app.state.plugin_manager.load_plugins(PluginTiming.DEFAULT)
    await app.state.plugin_manager.load_plugins(PluginTiming.AFTER_INIT)

    # Register Router Plugins
    router_plugins = app.state.plugin_manager.get_plugins_by_type(PluginType.ROUTER)
    for plugin in router_plugins:
        router = plugin.get_router()
        if router:
            app.include_router(router, prefix="/plugins")

    # Register Logging Plugins
    logging_plugins = app.state.plugin_manager.get_logging_plugins()
    for plugin in logging_plugins:
        provider = plugin.get_provider()
        if provider:
            log_manager.register_provider(provider)
            # Initialize the new provider immediately if manager is already init
            await provider.initialize()

    # Register Telemetry Plugins
    telemetry_plugins = app.state.plugin_manager.get_telemetry_plugins()
    for plugin in telemetry_plugins:
        provider = plugin.get_provider()
        if provider:
            telemetry_manager.register_provider(provider)
            # Initialize the new provider immediately if manager is already init
            await provider.initialize()

    # Mount StaticFiles last to avoid shadowing
    import os

    dashboard_dir = "src/artreactor/ui/dashboard"
    if os.path.exists(dashboard_dir):
        app.mount(
            "/", StaticFiles(directory=dashboard_dir, html=True), name="dashboard"
        )

    # Record application startup time
    startup_duration = time.perf_counter() - startup_start_time
    await telemetry_manager.record_timer(
        name="app.startup.duration",
        duration=startup_duration,
        tags={"status": "success"},
    )
    await log_manager.info(
        f"Application startup completed in {startup_duration:.3f}s",
        source="app.lifecycle",
        startup_time=startup_duration,
    )

    yield

    # Record application shutdown
    shutdown_start_time = time.perf_counter()
    await app.state.plugin_manager.shutdown_all()
    await telemetry_manager.shutdown()
    shutdown_duration = time.perf_counter() - shutdown_start_time
    await telemetry_manager.record_timer(
        name="app.shutdown.duration",
        duration=shutdown_duration,
        tags={"status": "success"},
    )
    await log_manager.shutdown()


app = FastAPI(title="ArteCore API Central Hub", version="0.1.0", lifespan=lifespan)

# Add Middleware
# Add Middleware
# Add Middleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # For dev/sidecar safety, or restrict to ["http://localhost:1420", "tauri://localhost"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


app.include_router(plugins.router)
app.include_router(agent.router)
app.include_router(projects.router)
app.include_router(secrets.router)
app.include_router(database.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
