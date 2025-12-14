# Tools and Decorators

## The @tool Decorator

See [Architecture - Plugin System](../architecture/plugin-system.md#tool-decorator) for complete documentation.

## Advanced Patterns

- Async tools
- Error handling
- Type validation
- Parameter defaults

## Examples

```python
from artreactor.core.decorators import tool

@tool(name="my_tool", description="Does something")
async def my_tool(self, param: str) -> dict:
    return {"result": param}
```
