# Database Manager

For detailed information, see [database_manager.md](../database_manager.md) in the docs root.

## Quick Start

```python
from artreactor.core.managers.database_manager import DatabaseManager

db = context["database_manager"]
await db.save("collection", "key", {"data": "value"})
record = await db.get("collection", "key")
```

See the full documentation for advanced usage.
