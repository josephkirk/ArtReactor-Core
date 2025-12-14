# Quick Start

Get up and running with ArtReactor Core in just a few minutes.

## Your First Plugin

Let's create a simple "Hello World" plugin to understand the basics.

### Step 1: Create a Plugin

Use the CLI to scaffold a new plugin:

```bash
arte plugin create hello-world --type core
```

This creates a new plugin in `plugins/hello-world/` with the following structure:

```
plugins/hello-world/
├── plugin.toml          # Plugin metadata
├── __init__.py          # Plugin implementation
└── SKILL.md             # Agent skill documentation
```

### Step 2: Implement Your Plugin

Open `plugins/hello-world/__init__.py` and add a simple tool:

```python
from artreactor.core.interfaces.plugin import CorePlugin, PluginManifest
from artreactor.core.decorators import tool
from typing import Any
import logging

logger = logging.getLogger(__name__)

class HelloWorldPlugin(CorePlugin):
    def __init__(self, manifest: PluginManifest, context: Any):
        super().__init__(manifest, context)

    async def initialize(self):
        logger.info("Hello World plugin initialized!")

    async def shutdown(self):
        logger.info("Hello World plugin shutting down.")

    @tool(
        name="greet",
        description="Greets a person by name"
    )
    def greet(self, name: str) -> str:
        """
        Returns a friendly greeting.
        
        Args:
            name: The name of the person to greet
            
        Returns:
            A greeting message
        """
        return f"Hello, {name}! Welcome to ArtReactor."
```

### Step 3: Start the Service

Run ArtReactor with your new plugin:

```bash
arte start
```

You should see log output indicating your plugin has loaded:

```
INFO: Hello World plugin initialized!
INFO: Registered tool: greet
```

### Step 4: Test Your Tool

Your `greet` tool is now available to AI agents and can be called via the API.

To test it programmatically:

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/api/agent/run",
    json={
        "prompt": "Please greet John using the greet tool"
    }
)
print(response.json())
```

## Understanding What We Built

### Plugin Manifest

The `plugin.toml` defines your plugin's metadata:

```toml
name = "hello-world"
version = "1.0.0"
type = "core"
description = "A simple hello world plugin"

[timing]
phase = "default"
priority = 50
```

### Plugin Class

Your plugin class inherits from `CorePlugin` and must implement:

- `initialize()`: Called when the plugin loads
- `shutdown()`: Called when the plugin unloads

### Tools

The `@tool` decorator exposes methods as callable tools for AI agents. These tools are automatically discovered and registered.

## Next Steps

Now that you've created your first plugin, explore:

1. [Plugin Types](../plugin-development/plugin-types.md) - Learn about different plugin types
2. [Tools and Decorators](../plugin-development/tools-and-decorators.md) - Advanced tool creation
3. [Agent Skills](../plugin-development/agent-skills.md) - Make your plugins AI-discoverable
4. [Best Practices](../plugin-development/best-practices.md) - Production-ready plugin development

## Common Patterns

### Adding Configuration

Plugins can read from the global `config.toml`:

```python
async def initialize(self):
    config = self.context.get("config", {})
    my_setting = config.get("plugins", {}).get("hello-world", {}).get("my_setting", "default")
    logger.info(f"Setting: {my_setting}")
```

### Accessing Other Plugins

Get access to other loaded plugins:

```python
async def initialize(self):
    plugin_manager = self.context.get("plugin_manager")
    other_plugin = plugin_manager.get_plugin("other-plugin-name")
```

### Working with Events

Use the event system for decoupled communication:

```python
from artreactor.core.events import fire, on

class HelloWorldPlugin(CorePlugin):
    async def initialize(self):
        # Listen for events
        on("user.connected", self.on_user_connected)
    
    async def on_user_connected(self, data):
        logger.info(f"User connected: {data['username']}")
    
    @tool(name="announce")
    def announce(self, message: str):
        # Fire an event
        fire("system.announcement", {"message": message})
        return "Announcement sent!"
```
