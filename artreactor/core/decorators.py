from typing import Callable, Optional


class ToolDefinition:
    """
    Metadata for a tool discovered via decorator.
    """

    def __init__(self, func: Callable, name: str, description: str):
        self.func = func
        self.name = name
        self.description = description


def tool(name: Optional[str] = None, description: Optional[str] = None):
    """
    Decorator to mark a function as an agent tool.

    Args:
        name: Optional custom name for the tool. Defaults to function name.
        description: Optional custom description. Defaults to docstring.
    """

    def decorator(func: Callable) -> Callable:
        # Attach metadata to the function itself
        # This allows us to inspect it later without wrapping it in a class yet
        setattr(func, "_is_tool", True)
        setattr(func, "_tool_name", name)
        setattr(func, "_tool_description", description)
        return func

    return decorator
