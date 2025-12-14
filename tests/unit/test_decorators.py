from artreactor.core.decorators import tool


def test_tool_decorator_metadata():
    @tool(name="custom_tool", description="A custom description")
    def my_func(x: int):
        """Original docstring"""
        return x

    assert getattr(my_func, "_is_tool") is True
    assert getattr(my_func, "_tool_name") == "custom_tool"
    assert getattr(my_func, "_tool_description") == "A custom description"


def test_tool_decorator_defaults():
    @tool()
    def my_func(x: int):
        """Original docstring"""
        return x

    assert getattr(my_func, "_is_tool") is True
    assert getattr(my_func, "_tool_name") is None
    assert getattr(my_func, "_tool_description") is None
