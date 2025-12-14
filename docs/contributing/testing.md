# Testing

## Running Tests

```bash
uv run pytest
```

## Test Structure

- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests
- `tests/mocks/` - Mock implementations

## Writing Tests

```python
import pytest
from mymodule import myfunction

@pytest.mark.asyncio
async def test_async_function():
    result = await myfunction()
    assert result == expected
```

## Coverage

```bash
uv run pytest --cov=artreactor
```
