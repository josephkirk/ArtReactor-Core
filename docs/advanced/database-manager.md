# Database Manager

The Database Manager provides a simple key-value storage interface for plugins and systems to store and query JSON-like data. It supports multiple database providers and offers a clean REST API.

## Features

- **Simple Interface**: Store, retrieve, and remove data with straightforward methods
- **Collections**: Organize data into named collections (similar to tables)
- **JSON Storage**: Store any JSON-serializable Python dictionary
- **Multiple Providers**: Pluggable provider architecture (SQLite by default)
- **REST API**: Access database operations via HTTP endpoints
- **Plugin Access**: Easy access from plugins via app context

## Architecture

The Database Manager follows the established provider pattern used in artreactor Core:

```
DatabaseManager (Interface)
    ↓
DatabaseProvider (Abstract Base)
    ↓
SqliteDatabaseProvider (Default Implementation)
```

### Provider Interface

```python
class DatabaseProvider(ABC):
    def set(self, collection: str, key: str, data: Dict[str, Any]) -> None
    def get(self, collection: str, key: str) -> Optional[Dict[str, Any]]
    def remove(self, collection: str, key: str) -> bool
    def list_keys(self, collection: str) -> List[str]
    def list_collections(self) -> List[str]
```

## Usage

### From Python Code

```python
from artreactor.core.managers.database_manager import DatabaseManager, SqliteDatabaseProvider

# Create a database manager
provider = SqliteDatabaseProvider(".artreactor/database.db")
db = DatabaseManager(provider)

# Store data
db.set("assets", "character_001", {
    "name": "Hero Character",
    "type": "3d_model",
    "status": "approved",
    "metadata": {
        "author": "Artist Name",
        "polycount": 50000
    }
})

# Retrieve data
asset = db.get("assets", "character_001")
print(asset["name"])  # "Hero Character"

# Update data
asset["status"] = "exported"
db.set("assets", "character_001", asset)

# Remove data
db.remove("assets", "character_001")

# List all keys in a collection
asset_keys = db.list_keys("assets")

# List all collections
all_collections = db.list_collections()
```

### From Plugins

Plugins can access the database manager through the app context:

```python
from artreactor.core.interfaces.plugin import CorePlugin

class MyPlugin(CorePlugin):
    async def initialize(self):
        # Access database manager from app state
        db = self.context.state.database_manager
        
        # Store plugin configuration
        db.set("plugin_config", self.manifest.name, {
            "enabled": True,
            "settings": {"option1": "value1"}
        })
    
    async def some_operation(self):
        db = self.context.state.database_manager
        
        # Retrieve data
        config = db.get("plugin_config", self.manifest.name)
        
        # Store results
        db.set("plugin_results", "operation_1", {
            "timestamp": "2024-01-01T12:00:00",
            "status": "success",
            "data": {"processed": 100}
        })
```

### Via REST API

#### Set Data

```bash
POST /database/set
Content-Type: application/json

{
    "collection": "assets",
    "key": "asset_001",
    "data": {
        "name": "Character Model",
        "type": "3d",
        "version": 1
    }
}

# Response
{
    "status": "success",
    "collection": "assets",
    "key": "asset_001"
}
```

#### Get Data

```bash
POST /database/get
Content-Type: application/json

{
    "collection": "assets",
    "key": "asset_001"
}

# Response
{
    "collection": "assets",
    "key": "asset_001",
    "data": {
        "name": "Character Model",
        "type": "3d",
        "version": 1
    }
}
```

#### Remove Data

```bash
POST /database/remove
Content-Type: application/json

{
    "collection": "assets",
    "key": "asset_001"
}

# Response
{
    "status": "success",
    "collection": "assets",
    "key": "asset_001",
    "removed": true
}
```

#### List Keys

```bash
POST /database/list-keys
Content-Type: application/json

{
    "collection": "assets"
}

# Response
{
    "collection": "assets",
    "keys": ["asset_001", "asset_002", "asset_003"]
}
```

#### List Collections

```bash
GET /database/collections

# Response
{
    "collections": ["assets", "projects", "metadata"]
}
```

## Use Cases

### Asset Pipeline Tracking

```python
# Store asset processing status
db.set("asset_pipeline", "char_hero_001", {
    "stages": {
        "modeling": {"status": "complete", "timestamp": "2024-01-01T10:00:00"},
        "texturing": {"status": "in_progress", "artist": "John"},
        "rigging": {"status": "pending"}
    },
    "current_stage": "texturing",
    "priority": "high"
})

# Query status
asset_status = db.get("asset_pipeline", "char_hero_001")
if asset_status["current_stage"] == "texturing":
    # Do something
    pass
```

### Plugin State Management

```python
# Store plugin state across sessions
db.set("plugin_state", "my-exporter", {
    "last_export_path": "C:/Projects/Export",
    "export_count": 42,
    "preferences": {
        "auto_export": True,
        "format": "fbx"
    }
})

# Restore state on next load
state = db.get("plugin_state", "my-exporter")
```

### Workflow Coordination

```python
# Store workflow checkpoints
db.set("workflows", "project_build_001", {
    "step": 3,
    "steps_completed": ["fetch_assets", "validate", "compile"],
    "steps_remaining": ["package", "deploy"],
    "data": {
        "assets_processed": 150,
        "errors": []
    }
})

# Other systems can query workflow state
workflow = db.get("workflows", "project_build_001")
next_step = workflow["steps_remaining"][0]
```

### Cache Management

```python
# Cache expensive computations
db.set("cache", "scene_analysis_scene_001", {
    "computed_at": "2024-01-01T12:00:00",
    "polycount": 1500000,
    "material_count": 45,
    "texture_memory": "2.5GB",
    "ttl": 3600  # Time to live in seconds
})

# Check cache
cached = db.get("cache", "scene_analysis_scene_001")
if cached and not is_expired(cached["computed_at"], cached["ttl"]):
    # Use cached data
    pass
```

## Implementation Details

### SQLite Provider

The default `SqliteDatabaseProvider` uses SQLite for storage:

- **Database Location**: `.artreactor/database.db` (configurable)
- **Schema**: Simple table with `collection`, `key`, and `data` columns
- **JSON Serialization**: Data is serialized using Python's `json` module
- **Thread Safety**: SQLite provides thread-safe operations
- **Persistence**: Data persists across application restarts

### Creating Custom Providers

You can create custom providers for different backends (MongoDB, Redis, etc.):

```python
from artreactor.core.managers.database_manager import DatabaseProvider

class MongoDBProvider(DatabaseProvider):
    def __init__(self, connection_string: str):
        self.client = MongoClient(connection_string)
        self.db = self.client.artreactor
    
    def set(self, collection: str, key: str, data: Dict[str, Any]) -> None:
        self.db[collection].update_one(
            {"_id": key},
            {"$set": data},
            upsert=True
        )
    
    def get(self, collection: str, key: str) -> Optional[Dict[str, Any]]:
        doc = self.db[collection].find_one({"_id": key})
        if doc:
            doc.pop("_id")
            return doc
        return None
    
    # Implement other methods...

# Use custom provider
from artreactor.core.managers.database_manager import DatabaseManager
db = DatabaseManager(MongoDBProvider("mongodb://localhost:27017/"))
```

## Best Practices

1. **Use Meaningful Collections**: Organize data into logical collections like "assets", "projects", "cache"
2. **Consistent Key Naming**: Use consistent naming conventions for keys (e.g., "asset_001", "project_main")
3. **Version Your Data**: Include version fields in your data structures for future compatibility
4. **Avoid Large Objects**: Keep stored data reasonably sized; use references for large files
5. **Clean Up**: Remove obsolete data using the `remove()` method
6. **Error Handling**: Always check if `get()` returns `None` before using the data

## Security Considerations

- The database is stored locally in `.artreactor/database.db`
- File permissions control access to the database file
- No authentication is built into the database manager itself
- Consider implementing access control at the API level if needed
- Sensitive data should be encrypted before storage

## Performance

- SQLite is efficient for local storage and moderate data volumes
- Queries are fast due to primary key indexing on (collection, key)
- For high-volume or distributed scenarios, consider implementing a custom provider (Redis, MongoDB, etc.)

## Testing

The Database Manager includes comprehensive tests:

- **Unit Tests**: `tests/unit/test_database_manager.py`
- **Integration Tests**: `tests/integration/test_database_api.py`

Run tests with:

```bash
pytest tests/unit/test_database_manager.py -v
pytest tests/integration/test_database_api.py -v
```

## Future Enhancements

Potential improvements for future versions:

- Query support (filter, search)
- Transactions
- Batch operations
- Data migration utilities
- Time-to-live (TTL) support
- Data encryption
- Backup/restore functionality
- Replication support
