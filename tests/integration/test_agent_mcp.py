from fastapi.testclient import TestClient
from artreactor.app import app
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


def test_agent_use_git_mcp_tool():
    # TestClient runs lifespan events automatically
    with TestClient(app) as client:
        # Create AgentManager
        agent_manager = AgentManager()

        # Wrap API call as a Tool
        def git_status(cwd: str = "."):
            response = client.get("/plugins/git/status", params={"cwd": cwd})
            if response.status_code == 200:
                return response.json()
            return f"Error: {response.status_code} {response.text}"

        tool = ToolDefinition(
            name="git_status",
            description="Checks git status. Args: cwd (str, optional)",
            func=git_status,
        )
        agent_manager.register_tool(tool)

        # Mock LLM for PydanticAI
        mock_responses = ["output"]  # Simpler response
        mock_model = MockPydanticModel(mock_responses)

        # Create agent with mock model
        agent_manager.agent = Agent(mock_model)

        # Register tools using helper
        register_tools_with_agent(agent_manager)

        # Run Agent - PydanticAI is async-first
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(agent_manager.run_agent("Check git status"))
        loop.close()

        # Verify Result
        print(f"Agent Response: {response}")
        assert "output" in str(response)
