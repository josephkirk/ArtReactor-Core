# Getting Started with Plugin Development

This guide will walk you through creating your first ArtReactor plugin from scratch.

## Prerequisites

Before you begin:

- ArtReactor Core installed ([Installation Guide](../getting-started/installation.md))
- Python 3.10+ knowledge
- Understanding of async/await (helpful but not required)
- Familiarity with the [Architecture](../architecture/overview.md) (recommended)

## Your First Plugin: "Hello World"

Let's create a simple plugin that adds a greeting tool.

### Step 1: Create Plugin Structure

Use the CLI to scaffold your plugin:

```bash
arte plugin create hello-world --type core
```

This creates:

```
plugins/hello-world/
├── plugin.toml      # Plugin metadata and configuration
├── __init__.py      # Plugin implementation
└── SKILL.md         # Agent skill documentation (optional)
```

### Step 2: Understanding the Manifest

Open `plugins/hello-world/plugin.toml`:

```toml
name = "hello-world"
version = "1.0.0"
type = "core"
description = "A simple hello world plugin"
dependencies = []

[timing]
phase = "default"
priority = 50
```

**Key Fields**:
- `name`: Unique identifier (use kebab-case)
- `version`: Semantic versioning (major.minor.patch)
- `type`: Plugin type (core, router, app, agent, model, ui)
- `timing.phase`: When to load (pre-init, default, post-init)
- `timing.priority`: Load order (higher = earlier)

### Step 3: Implement the Plugin

Open `plugins/hello-world/__init__.py`:

```python
from artreactor.core.interfaces.plugin import CorePlugin, PluginManifest
from artreactor.core.decorators import tool
from typing import Any
import logging

logger = logging.getLogger(__name__)


class HelloWorldPlugin(CorePlugin):
    """A simple plugin that provides greeting functionality."""
    
    def __init__(self, manifest: PluginManifest, context: Any):
        super().__init__(manifest, context)
        self.greeting_count = 0

    async def initialize(self):
        """Called when the plugin is loaded."""
        logger.info("Hello World plugin initialized!")
        
    async def shutdown(self):
        """Called when the plugin is unloaded."""
        logger.info(f"Hello World plugin shutting down. "
                   f"Total greetings: {self.greeting_count}")

    @tool(
        name="greet",
        description="Greets a person by name with a friendly message"
    )
    def greet(self, name: str, enthusiastic: bool = False) -> str:
        """
        Returns a personalized greeting.
        
        Args:
            name: The name of the person to greet
            enthusiastic: If True, adds extra enthusiasm to the greeting
            
        Returns:
            A greeting message
        """
        self.greeting_count += 1
        
        if enthusiastic:
            return f"Hello, {name}!!! 🎉 Welcome to ArtReactor! This is amazing!"
        else:
            return f"Hello, {name}! Welcome to ArtReactor."
```

### Step 4: Start the Service

Run ArtReactor to load your plugin:

```bash
arte start
```

Look for these log messages:

```
INFO: Discovered plugin: hello-world (v1.0.0)
INFO: Loading plugin: hello-world
INFO: Hello World plugin initialized!
INFO: Registered tool: greet
```

### Step 5: Test Your Plugin

#### Via Python

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/api/agent/run",
    json={
        "prompt": "Please greet Alice enthusiastically using the greet tool"
    }
)

print(response.json())
```

#### Via cURL

```bash
curl -X POST http://127.0.0.1:8000/api/agent/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Greet Bob using the greet tool"}'
```

## Understanding the Components

### Plugin Class

Every plugin must:

1. **Inherit from a plugin base class**:
   - `CorePlugin` - General purpose
   - `RouterPlugin` - Adds API endpoints
   - `AppPlugin` - Controls external apps
   - `AgentPlugin` - Defines custom agents
   - `ModelPlugin` - Provides AI models
   - `UiPlugin` - Serves web interfaces

2. **Implement lifecycle methods**:
   ```python
   async def initialize(self):
       """Setup: load config, create connections, register listeners"""
       pass
   
   async def shutdown(self):
       """Cleanup: close connections, save state, unregister"""
       pass
   ```

### Tool Decorator

The `@tool` decorator makes methods available to AI agents:

```python
from artreactor.core.decorators import tool

@tool(
    name="tool_name",           # Required: Unique tool name
    description="What it does"  # Required: For agent understanding
)
def my_tool(self, param: str) -> str:
    """
    Docstring explaining parameters and return value.
    This helps both developers and AI agents.
    """
    return f"Result: {param}"
```

**Key Points**:
- Must be a method of your plugin class
- Use type hints (required for validation)
- Provide clear descriptions
- Can be `async` if needed

### Context Object

Your plugin receives a context dict with access to managers:

```python
async def initialize(self):
    # Available in self.context:
    agent_manager = self.context["agent_manager"]
    plugin_manager = self.context["plugin_manager"]
    event_manager = self.context["event_manager"]
    config = self.context["config"]
    logger = self.context["logger"]
```

## Adding Complexity

### Configuration

Read plugin-specific config:

```python
async def initialize(self):
    config = self.context.get("config", {})
    plugin_config = config.get("plugins", {}).get("hello-world", {})
    settings = plugin_config.get("settings", {})
    
    self.max_length = settings.get("max_name_length", 50)
    self.default_greeting = settings.get("default_greeting", "Hello")
```

In `config.toml`:

```toml
[plugins.hello-world.settings]
max_name_length = 100
default_greeting = "Greetings"
```

### Multiple Tools

Add as many tools as needed:

```python
class HelloWorldPlugin(CorePlugin):
    @tool(name="greet")
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"
    
    @tool(name="farewell")
    def farewell(self, name: str) -> str:
        return f"Goodbye, {name}!"
    
    @tool(name="introduce")
    def introduce(self, name: str, role: str) -> str:
        return f"This is {name}, our {role}."
```

### Async Tools

For I/O operations, use async:

```python
import aiofiles

@tool(name="save_greeting")
async def save_greeting(self, name: str, filename: str) -> dict:
    """Save a greeting to a file."""
    try:
        greeting = f"Hello, {name}!"
        async with aiofiles.open(filename, 'w') as f:
            await f.write(greeting)
        return {"status": "success", "file": filename}
    except Exception as e:
        logger.error(f"Failed to save: {e}")
        return {"status": "error", "message": str(e)}
```

### Using Events

Communicate with other plugins via events:

```python
from artreactor.core.events import fire, on

class HelloWorldPlugin(CorePlugin):
    async def initialize(self):
        # Listen for events
        on("user.joined", self.on_user_joined)
    
    async def on_user_joined(self, data: dict):
        """Handle user joined event."""
        name = data.get("name")
        logger.info(f"New user joined: {name}")
        # Maybe send them a greeting
    
    @tool(name="announce_greeting")
    def announce_greeting(self, name: str) -> str:
        """Greet someone and announce it."""
        greeting = f"Hello, {name}!"
        
        # Fire event for other plugins
        fire("greeting.sent", {
            "name": name,
            "message": greeting,
            "timestamp": datetime.now().isoformat()
        })
        
        return greeting
```

### Error Handling

Always handle errors gracefully:

```python
@tool(name="safe_greet")
def safe_greet(self, name: str) -> dict:
    """Greet with error handling."""
    try:
        if not name or len(name) > 100:
            return {
                "status": "error",
                "message": "Name must be 1-100 characters"
            }
        
        greeting = f"Hello, {name}!"
        self.greeting_count += 1
        
        return {
            "status": "success",
            "message": greeting,
            "count": self.greeting_count
        }
        
    except Exception as e:
        logger.error(f"Error in safe_greet: {e}", exc_info=True)
        return {
            "status": "error",
            "message": "An internal error occurred"
        }
```

## Testing Your Plugin

Create `tests/test_hello_world.py`:

```python
import pytest
from plugins.hello_world import HelloWorldPlugin
from artreactor.models.plugin import PluginManifest
import logging

@pytest.fixture
def plugin():
    """Create a plugin instance for testing."""
    manifest = PluginManifest(
        name="hello-world",
        version="1.0.0",
        type="core",
        description="Test plugin"
    )
    context = {
        "config": {},
        "logger": logging.getLogger("test")
    }
    return HelloWorldPlugin(manifest, context)

@pytest.mark.asyncio
async def test_plugin_initialization(plugin):
    """Test plugin initializes correctly."""
    await plugin.initialize()
    assert plugin.greeting_count == 0

def test_greet_basic(plugin):
    """Test basic greeting."""
    result = plugin.greet("Alice", enthusiastic=False)
    assert "Alice" in result
    assert plugin.greeting_count == 1

def test_greet_enthusiastic(plugin):
    """Test enthusiastic greeting."""
    result = plugin.greet("Bob", enthusiastic=True)
    assert "Bob" in result
    assert "!" in result
    assert plugin.greeting_count == 1

@pytest.mark.asyncio
async def test_plugin_shutdown(plugin):
    """Test plugin shuts down cleanly."""
    await plugin.initialize()
    plugin.greet("Test")
    await plugin.shutdown()
    assert plugin.greeting_count == 1
```

Run tests:

```bash
uv run pytest tests/test_hello_world.py
```

## Debugging

### Enable Debug Logging

In `config.toml`:

```toml
[logging]
level = "DEBUG"
```

### Add Debug Logs

```python
async def initialize(self):
    logger.debug("Starting initialization")
    logger.debug(f"Config: {self.context.get('config')}")
    logger.info("Initialization complete")
```

### Check Plugin Loading

```bash
arte start --reload
```

Look for:
- "Discovered plugin: hello-world"
- "Loading plugin: hello-world"
- "Hello World plugin initialized!"
- "Registered tool: greet"

## Common Issues

### Plugin Not Loading

**Symptom**: No logs about your plugin

**Solutions**:
1. Check `plugin.toml` syntax
2. Verify plugin directory is in plugin path
3. Check Python syntax errors
4. Ensure class inherits from correct base

### Tool Not Registered

**Symptom**: Plugin loads but tool unavailable

**Solutions**:
1. Verify `@tool` decorator is used
2. Check method isn't private (`_method`)
3. Ensure method has type hints
4. Check `initialize()` completed successfully

### Import Errors

**Symptom**: `ModuleNotFoundError`

**Solutions**:
1. Install dependencies: `uv sync`
2. Check imports use correct paths
3. Verify `__init__.py` exists

## Next Steps

Now that you've created your first plugin:

1. [Plugin Types](plugin-types.md) - Learn about different plugin types
2. [Tools and Decorators](tools-and-decorators.md) - Advanced tool patterns
3. [Agent Skills](agent-skills.md) - Make plugins AI-discoverable
4. [Best Practices](best-practices.md) - Production-ready development

## Additional Resources

- [Architecture Overview](../architecture/overview.md)
- [Plugin System Deep Dive](../architecture/plugin-system.md)
- [API Reference](../api/interfaces.md)
- [Example Plugins](https://github.com/josephkirk/ArtReactorCore/tree/main/docs/examples)
