from fastapi import APIRouter
from artreactor.core.utils.tool_utils import convert_router_to_tools


def test_convert_router_simple():
    router = APIRouter()

    @router.get("/items/{item_id}")
    def read_item(item_id: int):
        """Read an item."""
        return {"item_id": item_id}

    tools = convert_router_to_tools(router, prefix="test")

    assert len(tools) == 1
    tool = tools[0]
    assert tool.name == "test_read_item"
    assert tool.description == "Read an item."
    assert "item_id" in tool.inputs
    assert tool.inputs["item_id"]["type"] == "integer"


def test_convert_router_multiple():
    router = APIRouter()

    @router.get("/a")
    def func_a():
        pass

    @router.post("/b")
    def func_b():
        pass

    tools = convert_router_to_tools(router)
    assert len(tools) == 2
    names = [t.name for t in tools]
    assert "func_a" in names
    assert "func_b" in names
