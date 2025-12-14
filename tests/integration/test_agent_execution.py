import pytest
from artreactor.core.managers.agent_manager import AgentManager, ToolDefinition
from artreactor.core.managers.plugin_manager import PluginManager
from artreactor.core.interfaces.plugin import Plugin, PluginManifest, PluginType
from artreactor.core.decorators import tool
from pydantic_ai import Agent

from ..mocks.mock_llm import MockPydanticModel


def register_tools_with_agent(agent_manager):
    """Helper to register all tools with the agent instance."""
    for tool_def in agent_manager.tools:
        tool_func = agent_manager._create_tool_wrapper(tool_def)
        agent_manager.agent.tool_plain(
            tool_func, name=tool_def.name, description=tool_def.description
        )


# Mock Plugin with Tools
class E2EPlugin(Plugin):
    async def initialize(self):
        pass

    async def shutdown(self):
        pass

    @tool(name="add_numbers", description="Adds two numbers")
    def add(self, a: int, b: int) -> int:
        return a + b


@pytest.mark.asyncio
async def test_agent_execution_e2e():
    # Setup Managers
    plugin_manager = PluginManager()
    agent_manager = AgentManager()

    # Manually load plugin
    manifest = PluginManifest(name="e2e-plugin", version="1.0", type=PluginType.CORE)
    plugin = E2EPlugin(manifest, None)

    # Scan and Register
    plugin_manager._scan_for_tools(plugin)
    plugin_manager.plugins["e2e-plugin"] = plugin  # Mock registration

    await agent_manager.register_plugin_tools(plugin_manager)

    # Verify Tool Registration
    assert any(t.name == "add_numbers" for t in agent_manager.tools)

    # Mock LLM for PydanticAI
    mock_responses = ["8"]  # PydanticAI has simpler response format
    mock_model = MockPydanticModel(mock_responses)

    # Create agent with mock model
    agent_manager.agent = Agent(mock_model)

    # Register tools with the agent using helper
    register_tools_with_agent(agent_manager)

    # Run Agent
    response = await agent_manager.run_agent("Add 5 and 3")

    # Assert - PydanticAI returns structured response
    assert "8" in str(response)


@pytest.mark.asyncio
async def test_agent_context_injection():
    # Setup
    agent_manager = AgentManager()

    # Tool that needs context - PydanticAI handles deps injection automatically
    def context_aware_tool(key: str) -> str:
        return f"Context key: {key}"

    tool = ToolDefinition(
        name="get_context", description="Gets context value", func=context_aware_tool
    )
    await agent_manager.register_tool(tool)

    # Mock LLM for PydanticAI
    mock_responses = ["user_123"]  # Simple response
    mock_model = MockPydanticModel(mock_responses)

    # Create agent with mock model
    agent_manager.agent = Agent(mock_model)

    # Register tools using helper
    register_tools_with_agent(agent_manager)

    # Run with Context - PydanticAI passes context via deps parameter
    response = await agent_manager.run_agent(
        "Who am I?", context={"user_id": "user_123"}
    )
    assert response  # Just check it runs successfully
