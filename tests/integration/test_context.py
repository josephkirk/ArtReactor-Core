from artreactor.core.managers.agent_manager import AgentManager, ToolDefinition
import pytest


def mock_tool_func(context: dict = None):
    if context:
        return f"Context: {context.get('project')}"
    return "No Context"


@pytest.mark.asyncio
async def test_context_injection():
    am = AgentManager()
    tool = ToolDefinition(
        name="test_tool", description="A test tool", func=mock_tool_func
    )
    await am.register_tool(tool)

    # Test that the tool was registered
    assert len(am.tools) == 1
    assert am.tools[0].name == "test_tool"

    # Test tool execution with context
    result = mock_tool_func({"project": "Titan"})
    assert "Titan" in result
