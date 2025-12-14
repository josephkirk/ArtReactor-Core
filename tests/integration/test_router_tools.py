import pytest
from fastapi import APIRouter
from artreactor.core.utils.tool_utils import convert_router_to_tools
from artreactor.core.managers.agent_manager import AgentManager
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
async def test_router_tool_execution():
    # Setup Router
    router = APIRouter()

    @router.get("/echo/{message}")
    def echo(message: str) -> str:
        """Echoes the message."""
        return f"Echo: {message}"

    # Convert to Tools
    tools = convert_router_to_tools(router, prefix="api")

    # Setup Agent
    agent_manager = AgentManager()
    for tool_def in tools:
        await agent_manager.register_tool(tool_def)

    # Mock LLM for PydanticAI
    mock_responses = ["Echo: hello"]  # Simpler response format
    mock_model = MockPydanticModel(mock_responses)
    agent_manager.agent = Agent(mock_model)

    # Register tools using helper
    register_tools_with_agent(agent_manager)

    # Run Agent
    response = await agent_manager.run_agent("Echo hello")

    # Assert
    assert "Echo: hello" in str(response)
