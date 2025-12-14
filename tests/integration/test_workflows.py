import os
import pytest
from artreactor.core.managers.project_manager import ProjectManager
from artreactor.core.managers.database_manager import (
    DatabaseManager,
    SqliteDatabaseProvider,
)
from artreactor.core.managers.agent_manager import AgentManager


@pytest.mark.asyncio
async def test_workflow_loading(tmp_path):
    # Setup database for project manager
    workflows_path = os.path.abspath("tests/resources/workflows")
    db_path = tmp_path / "test_db.db"
    db_provider = SqliteDatabaseProvider(str(db_path))
    db_manager = DatabaseManager(db_provider)
    pm = ProjectManager(db_manager, provider=None)

    # Create project in cache
    pm.create_project("Titan", workflows_path)
    am = AgentManager()

    # Load tools
    await am.load_project_tools("Titan", pm)

    # Verify tool is registered
    tool_names = [t.name for t in am.tools]
    assert "Titan_daily_build" in tool_names

    # Execute tool
    tool = next(t for t in am.tools if t.name == "Titan_daily_build")
    result = tool.func(target="win64")
    assert "Build started for win64" in result
