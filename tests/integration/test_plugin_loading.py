import pytest
from fastapi import FastAPI
from artreactor.core.managers.plugin_manager import PluginManager
from artreactor.core.managers.source_control import SourceControlManager
from artreactor.core.managers.project_manager import ProjectManager
from artreactor.core.managers.database_manager import (
    DatabaseManager,
    SqliteDatabaseProvider,
)
from artreactor.core.interfaces.plugin import PluginTiming


@pytest.mark.asyncio
async def test_plugin_load_order(tmp_path):
    # Setup App Context
    app = FastAPI()
    app.state.source_control = SourceControlManager()
    db_path = tmp_path / "test_db.db"
    db_provider = SqliteDatabaseProvider(str(db_path))
    db_manager = DatabaseManager(db_provider)
    app.state.project_manager = ProjectManager(db_manager, provider=None)

    # Create dummy plugins with different priorities/types/timing
    p1 = tmp_path / "p1-core"
    p1.mkdir()
    (p1 / "plugin.toml").write_text("""
name = "p1-core"
version = "0.1.0"
type = "ui"
description = "Core plugin"
timing = "pre-init"
""")

    p2 = tmp_path / "p2-router"
    p2.mkdir()
    (p2 / "plugin.toml").write_text("""
name = "p2-router"
version = "0.1.0"
type = "ui"
description = "Router plugin"
timing = "default"
""")

    p3 = tmp_path / "p3-app"
    p3.mkdir()
    (p3 / "plugin.toml").write_text("""
name = "p3-app"
version = "0.1.0"
type = "ui"
description = "App plugin"
timing = "default"
""")

    # Initialize PluginManager pointing to tmp_path
    plugin_manager = PluginManager(plugin_dirs=[str(tmp_path)], context=app)
    app.state.plugin_manager = plugin_manager

    # Load All Phases
    await plugin_manager.load_plugins(PluginTiming.PRE_INIT)
    await plugin_manager.load_plugins(PluginTiming.DEFAULT)
    await plugin_manager.load_plugins(PluginTiming.AFTER_INIT)

    load_order = plugin_manager._load_order
    print(f"Load Order: {load_order}")

    # Verify Order
    assert "p1-core" in load_order
    assert "p2-router" in load_order
    assert "p3-app" in load_order

    # Core (Pre-Init) should be before others (Default)
    assert load_order.index("p1-core") < load_order.index("p2-router")
    assert load_order.index("p1-core") < load_order.index("p3-app")
