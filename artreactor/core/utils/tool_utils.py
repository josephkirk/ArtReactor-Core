from typing import List, Callable
from fastapi import APIRouter

from artreactor.core.managers.agent_manager import ToolDefinition
from pydantic_ai import Agent
import inspect


def convert_router_to_tools(
    router: APIRouter, prefix: str = ""
) -> List[ToolDefinition]:
    """
    Convert FastAPI router endpoints into PydanticAI tool definitions.

    PydanticAI advantages:
    - Better async handling (native support)
    - Type-safe parameter extraction
    - Automatic Pydantic model validation

    Args:
        router: The APIRouter instance
        prefix: Optional prefix for tool names

    Returns:
        List of ToolDefinition objects for PydanticAI
    """
    tools = []

    for route in router.routes:
        # Only handle APIRoute objects
        if not hasattr(route, "endpoint"):
            continue

        endpoint = route.endpoint

        # Determine tool name
        func_name = endpoint.__name__
        tool_name = f"{prefix}_{func_name}" if prefix else func_name

        # Determine description
        description = inspect.getdoc(endpoint) or f"Call endpoint {route.path}"

        # Extract parameters from function signature
        sig = inspect.signature(endpoint)
        inputs = {}
        for param_name, param in sig.parameters.items():
            if param_name in ["request", "response"]:  # Skip FastAPI special params
                continue
            param_type = (
                param.annotation if param.annotation != inspect.Parameter.empty else str
            )
            # Map Python types to JSON schema types
            type_name = (
                param_type.__name__
                if hasattr(param_type, "__name__")
                else str(param_type)
            )
            if type_name == "int":
                type_name = "integer"
            inputs[param_name] = {
                "type": type_name,
                "required": param.default == inspect.Parameter.empty,
            }

        # Create ToolDefinition object
        tool_def = ToolDefinition(
            name=tool_name,
            description=description,
            func=endpoint,
            parameters=inputs if inputs else None,
        )

        tools.append(tool_def)

    return tools


def create_tool_from_function(
    func: Callable, name: str = None, description: str = None
) -> dict:
    """
    Create a PydanticAI tool definition from a function.

    PydanticAI advantages:
    - Automatic parameter inference from type hints
    - Native async support
    - Pydantic validation of inputs/outputs

    Args:
        func: The function to wrap as a tool
        name: Optional name (defaults to function name)
        description: Optional description (defaults to docstring)

    Returns:
        Tool definition dict
    """
    tool_name = name or func.__name__
    tool_description = description or inspect.getdoc(func) or f"Execute {tool_name}"

    return {
        "name": tool_name,
        "description": tool_description,
        "func": func,
    }


def register_tools_with_agent(agent: Agent, tools: List[dict]):
    """
    Register multiple tools with a PydanticAI agent.

    PydanticAI advantages:
    - Programmatic tool registration
    - Type-safe tool definitions
    - Better error handling

    Args:
        agent: PydanticAI Agent instance
        tools: List of tool definition dicts
    """
    for tool_def in tools:
        func = tool_def["func"]
        name = tool_def["name"]
        description = tool_def["description"]

        # Register tool with agent using tool_plain for programmatic registration
        # PydanticAI automatically handles async functions
        agent.tool_plain(func, name=name, description=description)
