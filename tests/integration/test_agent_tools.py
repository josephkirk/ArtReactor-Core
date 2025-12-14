import pytest
import sys
import os

sys.path.append(os.getcwd())
from fastapi import FastAPI
from unittest.mock import AsyncMock
from artreactor.core.managers.agent_manager import AgentManager, ToolDefinition
from pydantic_ai import Agent

from ..mocks.mock_llm import MockPydanticModel


def register_tools_with_agent(agent_manager):
    """Helper to register all tools with the agent instance."""
    for tool_def in agent_manager.tools:
        tool_func = agent_manager._create_tool_wrapper(tool_def)
        agent_manager.agent.tool_plain(
            tool_func, name=tool_def.name, description=tool_def.description
        )


@pytest.mark.asyncio
async def test_agent_use_subprocess_tool():
    # Setup App Context
    app = FastAPI()

    # Mock subprocess_launcher
    # We mock the 'run' method to return a known output
    mock_launcher = AsyncMock()
    mock_launcher.run.return_value = (0, "hello agent", "")
    app.state.subprocess_launcher = mock_launcher

    launcher = app.state.subprocess_launcher

    # Create AgentManager
    agent_manager = AgentManager()

    # Wrap subprocess_launcher.run as a Tool
    # PydanticAI natively supports async tools!
    async def run_command(command: str, cwd: str = None):
        return await launcher.run(command, cwd)

    tool = ToolDefinition(
        name="run_command",
        description="Runs a shell command. Args: command (str), cwd (str, optional)",
        func=run_command,
    )
    agent_manager.register_tool(tool)

    # Mock LLM for PydanticAI
    mock_responses = ["hello agent"]  # Simpler response
    mock_model = MockPydanticModel(mock_responses)

    # Create agent with mock model
    agent_manager.agent = Agent(mock_model)

    # Register tools using helper
    register_tools_with_agent(agent_manager)

    # Run Agent
    response = await agent_manager.run_agent("Run echo hello agent")

    # Verify Result
    print(f"Agent Response: {response}")
    assert "hello agent" in str(response)
